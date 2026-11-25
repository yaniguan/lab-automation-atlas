"""Stdlib SPDX 2.3/3.0 expression parser, bounded license lattice, and default-deny training policy.

Implements a zero-dependency lexer and recursive-descent AST parser supporting compound SPDX
expressions (`AND`, `OR`, `WITH`, `+`, and nested parentheses) aligned 1-to-1 with the formal
5-element bounded distributive lattice in `lean/LabAtlasLean.lean`:

    permissive (0) < share_alike (1) < non_commercial (2) < custom_terms (3) < eval_only (4)

- `conj` (`AND` / corpus derivation): join (`max` restrictiveness; `eval_only` is absorptive top).
- `disj` (`OR` / dual-license choice): meet (`min` restrictiveness; `permissive` is bottom).
- Default-deny training policy: unknown identifiers and `NOASSERTION` / `NONE` / unverified
  `LicenseRef-*` classify as `custom_terms` and are blocked from all training (`commercial` and
  academic alike).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

LICENSE_CLASSES_ORDERED: tuple[str, ...] = (
    "permissive",
    "share_alike",
    "non_commercial",
    "custom_terms",
    "eval_only",
)

_CLASS_TO_RANK: dict[str, int] = {name: idx for idx, name in enumerate(LICENSE_CLASSES_ORDERED)}

# Strict default-deny allowlist of permissive SPDX identifiers safe for commercial & academic training.
PERMISSIVE_SPDX_ALLOWLIST: frozenset[str] = frozenset(
    {
        "0BSD",
        "Apache-2.0",
        "Artistic-2.0",
        "BlueOak-1.0.0",
        "BSD-1-Clause",
        "BSD-2-Clause",
        "BSD-2-Clause-Patent",
        "BSD-2-Clause-Views",
        "BSD-3-Clause",
        "BSD-3-Clause-Clear",
        "BSL-1.0",
        "CC-BY-3.0",
        "CC-BY-4.0",
        "CC0-1.0",
        "CDLA-Permissive-1.0",
        "CDLA-Permissive-2.0",
        "ISC",
        "MIT",
        "MIT-0",
        "NCSA",
        "ODC-By-1.0",
        "PDDL-1.0",
        "PostgreSQL",
        "PSF-2.0",
        "Python-2.0",
        "Unlicense",
        "UPL-1.0",
        "WTFPL",
        "Zlib",
    }
)

# Known standard SPDX `WITH` exceptions that do not add non-commercial or copyleft training taint
# onto an already permissive base license.
PERMISSIVE_SPDX_EXCEPTIONS: frozenset[str] = frozenset(
    {
        "Autoconf-exception-3.0",
        "Bison-exception-2.2",
        "Classpath-exception-2.0",
        "FPC-exception-2.0",
        "GCC-exception-3.1",
        "Linux-syscall-note",
        "LLVM-exception",
        "OCaml-LGPL-linking-exception",
        "Swift-exception",
    }
)

SHARE_ALIKE_SPDX_IDS: frozenset[str] = frozenset(
    {
        "AGPL-3.0-only",
        "AGPL-3.0-or-later",
        "AGPL-3.0+",
        "CC-BY-SA-2.0",
        "CC-BY-SA-3.0",
        "CC-BY-SA-4.0",
        "CDDL-1.0",
        "CDDL-1.1",
        "CDLA-Sharing-1.0",
        "EPL-1.0",
        "EPL-2.0",
        "EUPL-1.2",
        "GPL-2.0-only",
        "GPL-2.0-or-later",
        "GPL-2.0+",
        "GPL-3.0-only",
        "GPL-3.0-or-later",
        "GPL-3.0+",
        "LGPL-2.1-only",
        "LGPL-2.1-or-later",
        "LGPL-2.1+",
        "LGPL-3.0-only",
        "LGPL-3.0-or-later",
        "LGPL-3.0+",
        "MPL-2.0",
        "ODbL-1.0",
        "OSL-3.0",
    }
)

NON_COMMERCIAL_SPDX_IDS: frozenset[str] = frozenset(
    {
        "CC-BY-NC-1.0",
        "CC-BY-NC-2.0",
        "CC-BY-NC-3.0",
        "CC-BY-NC-4.0",
        "CC-BY-NC-SA-2.0",
        "CC-BY-NC-SA-3.0",
        "CC-BY-NC-SA-4.0",
        "PolyForm-Noncommercial-1.0.0",
    }
)

# NoDerivatives and special SPDX sentinel values: recognized SPDX identifiers (`spdx_known=True`),
# but forbidden for training (`custom_terms`).
KNOWN_NON_TRAINABLE_SPDX_IDS: frozenset[str] = frozenset(
    {
        "CC-BY-ND-2.0",
        "CC-BY-ND-3.0",
        "CC-BY-ND-4.0",
        "CC-BY-NC-ND-2.0",
        "CC-BY-NC-ND-3.0",
        "CC-BY-NC-ND-4.0",
        "NOASSERTION",
        "NONE",
    }
)

_PERMISSIVE_LOWER = {k.lower(): k for k in PERMISSIVE_SPDX_ALLOWLIST}
_EXCEPTIONS_LOWER = {k.lower(): k for k in PERMISSIVE_SPDX_EXCEPTIONS}
_SHARE_ALIKE_LOWER = {k.lower(): k for k in SHARE_ALIKE_SPDX_IDS}
_NON_COMMERCIAL_LOWER = {k.lower(): k for k in NON_COMMERCIAL_SPDX_IDS}
_NON_TRAINABLE_LOWER = {k.lower(): k for k in KNOWN_NON_TRAINABLE_SPDX_IDS}

_POLICY_ALIASES: dict[str, str] = {
    "permissive": "permissive",
    "share_alike": "share_alike",
    "sharealike": "share_alike",
    "non_commercial": "non_commercial",
    "noncommercial": "non_commercial",
    "custom_terms": "custom_terms",
    "customterms": "custom_terms",
    "eval_only": "eval_only",
    "evalonly": "eval_only",
}

_SPDX_ID_RE = re.compile(
    r"^(?:DocumentRef-[A-Za-z0-9.\-]+:)?[A-Za-z0-9.\-]+\+?$"
)
_POLICY_ID_RE = re.compile(
    r"^(?:(?:DocumentRef-[A-Za-z0-9.\-]+:)?[A-Za-z0-9.\-]+\+?|[A-Za-z_]+)$"
)
_LICENSE_REF_RE = re.compile(
    r"^(?:DocumentRef-[A-Za-z0-9.\-]+:)?LicenseRef-[A-Za-z0-9.\-]+$",
    re.IGNORECASE,
)


class SpdxParseError(ValueError):
    """Raised when an SPDX license expression violates lexical or grammatical syntax."""


@dataclass(frozen=True)
class SpdxLeaf:
    identifier: str


@dataclass(frozen=True)
class SpdxWith:
    license_id: str
    exception_id: str


@dataclass(frozen=True)
class SpdxAnd:
    left: SpdxExpr
    right: SpdxExpr


@dataclass(frozen=True)
class SpdxOr:
    left: SpdxExpr
    right: SpdxExpr


SpdxExpr = SpdxLeaf | SpdxWith | SpdxAnd | SpdxOr


@dataclass(frozen=True)
class LicenseEvaluation:
    """Evaluated posture and governance booleans for a parsed SPDX expression."""

    expression: str
    license_class: str
    spdx_known: bool
    commercial_train_ok: bool
    academic_train_ok: bool


def license_rank(license_class: str) -> int:
    """Return integer rank in the 5-element bounded lattice (`0` permissive .. `4` eval_only)."""
    if license_class not in _CLASS_TO_RANK:
        raise ValueError(f"Unknown license_class: {license_class!r}")
    return _CLASS_TO_RANK[license_class]


def license_conj(a: str, b: str) -> str:
    """Join (`⊔`) in the restrictiveness lattice: SPDX `AND` / multi-corpus derivation."""
    return a if license_rank(a) >= license_rank(b) else b


def license_disj(a: str, b: str) -> str:
    """Meet (`⊓`) in the restrictiveness lattice: SPDX `OR` / dual-license choice."""
    return a if license_rank(a) <= license_rank(b) else b


def is_commercial_train_ok(license_class: str) -> bool:
    """Mirror `LabAtlasLean.LicenseClass.commercialTrainOK`."""
    return license_class == "permissive"


def is_academic_train_ok(license_class: str) -> bool:
    """Mirror `LabAtlasLean.LicenseClass.academicTrainOK`."""
    return license_class in ("permissive", "share_alike", "non_commercial")


def effective_license_class(parents: Sequence[str], own: str) -> str:
    """Mirror `LabAtlasLean.effectiveLicense`: fold `conj` across upstream parent classes."""
    acc = own
    for parent in parents:
        acc = license_conj(acc, parent)
    return acc


def _tokenize_spdx(
    expr: str,
    *,
    allow_policy_aliases: bool = False,
    require_uppercase_operators: bool = False,
) -> list[tuple[str, str]]:
    if not isinstance(expr, str) or not expr.strip():
        raise SpdxParseError("SPDX license expression must be a non-empty string.")
    tokens: list[tuple[str, str]] = []
    i = 0
    n = len(expr)
    id_pattern = _POLICY_ID_RE if allow_policy_aliases else _SPDX_ID_RE

    while i < n:
        ch = expr[i]
        if ch.isspace():
            i += 1
            continue
        if ch == "(":
            tokens.append(("LPAREN", "("))
            i += 1
            continue
        if ch == ")":
            tokens.append(("RPAREN", ")"))
            i += 1
            continue
        # Read contiguous non-whitespace, non-paren word
        start = i
        while i < n and not expr[i].isspace() and expr[i] not in ("(", ")"):
            i += 1
        word = expr[start:i]
        # Handle standalone trailing '+' attached as separate token or suffix
        upper = word.upper()
        if upper in ("AND", "OR", "WITH"):
            if require_uppercase_operators and word != upper:
                raise SpdxParseError(
                    f"SPDX boolean/exception operator {word!r} must be uppercase {upper!r}."
                )
            tokens.append((upper, upper))
        else:
            if not id_pattern.match(word):
                raise SpdxParseError(f"Invalid SPDX identifier token {word!r} in {expr!r}.")
            tokens.append(("ID", word))

    if not tokens:
        raise SpdxParseError("SPDX license expression produced zero tokens.")
    return tokens


class _Parser:
    def __init__(self, tokens: list[tuple[str, str]], raw: str) -> None:
        self._tokens = tokens
        self._pos = 0
        self._raw = raw

    def _peek(self) -> tuple[str, str] | None:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _consume(self, expected_kind: str | None = None) -> tuple[str, str]:
        tok = self._peek()
        if tok is None:
            raise SpdxParseError(f"Unexpected end of SPDX expression: {self._raw!r}")
        if expected_kind is not None and tok[0] != expected_kind:
            raise SpdxParseError(
                f"Expected {expected_kind} but got {tok[0]} ({tok[1]!r}) in {self._raw!r}"
            )
        self._pos += 1
        return tok

    def parse(self) -> SpdxExpr:
        node = self._parse_or()
        if self._peek() is not None:
            extra = self._peek()
            raise SpdxParseError(f"Unexpected trailing token {extra!r} in {self._raw!r}")
        return node

    def _parse_or(self) -> SpdxExpr:
        node = self._parse_and()
        while (tok := self._peek()) is not None and tok[0] == "OR":
            self._consume("OR")
            right = self._parse_and()
            node = SpdxOr(left=node, right=right)
        return node

    def _parse_and(self) -> SpdxExpr:
        node = self._parse_with_or_atom()
        while (tok := self._peek()) is not None and tok[0] == "AND":
            self._consume("AND")
            right = self._parse_with_or_atom()
            node = SpdxAnd(left=node, right=right)
        return node

    def _parse_with_or_atom(self) -> SpdxExpr:
        tok = self._peek()
        if tok is None:
            raise SpdxParseError(f"Expected license identifier or '(' in {self._raw!r}")
        if tok[0] == "LPAREN":
            self._consume("LPAREN")
            inner = self._parse_or()
            self._consume("RPAREN")
            nxt = self._peek()
            if nxt is not None and nxt[0] == "WITH":
                raise SpdxParseError(
                    f"SPDX WITH operator must follow a simple license ID, not ')' in {self._raw!r}"
                )
            return inner
        if tok[0] == "ID":
            _, lic_id = self._consume("ID")
            nxt = self._peek()
            if nxt is not None and nxt[0] == "WITH":
                self._consume("WITH")
                _, exc_id = self._consume("ID")
                if exc_id.endswith("+"):
                    raise SpdxParseError(
                        f"SPDX exception identifier {exc_id!r} cannot carry '+' suffix in {self._raw!r}"
                    )
                return SpdxWith(license_id=lic_id, exception_id=exc_id)
            return SpdxLeaf(identifier=lic_id)
        raise SpdxParseError(f"Unexpected token {tok[1]!r} in SPDX expression {self._raw!r}")


def parse_spdx_expression(
    expr: str,
    *,
    allow_policy_aliases: bool = False,
    require_uppercase_operators: bool = False,
) -> SpdxExpr:
    """Parse an SPDX 2.3/3.0 license expression into an AST (`SpdxLeaf`, `SpdxWith`, `SpdxAnd`, `SpdxOr`)."""
    tokens = _tokenize_spdx(
        expr,
        allow_policy_aliases=allow_policy_aliases,
        require_uppercase_operators=require_uppercase_operators,
    )
    return _Parser(tokens, expr).parse()


def _classify_leaf_id(identifier: str, *, allow_policy_aliases: bool) -> tuple[str, bool]:
    low = identifier.lower()
    if allow_policy_aliases and low in _POLICY_ALIASES:
        return _POLICY_ALIASES[low], True

    lookup = low[:-1] if low.endswith("+") and low not in _SHARE_ALIKE_LOWER else low
    if lookup in _PERMISSIVE_LOWER:
        return "permissive", True
    if lookup in _SHARE_ALIKE_LOWER or low in _SHARE_ALIKE_LOWER:
        return "share_alike", True
    if lookup in _NON_COMMERCIAL_LOWER:
        return "non_commercial", True
    if lookup in _NON_TRAINABLE_LOWER and not low.endswith("+"):
        return "custom_terms", True

    if _LICENSE_REF_RE.match(identifier):
        if "evalonly" in low or "eval-only" in low or "canary" in low:
            return "eval_only", True
        return "custom_terms", True

    # Unknown identifier: default-deny -> custom_terms with spdx_known=False
    return "custom_terms", False


def _eval_ast(node: SpdxExpr, *, allow_policy_aliases: bool) -> tuple[str, bool]:
    if isinstance(node, SpdxLeaf):
        return _classify_leaf_id(node.identifier, allow_policy_aliases=allow_policy_aliases)
    if isinstance(node, SpdxWith):
        base_cls, base_known = _classify_leaf_id(
            node.license_id, allow_policy_aliases=allow_policy_aliases
        )
        exc_low = node.exception_id.lower()
        exc_known = exc_low in _EXCEPTIONS_LOWER or bool(_LICENSE_REF_RE.match(node.exception_id))
        if exc_low in _EXCEPTIONS_LOWER:
            return base_cls, base_known and exc_known
        # Unknown or custom LicenseRef exception: conservative default-deny conjunction with custom_terms
        return license_conj(base_cls, "custom_terms"), (base_known and exc_known)
    if isinstance(node, SpdxAnd):
        l_cls, l_known = _eval_ast(node.left, allow_policy_aliases=allow_policy_aliases)
        r_cls, r_known = _eval_ast(node.right, allow_policy_aliases=allow_policy_aliases)
        return license_conj(l_cls, r_cls), (l_known and r_known)
    if isinstance(node, SpdxOr):
        l_cls, l_known = _eval_ast(node.left, allow_policy_aliases=allow_policy_aliases)
        r_cls, r_known = _eval_ast(node.right, allow_policy_aliases=allow_policy_aliases)
        return license_disj(l_cls, r_cls), (l_known and r_known)
    raise TypeError(f"Unsupported AST node: {node!r}")


def evaluate_spdx_expression(
    expr: str,
    *,
    allow_policy_aliases: bool = False,
    require_uppercase_operators: bool = False,
) -> LicenseEvaluation:
    """Parse and evaluate an SPDX expression under the default-deny L5 training policy lattice."""
    try:
        ast = parse_spdx_expression(
            expr,
            allow_policy_aliases=allow_policy_aliases,
            require_uppercase_operators=require_uppercase_operators,
        )
    except SpdxParseError:
        return LicenseEvaluation(
            expression=str(expr),
            license_class="custom_terms",
            spdx_known=False,
            commercial_train_ok=False,
            academic_train_ok=False,
        )
    cls, known = _eval_ast(ast, allow_policy_aliases=allow_policy_aliases)
    # If any token in the expression was not a recognized SPDX identifier, never allow training
    if not known:
        cls = license_conj(cls, "custom_terms")
    return LicenseEvaluation(
        expression=expr.strip(),
        license_class=cls,
        spdx_known=known,
        commercial_train_ok=known and is_commercial_train_ok(cls),
        academic_train_ok=known and is_academic_train_ok(cls),
    )


def check_atlas_resource_policy(
    *,
    https_only: bool,
    no_private_ip: bool,
    spdx_known: bool,
    license_class: str,
    for_training: bool,
    commercial: bool,
) -> str | None:
    """Exact Python mirror of `LabAtlasLean.checkAtlasResource`, returning violated rule ID or None."""
    if not (https_only and no_private_ip):
        return "https_ssrf_guard"
    if not spdx_known:
        return "explicit_spdx_license"
    if for_training and license_class == "eval_only":
        return "eval_only_contamination_guard"
    if for_training and not is_academic_train_ok(license_class):
        return "academic_training_license_guard"
    if for_training and commercial and not is_commercial_train_ok(license_class):
        return "commercial_training_license_guard"
    return None


def _leaf_matches_query(leaf_id: str, query_norm: str) -> bool:
    low = leaf_id.lower()
    if low == query_norm:
        return True
    # Support family prefix queries such as "BSD" or "CC-BY-NC" without matching unrelated tokens
    if low.startswith(query_norm + "-"):
        return True
    return False


def spdx_satisfies_filter(entry_expr: str, query: str) -> bool:
    """Evaluate whether `entry_expr` satisfies a license filter `query` under `AND`/`OR` semantics.

    - `A OR B`: satisfied if either `A` or `B` satisfies `query`.
    - `A AND B`: satisfied only if an operand matches `query` AND the conjoined expression is no
      more restrictive than `query`'s own license posture (preventing `MIT AND CC-BY-NC-4.0` from
      matching `--license MIT`).
    """
    q_norm = query.strip().lower()
    if not q_norm:
        return True

    q_eval = evaluate_spdx_expression(query, allow_policy_aliases=True)
    if q_eval.spdx_known:
        max_allowed_rank = license_rank(q_eval.license_class)
    elif q_norm.startswith("bsd"):
        max_allowed_rank = license_rank("permissive")
    elif q_norm.startswith("cc-by-nc"):
        max_allowed_rank = license_rank("non_commercial")
    elif q_norm.startswith(("cc-by-sa", "gpl", "agpl", "lgpl", "mpl")):
        max_allowed_rank = license_rank("share_alike")
    else:
        max_allowed_rank = license_rank("eval_only")

    try:
        ast = parse_spdx_expression(entry_expr, allow_policy_aliases=True)
    except SpdxParseError:
        return False

    def _matches(node: SpdxExpr) -> bool:
        if isinstance(node, SpdxLeaf):
            cls, _ = _eval_ast(node, allow_policy_aliases=True)
            return _leaf_matches_query(node.identifier, q_norm) and license_rank(cls) <= max_allowed_rank
        if isinstance(node, SpdxWith):
            cls, _ = _eval_ast(node, allow_policy_aliases=True)
            full_str = f"{node.license_id} with {node.exception_id}".lower()
            matched = (
                full_str == q_norm
                or _leaf_matches_query(node.license_id, q_norm)
                or node.exception_id.lower() == q_norm
            )
            return matched and license_rank(cls) <= max_allowed_rank
        if isinstance(node, SpdxOr):
            return _matches(node.left) or _matches(node.right)
        if isinstance(node, SpdxAnd):
            cls, _ = _eval_ast(node, allow_policy_aliases=True)
            if license_rank(cls) > max_allowed_rank:
                return False
            return _matches(node.left) or _matches(node.right)
        return False

    return _matches(ast)
