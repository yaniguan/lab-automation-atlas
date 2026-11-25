"""CLI (`lab-atlas`) and repository English-only tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from lab_atlas.catalog import REPO_ROOT
from lab_atlas.cli import main as cli_main


def test_cli_list_filters_and_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    """Issue #18: Test `lab-atlas list` filtering by category, commercial-ok, osi-only, and purpose."""
    rc = cli_main(["list", "--category", "software", "--commercial-ok", "--osi-only", "--json"])
    assert rc == 0
    software = json.loads(capsys.readouterr().out)
    assert len(software) == 9
    assert all(e["commercial_use_ok"] and e["osi_approved"] for e in software)

    rc = cli_main(["list", "--category", "dataset", "--purpose", "train_commercial", "--json"])
    assert rc == 0
    trainable = json.loads(capsys.readouterr().out)
    ids = {e["id"] for e in trainable}
    assert "wlp" in ids
    assert "bioprobench" not in ids
    assert "lab-bench" not in ids

    rc = cli_main(["list", "--modality", "Raman", "--json"])
    assert rc == 0
    raman_entries = json.loads(capsys.readouterr().out)
    raman_ids = {e["id"] for e in raman_entries}
    assert {"lab-attrib", "emerald-cloud-lab", "bluesky"} <= raman_ids

    rc = cli_main(["list", "--min-volume-at-most", "0.5", "--max-volume-at-least", "1000", "--json"])
    assert rc == 0
    vol_entries = json.loads(capsys.readouterr().out)
    vol_ids = {e["id"] for e in vol_entries}
    assert {"hamilton", "tecan", "emerald-cloud-lab"} <= vol_ids


def test_cli_inspect_compatibility_export_validate_and_check_links(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Issue #18: Test inspect, compatibility, export (YAML/JSON), validate, sync-readme, check-links."""
    assert cli_main(["inspect", "bioprobench", "--json"]) == 0
    entry = json.loads(capsys.readouterr().out)
    assert entry["spdx_license"] == "CC-BY-NC-4.0"

    assert cli_main(["inspect", "does-not-exist"]) == 1
    capsys.readouterr()

    assert cli_main(["compatibility", "--json"]) == 0
    comp = json.loads(capsys.readouterr().out)
    assert len(comp) >= 5

    yaml_out = tmp_path / "atlas.yaml"
    assert cli_main(["export", "--format", "yaml", "--output", str(yaml_out)]) == 0
    capsys.readouterr()
    yaml_text = yaml_out.read_text(encoding="utf-8")
    assert "atlas_name: \"lab-automation-atlas\"" in yaml_text
    assert "bioprobench" in yaml_text

    assert cli_main(["validate"]) == 0
    assert cli_main(["sync-readme", "--check"]) == 0
    capsys.readouterr()

    report_path = tmp_path / "offline_links.json"
    assert cli_main(["check-links", "--offline", "--json-out", str(report_path)]) == 0
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["broken_total"] == 0


def test_zero_cjk_characters_across_repository() -> None:
    """Ensure 100% English prose/comments across all repository text files."""
    out = subprocess.check_output(
        ["git", "-C", str(REPO_ROOT), "ls-files", "-c", "-o", "--exclude-standard"],
        text=True,
        encoding="utf-8",
    )
    for rel in out.splitlines():
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for ch in text:
            code = ord(ch)
            assert not (
                0x4E00 <= code <= 0x9FFF
                or 0x3400 <= code <= 0x4DBF
                or 0x3000 <= code <= 0x303F
                or 0xFF00 <= code <= 0xFFEF
            ), f"Non-English CJK character {ch!r} found in {rel}"
