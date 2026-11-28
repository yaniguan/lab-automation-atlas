"""Canonical URL normalization and prefix matching for L5 catalog governance and wire gating.

Normalizes equivalent upstream URLs across GitHub, Hugging Face (`huggingface.co`, `hf.co`,
`datasets-server.huggingface.co`, `/api/datasets/...`), `raw.githubusercontent.com`, arXiv
(`/abs/`, `/pdf/`, `/html/`, `.pdf`, version suffixes `vN`), and `doi.org` so held-out
`eval_only` benchmarks and restricted corpora cannot bypass training gates via URL aliases.
"""

from __future__ import annotations

import re
import urllib.parse
from typing import Any, Iterable

_ARXIV_NEW_ID_RE = re.compile(r"^([0-9]{4}\.[0-9]{4,5})(?:v[0-9]+)?$", re.IGNORECASE)
_ARXIV_OLD_ID_RE = re.compile(
    r"^([a-z\-]+(?:\.[a-z]{2})?/[0-9]{7})(?:v[0-9]+)?$",
    re.IGNORECASE,
)
_ARXIV_DOI_RE = re.compile(
    r"^(10\.48550/arxiv\.[0-9]{4}\.[0-9]{4,5})(?:v[0-9]+)?$",
    re.IGNORECASE,
)

CROSS_REF_LINK_LABELS: frozenset[str] = frozenset({"lab-rehearsal", "lab-verify", "Studio"})


def _strip_git_suffix(segment: str) -> str:
    if segment.lower().endswith(".git") and len(segment) > 4:
        return segment[:-4]
    return segment


def _split_unquoted_segments(path: str) -> list[str]:
    segments: list[str] = []
    for raw_seg in path.split("/"):
        if not raw_seg:
            continue
        unquoted = urllib.parse.unquote(raw_seg)
        for sub in unquoted.split("/"):
            if sub:
                segments.append(sub)
    return segments


def canonicalize_url_for_match(url: str) -> str:
    """Canonicalize an external URL into a normalized `<scheme>://<host><path>` prefix key.

    Rules:
    - Lower-case scheme and host, drop trailing `.` and leading `www.`, and map `hf.co` ->
      `huggingface.co`, `export.arxiv.org` -> `arxiv.org`, `dx.doi.org` -> `doi.org`.
    - Map `raw.githubusercontent.com/<owner>/<repo>/...` and
      `codeload.github.com/<owner>/<repo>/...` -> `<scheme>://github.com/<owner>/<repo>`.
    - On `github.com` and `huggingface.co`, lower-case `<owner>/<repo>` (and
      `datasets/<owner>/<name>` / `spaces/<owner>/<name>`) segments and strip `.git`.
    - Map `huggingface.co/api/datasets/<id>/...` and
      `datasets-server.huggingface.co/...?dataset=<id>` ->
      `<scheme>://huggingface.co/datasets/<id>`.
    - Map arXiv `/pdf/<id>(.pdf)`, `/abs/<id>vN`, `/pdf/<id>vN(.pdf)`, `/html/<id>(vN)` ->
      `<scheme>://arxiv.org/abs/<id>`.
    """
    if not isinstance(url, str):
        return ""
    raw = url.strip()
    if not raw:
        return ""

    parsed = urllib.parse.urlsplit(raw)
    scheme = parsed.scheme.lower()
    host = (parsed.hostname or "").strip().lower().rstrip(".")
    if not scheme or not host:
        return ""

    if host.startswith("www."):
        host = host[4:]

    if host == "hf.co":
        host = "huggingface.co"
    elif host == "export.arxiv.org":
        host = "arxiv.org"
    elif host == "dx.doi.org":
        host = "doi.org"

    if host == "datasets-server.huggingface.co":
        qs = urllib.parse.parse_qs(parsed.query)
        ds_vals = qs.get("dataset") or []
        if ds_vals and ds_vals[0].strip():
            ds_segs = _split_unquoted_segments(ds_vals[0].strip())
            if len(ds_segs) >= 2:
                owner = ds_segs[0].lower()
                name = _strip_git_suffix(ds_segs[1].lower())
                return f"{scheme}://huggingface.co/datasets/{owner}/{name}"
            if len(ds_segs) == 1:
                name = _strip_git_suffix(ds_segs[0].lower())
                return f"{scheme}://huggingface.co/datasets/{name}"

    segments = _split_unquoted_segments(parsed.path)

    if host in ("raw.githubusercontent.com", "codeload.github.com") and len(segments) >= 2:
        owner = segments[0].lower()
        repo = _strip_git_suffix(segments[1].lower())
        return f"{scheme}://github.com/{owner}/{repo}"

    if host == "github.com":
        if len(segments) >= 2:
            owner = segments[0].lower()
            repo = _strip_git_suffix(segments[1].lower())
            tail = "/".join(segments[2:])
            base = f"{scheme}://github.com/{owner}/{repo}"
            return f"{base}/{tail}" if tail else base
        if len(segments) == 1:
            return f"{scheme}://github.com/{_strip_git_suffix(segments[0].lower())}"
        return f"{scheme}://github.com"

    if host == "huggingface.co":
        if len(segments) >= 3 and segments[0].lower() == "api":
            kind = segments[1].lower()
            if kind == "datasets":
                if len(segments) >= 4:
                    owner = segments[2].lower()
                    name = _strip_git_suffix(segments[3].lower())
                    return f"{scheme}://huggingface.co/datasets/{owner}/{name}"
                name = _strip_git_suffix(segments[2].lower())
                return f"{scheme}://huggingface.co/datasets/{name}"
            if kind == "spaces" and len(segments) >= 4:
                owner = segments[2].lower()
                name = _strip_git_suffix(segments[3].lower())
                return f"{scheme}://huggingface.co/spaces/{owner}/{name}"
            if kind == "models" and len(segments) >= 4:
                owner = segments[2].lower()
                name = _strip_git_suffix(segments[3].lower())
                return f"{scheme}://huggingface.co/{owner}/{name}"

        if segments and segments[0].lower() in ("datasets", "spaces"):
            prefix_kind = segments[0].lower()
            if len(segments) >= 3:
                owner = segments[1].lower()
                name = _strip_git_suffix(segments[2].lower())
                tail = "/".join(segments[3:])
                base = f"{scheme}://huggingface.co/{prefix_kind}/{owner}/{name}"
                return f"{base}/{tail}" if tail else base
            if len(segments) == 2:
                name = _strip_git_suffix(segments[1].lower())
                return f"{scheme}://huggingface.co/{prefix_kind}/{name}"
            return f"{scheme}://huggingface.co/{prefix_kind}"

        if len(segments) >= 2:
            owner = segments[0].lower()
            name = _strip_git_suffix(segments[1].lower())
            tail = "/".join(segments[2:])
            base = f"{scheme}://huggingface.co/{owner}/{name}"
            return f"{base}/{tail}" if tail else base
        if len(segments) == 1:
            return f"{scheme}://huggingface.co/{_strip_git_suffix(segments[0].lower())}"
        return f"{scheme}://huggingface.co"

    if host == "arxiv.org" and len(segments) >= 2:
        kind = segments[0].lower()
        if kind in ("abs", "pdf", "html", "e-print", "src"):
            rest = "/".join(segments[1:])
            if rest.lower().endswith(".pdf"):
                rest = rest[:-4]
            m_new = _ARXIV_NEW_ID_RE.match(rest)
            if m_new:
                return f"{scheme}://arxiv.org/abs/{m_new.group(1).lower()}"
            m_old = _ARXIV_OLD_ID_RE.match(rest)
            if m_old:
                return f"{scheme}://arxiv.org/abs/{m_old.group(1).lower()}"

    if host == "doi.org" and segments:
        doi_joined = "/".join(segments).lower()
        m_arxiv_doi = _ARXIV_DOI_RE.match(doi_joined)
        if m_arxiv_doi:
            return f"{scheme}://doi.org/{m_arxiv_doi.group(1).lower()}"
        return f"{scheme}://doi.org/{doi_joined}"

    norm_path = parsed.path.rstrip("/")
    return f"{scheme}://{host}{norm_path}"


def build_entry_url_prefixes(
    entries: Iterable[dict[str, Any]],
    *,
    cross_ref_labels: frozenset[str] = CROSS_REF_LINK_LABELS,
) -> list[tuple[str, dict[str, Any]]]:
    """Build canonicalized `(prefix, entry)` pairs sorted longest-prefix-first."""
    url_prefixes: list[tuple[str, dict[str, Any]]] = []
    for entry in entries:
        candidates: list[str] = []
        for link in entry.get("links") or []:
            if link.get("label") in cross_ref_labels:
                continue
            candidates.append(canonicalize_url_for_match(link["url"]))
        hf_id = entry.get("huggingface_id")
        if isinstance(hf_id, str) and hf_id.strip():
            candidates.append(canonicalize_url_for_match(f"https://huggingface.co/datasets/{hf_id}"))
            candidates.append(canonicalize_url_for_match(f"https://huggingface.co/{hf_id}"))
        doi = entry.get("doi")
        if isinstance(doi, str) and doi.strip():
            candidates.append(canonicalize_url_for_match(f"https://doi.org/{doi}"))

        seen_norm: set[str] = set()
        for norm_u in candidates:
            if norm_u and norm_u not in seen_norm:
                seen_norm.add(norm_u)
                url_prefixes.append((norm_u, entry))

    url_prefixes.sort(key=lambda item: len(item[0]), reverse=True)
    return url_prefixes


def match_url_prefixes(
    url: str,
    url_prefixes: Iterable[tuple[str, dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Return deduplicated catalog entries matching `url` under canonical prefix matching."""
    norm_target = canonicalize_url_for_match(url)
    if not norm_target:
        return []
    matched: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for prefix, entry in url_prefixes:
        if norm_target == prefix or norm_target.startswith(prefix + "/"):
            eid = entry["id"]
            if eid not in seen_ids:
                seen_ids.add(eid)
                matched.append(entry)
    return matched
