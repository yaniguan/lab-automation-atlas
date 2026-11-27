"""Verify Lean 4.36.0 LabAtlasLean theorem axioms and >=100-case #eval parity with lab_atlas.spdx.

1. Audits `lean/LabAtlasLean.lean` source for zero `sorry` and zero `axiom` declarations, and
   discovers every `theorem` declaration automatically.
2. Runs `lake env lean` on an ephemeral verification harness importing `LabAtlasLean` to:
   - Execute `#print axioms` on every theorem, enforcing strictly standard Lean kernel axioms
     (`propext`, `Classical.choice`, `Quot.sound`) with no custom axioms and zero `sorryAx`.
   - Execute `335` `#eval` differential parity cases (`25` join/meet lattice & homomorphism cases,
     `125` multi-parent `effectiveLicense` taint cases, `25` 3-hop `LineageDAG.effective` DAG taint
     cases, and `160` `checkAtlasResource` policy states) against Python `lab_atlas.spdx`.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lab_atlas.spdx import (  # noqa: E402
    LICENSE_CLASSES_ORDERED,
    check_atlas_resource_policy,
    effective_license_class,
    is_academic_train_ok,
    is_commercial_train_ok,
    license_conj,
    license_disj,
)

ALLOWED_LEAN_AXIOMS: frozenset[str] = frozenset(
    {"propext", "Classical.choice", "Quot.sound"}
)

_THEOREM_RE = re.compile(
    r"^\s*(?:@\[[^\]]+\]\s*)*(?:private\s+|protected\s+)?theorem\s+([A-Za-z0-9_.']+)\b",
    re.MULTILINE,
)
_NO_AXIOMS_RE = re.compile(r"^'([^']+)' does not depend on any axioms\s*$")
_DEPENDS_AXIOMS_RE = re.compile(r"^'([^']+)' depends on axioms:\s*\[([^\]]*)\]\s*$")


def resolve_lake_binary(explicit: str | None = None) -> str:
    """Locate the `lake` executable on PATH or under `~/.elan/bin`."""
    if explicit:
        return explicit
    found = shutil.which("lake")
    if found:
        return found
    elan_bin = Path.home() / ".elan" / "bin"
    for name in ("lake.exe", "lake"):
        candidate = elan_bin / name
        if candidate.is_file():
            return str(candidate)
    raise FileNotFoundError(
        "Could not locate Lean 4 `lake` binary on PATH or in ~/.elan/bin."
    )


def discover_lean_theorems(lean_source_path: Path) -> list[str]:
    """Extract fully-qualified `LabAtlasLean.<name>` theorem identifiers and audit source hygiene."""
    src = lean_source_path.read_text(encoding="utf-8")
    # Strip line and block comments before checking forbidden tokens and theorem declarations
    stripped = re.sub(r"/-.*?-/", "", src, flags=re.DOTALL)
    stripped = re.sub(r"--[^\n]*", "", stripped)

    if re.search(r"\bsorry\b", stripped):
        raise ValueError(f"Forbidden `sorry` token detected in {lean_source_path}")
    if re.search(r"\baxiom\b", stripped):
        raise ValueError(f"Custom `axiom` declaration detected in {lean_source_path}")

    theorems: list[str] = []
    for match in _THEOREM_RE.finditer(stripped):
        raw_name = match.group(1)
        fq_name = (
            raw_name
            if raw_name.startswith("LabAtlasLean.")
            else f"LabAtlasLean.{raw_name}"
        )
        if fq_name not in theorems:
            theorems.append(fq_name)
    if not theorems:
        raise ValueError(f"Discovered 0 theorems in {lean_source_path}")
    return theorems


def _build_lean_harness(theorems: Sequence[str]) -> str:
    lines: list[str] = [
        "import LabAtlasLean",
        "open LabAtlasLean",
        "",
    ]
    for thm in theorems:
        lines.append(f"#print axioms {thm}")

    lines.extend(
        [
            "",
            "private def licSnake : LicenseClass -> String",
            '  | .permissive    => "permissive"',
            '  | .shareAlike    => "share_alike"',
            '  | .nonCommercial => "non_commercial"',
            '  | .customTerms   => "custom_terms"',
            '  | .evalOnly      => "eval_only"',
            "",
            "private def boolToken (b : Bool) : String := if b then \"1\" else \"0\"",
            "",
            "private def optRule : Option RegimeViolation -> String",
            '  | none   => "NONE"',
            "  | some v => v.rule",
            "",
            "private def allLic : List LicenseClass :=",
            "  [.permissive, .shareAlike, .nonCommercial, .customTerms, .evalOnly]",
            "",
            "private def allBools : List Bool := [false, true]",
            "",
            "#eval show IO Unit from do",
            "  -- 1) 25 binary lattice & homomorphism cases",
            "  for a in allLic do",
            "    for b in allLic do",
            "      let cj := a.conj b",
            "      let dj := a.disj b",
            "      IO.println s!\"PARITY|LATTICE|{licSnake a}|{licSnake b}|{licSnake cj}|{licSnake dj}|{boolToken cj.commercialTrainOK}|{boolToken cj.academicTrainOK}|{boolToken dj.commercialTrainOK}|{boolToken dj.academicTrainOK}\"",
            "  -- 2) 125 2-parent effectiveLicense lineage taint cases",
            "  for p1 in allLic do",
            "    for p2 in allLic do",
            "      for own in allLic do",
            "        let eff := effectiveLicense [p1, p2] own",
            "        IO.println s!\"PARITY|LINEAGE|{licSnake p1}|{licSnake p2}|{licSnake own}|{licSnake eff}\"",
            "  -- 3) 25 3-hop LineageDAG.effective deep derivation DAG cases",
            "  for anc in allLic do",
            "    for mid in allLic do",
            "      let dag : LineageDAG := .derived .permissive [.derived mid [.leaf anc], .leaf .shareAlike]",
            "      IO.println s!\"PARITY|DAG|{licSnake anc}|{licSnake mid}|{licSnake dag.effective}\"",
            "  -- 4) 160 checkAtlasResource policy gate cases",
            "  for h in allBools do",
            "    for np in allBools do",
            "      for sk in allBools do",
            "        for lc in allLic do",
            "          for ft in allBools do",
            "            for cm in allBools do",
            "              let r : AtlasResource := { httpsOnly := h, noPrivateIp := np, spdxKnown := sk, licenseClass := lc, forTraining := ft, commercial := cm }",
            "              IO.println s!\"PARITY|POLICY|{boolToken h}|{boolToken np}|{boolToken sk}|{licSnake lc}|{boolToken ft}|{boolToken cm}|{optRule (checkAtlasResource r)}\"",
            "",
        ]
    )
    return "\n".join(lines)


def verify_lean_axioms_and_parity(
    *,
    lake_bin: str | None = None,
    run_build: bool = False,
    min_cases: int = 100,
) -> dict[str, object]:
    """Run `#print axioms` and `#eval` differential parity between Lean 4.36.0 and Python."""
    lake = resolve_lake_binary(lake_bin)
    lean_dir = ROOT / "lean"
    lean_src = lean_dir / "LabAtlasLean.lean"
    theorems = discover_lean_theorems(lean_src)

    if run_build or not (lean_dir / ".lake" / "build").is_dir():
        build_proc = subprocess.run(
            [lake, "build"],
            cwd=str(lean_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if build_proc.returncode != 0:
            raise RuntimeError(
                f"`lake build` failed (exit {build_proc.returncode}):\n"
                f"{build_proc.stdout}\n{build_proc.stderr}"
            )

    harness_code = _build_lean_harness(theorems)
    fd, tmp_name = tempfile.mkstemp(suffix="_lab_atlas_parity.lean")
    os.close(fd)
    tmp_path = Path(tmp_name)
    try:
        tmp_path.write_text(harness_code, encoding="utf-8")
        proc = subprocess.run(
            [lake, "env", "lean", str(tmp_path)],
            cwd=str(lean_dir),
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    finally:
        tmp_path.unlink(missing_ok=True)

    if proc.returncode != 0:
        raise RuntimeError(
            f"`lake env lean` failed (exit {proc.returncode}):\n{proc.stdout}\n{proc.stderr}"
        )

    axiom_map: dict[str, list[str]] = {}
    parity_counts = {"LATTICE": 0, "LINEAGE": 0, "DAG": 0, "POLICY": 0}

    for raw_line in proc.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        m_none = _NO_AXIOMS_RE.match(line)
        if m_none:
            axiom_map[m_none.group(1)] = []
            continue

        m_dep = _DEPENDS_AXIOMS_RE.match(line)
        if m_dep:
            thm_name = m_dep.group(1)
            axioms = [a.strip() for a in m_dep.group(2).split(",") if a.strip()]
            disallowed = [a for a in axioms if a not in ALLOWED_LEAN_AXIOMS]
            if disallowed:
                raise AssertionError(
                    f"Theorem {thm_name} depends on disallowed/custom axioms {disallowed} "
                    f"(allowed={sorted(ALLOWED_LEAN_AXIOMS)})"
                )
            axiom_map[thm_name] = axioms
            continue

        if line.startswith("PARITY|"):
            parts = line.split("|")
            kind = parts[1]
            if kind == "LATTICE":
                _, _, a, b, lean_cj, lean_dj, cj_c, cj_a, dj_c, dj_a = parts
                py_cj = license_conj(a, b)
                py_dj = license_disj(a, b)
                assert lean_cj == py_cj, f"conj({a}, {b}): Lean={lean_cj} != Python={py_cj}"
                assert lean_dj == py_dj, f"disj({a}, {b}): Lean={lean_dj} != Python={py_dj}"
                assert (cj_c == "1") is is_commercial_train_ok(py_cj)
                assert (cj_a == "1") is is_academic_train_ok(py_cj)
                assert (dj_c == "1") is is_commercial_train_ok(py_dj)
                assert (dj_a == "1") is is_academic_train_ok(py_dj)
                parity_counts["LATTICE"] += 1
            elif kind == "LINEAGE":
                _, _, p1, p2, own, lean_eff = parts
                py_eff = effective_license_class([p1, p2], own)
                assert lean_eff == py_eff, (
                    f"effectiveLicense([{p1}, {p2}], {own}): Lean={lean_eff} != Python={py_eff}"
                )
                parity_counts["LINEAGE"] += 1
            elif kind == "DAG":
                _, _, anc, mid, lean_dag_eff = parts
                branch1 = effective_license_class([anc], mid)
                py_dag_eff = effective_license_class([branch1, "share_alike"], "permissive")
                assert lean_dag_eff == py_dag_eff, (
                    f"LineageDAG({anc}, {mid}): Lean={lean_dag_eff} != Python={py_dag_eff}"
                )
                parity_counts["DAG"] += 1
            elif kind == "POLICY":
                _, _, h, np, sk, lc, ft, cm, lean_rule_tok = parts
                lean_rule = None if lean_rule_tok == "NONE" else lean_rule_tok
                py_rule = check_atlas_resource_policy(
                    https_only=(h == "1"),
                    no_private_ip=(np == "1"),
                    spdx_known=(sk == "1"),
                    license_class=lc,
                    for_training=(ft == "1"),
                    commercial=(cm == "1"),
                )
                assert lean_rule == py_rule, (
                    f"checkAtlasResource(h={h}, np={np}, sk={sk}, lc={lc}, ft={ft}, cm={cm}): "
                    f"Lean={lean_rule} != Python={py_rule}"
                )
                parity_counts["POLICY"] += 1
            else:
                raise ValueError(f"Unexpected PARITY record kind: {line!r}")

    missing_theorems = [t for t in theorems if t not in axiom_map]
    if missing_theorems:
        raise AssertionError(f"Missing `#print axioms` output for theorems: {missing_theorems}")

    total_cases = sum(parity_counts.values())
    if total_cases < min_cases:
        raise AssertionError(
            f"Expected >= {min_cases} #eval differential parity cases, ran {total_cases}"
        )
    assert LICENSE_CLASSES_ORDERED == (
        "permissive",
        "share_alike",
        "non_commercial",
        "custom_terms",
        "eval_only",
    )

    seen_axioms = sorted({ax for axs in axiom_map.values() for ax in axs})
    return {
        "theorems_verified": len(theorems),
        "axioms_observed": seen_axioms,
        "parity_cases_total": total_cases,
        "parity_breakdown": parity_counts,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify LabAtlasLean theorem axioms and >=100-case #eval parity with Python."
    )
    parser.add_argument(
        "--lake-bin",
        default=None,
        help="Optional explicit path to `lake` executable.",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Run `lake build` before executing `#print axioms` and `#eval` parity checks.",
    )
    parser.add_argument(
        "--min-cases",
        type=int,
        default=100,
        help="Minimum required #eval differential parity test cases (default: 100).",
    )
    args = parser.parse_args(argv)

    summary = verify_lean_axioms_and_parity(
        lake_bin=args.lake_bin,
        run_build=args.build,
        min_cases=args.min_cases,
    )
    print(
        f"OK: verified {summary['theorems_verified']} Lean 4.36.0 theorems "
        f"(no custom axioms; observed={summary['axioms_observed']}) and "
        f"{summary['parity_cases_total']} #eval differential parity cases "
        f"{summary['parity_breakdown']} against lab_atlas.spdx."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
