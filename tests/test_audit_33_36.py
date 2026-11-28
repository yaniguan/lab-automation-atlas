"""Regression and differential test suite for external audit Issues #33, #34, #35, and #36."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Callable

import jsonschema
import pytest

import autolab_wire
from lab_atlas.catalog import (
    REPO_ROOT,
    filter_entries,
    is_generic_or_bare_arxiv_license_evidence,
    load_catalog,
    load_schema,
    validate_catalog,
)
from lab_atlas.urlmatch import canonicalize_url_for_match
import scripts.check_licenses as check_licenses_mod
import scripts.gen_lean_parity as gen_lean_parity_mod


def _build_eval_only_url_variants() -> list[tuple[str, str, str]]:
    """Generate equivalent URL variants across every eval_only catalog entry."""
    catalog = load_catalog()
    cases: list[tuple[str, str, str]] = []
    for entry in catalog["entries"]:
        if entry["allowed_purposes"] != ["eval_only"]:
            continue
        eid = entry["id"]
        for link in entry["links"]:
            if link["label"] in ("lab-rehearsal", "lab-verify", "Studio"):
                continue
            url = link["url"]
            if "github.com/" in url:
                parts = url.rstrip("/").split("github.com/", 1)[1].split("/")
                if len(parts) >= 2:
                    owner, repo = parts[0], parts[1]
                    cases.extend(
                        [
                            (eid, "gh_git_suffix", f"https://github.com/{owner}/{repo}.git"),
                            (eid, "gh_lower_path", f"https://github.com/{owner.lower()}/{repo.lower()}"),
                            (eid, "gh_upper_path", f"https://github.com/{owner.upper()}/{repo.upper()}"),
                            (eid, "gh_www_host", f"https://www.github.com/{owner}/{repo}"),
                            (
                                eid,
                                "gh_raw_readme",
                                f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md",
                            ),
                        ]
                    )
            elif "huggingface.co/datasets/" in url:
                ds_id = url.rstrip("/").split("huggingface.co/datasets/", 1)[1]
                cases.extend(
                    [
                        (eid, "hf_git_suffix", f"https://huggingface.co/datasets/{ds_id}.git"),
                        (eid, "hf_lower_path", f"https://huggingface.co/datasets/{ds_id.lower()}"),
                        (eid, "hf_upper_path", f"https://huggingface.co/datasets/{ds_id.upper()}"),
                        (eid, "hf_www_host", f"https://www.huggingface.co/datasets/{ds_id}"),
                        (eid, "hf_short_domain", f"https://hf.co/datasets/{ds_id.lower()}"),
                        (
                            eid,
                            "hf_api_datasets",
                            f"https://huggingface.co/api/datasets/{ds_id.lower()}/parquet",
                        ),
                        (
                            eid,
                            "hf_datasets_server",
                            f"https://datasets-server.huggingface.co/rows?dataset={ds_id.lower()}&config=default&split=test",
                        ),
                    ]
                )
            elif "arxiv.org/abs/" in url:
                arxiv_id = url.rstrip("/").split("arxiv.org/abs/", 1)[1]
                cases.extend(
                    [
                        (eid, "arxiv_www", f"https://www.arxiv.org/abs/{arxiv_id}"),
                        (eid, "arxiv_abs_v1", f"https://arxiv.org/abs/{arxiv_id}v1"),
                        (eid, "arxiv_abs_v2", f"https://arxiv.org/abs/{arxiv_id}v2"),
                        (eid, "arxiv_pdf_bare", f"https://arxiv.org/pdf/{arxiv_id}"),
                        (eid, "arxiv_pdf_ext", f"https://arxiv.org/pdf/{arxiv_id}.pdf"),
                        (eid, "arxiv_pdf_v1", f"https://arxiv.org/pdf/{arxiv_id}v1"),
                        (eid, "arxiv_pdf_v1_ext", f"https://arxiv.org/pdf/{arxiv_id}v1.pdf"),
                    ]
                )
    return cases


_EVAL_ONLY_VARIANT_CASES = _build_eval_only_url_variants()


def test_issue_33_variant_suite_covers_all_eval_only_entries_and_exceeds_43_cases() -> None:
    catalog = load_catalog()
    expected_eval_ids = {
        e["id"] for e in catalog["entries"] if e["allowed_purposes"] == ["eval_only"]
    }
    covered_ids = {eid for eid, _, _ in _EVAL_ONLY_VARIANT_CASES}
    assert covered_ids == expected_eval_ids
    assert len(_EVAL_ONLY_VARIANT_CASES) >= 43


@pytest.mark.parametrize(
    ("entry_id", "variant_kind", "variant_url"),
    _EVAL_ONLY_VARIANT_CASES,
    ids=[f"{eid}-{kind}" for eid, kind, _ in _EVAL_ONLY_VARIANT_CASES],
)
def test_issue_33_equivalent_urls_for_eval_only_benchmarks_halt_training(
    entry_id: str,
    variant_kind: str,
    variant_url: str,
) -> None:
    """Issue #33: Every equivalent URL variant of every eval_only benchmark halts under for_training=True."""
    _ = (entry_id, variant_kind)
    out = autolab_wire.process_packet(
        {
            "resource_url": variant_url,
            "license_class": "MIT",
            "for_training": True,
            "commercial": False,
        }
    )
    assert out["halted"] is True
    assert out["halt_reason"] == "L5_ATLAS_LICENSE_OR_URL_BLOCK"
    assert out["platform_grounding"]["effective_license_class"] == "eval_only"
    assert out["platform_grounding"]["policy_violation"] == "eval_only_contamination_guard"
    assert out["platform_grounding"]["license_ok"] is False


def test_issue_33_missing_license_default_deny_and_same_owner_negative_match() -> None:
    """Issue #33: Unknown URL + missing license halts on explicit_spdx_license; catalog URL uses catalog SPDX."""
    # 1. Unknown URL + no license_class -> halts with rule explicit_spdx_license
    unknown_no_lic = autolab_wire.process_packet(
        {"resource_url": "https://example.org/unknown-dataset.tar.gz"}
    )
    assert unknown_no_lic["halted"] is True
    assert unknown_no_lic["halt_reason"] == "L5_ATLAS_LICENSE_OR_URL_BLOCK"
    assert unknown_no_lic["platform_grounding"]["policy_violation"] == "explicit_spdx_license"
    assert "rule=explicit_spdx_license" in unknown_no_lic["trace"][-1]["summary"]

    # 2. Empty packet {} -> resolves default stepbot catalog URL (MIT) -> PASS
    empty_pkt = autolab_wire.process_packet({})
    assert empty_pkt["halted"] is False
    assert empty_pkt["platform_grounding"]["effective_license_class"] == "permissive"
    assert empty_pkt["platform_grounding"]["license_ok"] is True

    # 3. Catalog URL + no license_class -> uses catalog entry's spdx_license
    msd_comm = autolab_wire.process_packet(
        {
            "resource_url": "https://github.com/rxn4chemistry/multimodal-spectroscopic-dataset",
            "for_training": True,
            "commercial": True,
        }
    )
    assert msd_comm["halted"] is True
    assert msd_comm["platform_grounding"]["effective_license_class"] == "share_alike"
    assert msd_comm["platform_grounding"]["policy_violation"] == "commercial_training_license_guard"

    msd_acad = autolab_wire.process_packet(
        {
            "resource_url": "https://github.com/rxn4chemistry/multimodal-spectroscopic-dataset",
            "for_training": True,
            "commercial": False,
        }
    )
    assert msd_acad["halted"] is False
    assert msd_acad["platform_grounding"]["effective_license_class"] == "share_alike"

    # 4. Negative test: unrelated repository under the same owner is NOT matched
    unrelated_mit = autolab_wire.process_packet(
        {
            "resource_url": "https://github.com/Future-House/other-repo",
            "license_class": "MIT",
            "for_training": True,
            "commercial": True,
        }
    )
    assert unrelated_mit["halted"] is False
    assert unrelated_mit["platform_grounding"]["effective_license_class"] == "permissive"

    unrelated_no_lic = autolab_wire.process_packet(
        {
            "resource_url": "https://github.com/Future-House/other-repo",
            "for_training": True,
        }
    )
    assert unrelated_no_lic["halted"] is True
    assert unrelated_no_lic["platform_grounding"]["policy_violation"] == "explicit_spdx_license"

    assert (
        canonicalize_url_for_match("https://hf.co/datasets/FutureHouse/LAB-Bench.git")
        == "https://huggingface.co/datasets/futurehouse/lab-bench"
    )


def test_issue_34_bioprobench_mutation_and_train_commercial_wire_agreement() -> None:
    """Issue #34: Reject license-vs-purpose/commercial contradictions and verify wire agreement."""
    catalog = load_catalog()
    mutated = copy.deepcopy(catalog)
    bpb = next(e for e in mutated["entries"] if e["id"] == "bioprobench")
    bpb["allowed_purposes"] = ["train_commercial"]
    bpb["commercial_use_ok"] = True
    errs = validate_catalog(mutated)
    assert any("bioprobench" in e and "train_commercial" in e for e in errs)
    assert any("bioprobench" in e and "commercial_use_ok" in e for e in errs)

    # Every dataset and chemistry_and_procurement entry with train_commercial must pass wire gate
    checked = 0
    for cat_name in ("dataset", "chemistry_and_procurement"):
        trainable = filter_entries(
            catalog["entries"],
            category=cat_name,
            allowed_purpose="train_commercial",
        )
        for entry in trainable:
            checked += 1
            first_url = entry["links"][0]["url"]
            res = autolab_wire.process_packet(
                {
                    "resource_url": first_url,
                    "license_class": entry["spdx_license"],
                    "for_training": True,
                    "commercial": True,
                }
            )
            assert res["halted"] is False, (
                f"Entry {entry['id']} ({entry['spdx_license']}) listed for train_commercial "
                f"halted on {first_url}: {res['trace'][-1]['summary']}"
            )
    assert checked >= 15


def _build_25_catalog_mutations() -> list[tuple[str, Callable[[dict[str, Any]], None], bool, bool]]:
    """Return 25 single-field catalog mutations and expected (py_rejects, schema_rejects) outcomes."""

    def _m01_root_extra(c: dict[str, Any]) -> None:
        c["unexpected_root"] = True

    def _m02_entry_extra(c: dict[str, Any]) -> None:
        c["entries"][0]["unexpected_entry_key"] = 123

    def _m03_bad_schema_version(c: dict[str, Any]) -> None:
        c["schema_version"] = "2.0.0"

    def _m04_bad_id_slug(c: dict[str, Any]) -> None:
        c["entries"][0]["id"] = "Invalid Uppercase ID"

    def _m05_http_link(c: dict[str, Any]) -> None:
        c["entries"][0]["links"][0]["url"] = "http://github.com/yaniguan/auto-lab"

    def _m06_bad_modality(c: dict[str, Any]) -> None:
        c["entries"][0]["analytical_modalities"] = ["Neutron_Reflectometry"]

    def _m07_eval_only_null_warning(c: dict[str, Any]) -> None:
        e = next(x for x in c["entries"] if x["id"] == "lab-bench")
        e["contamination_warning"] = None

    def _m08_empty_huggingface_id(c: dict[str, Any]) -> None:
        c["entries"][0]["huggingface_id"] = ""

    def _m09_whitespace_doi(c: dict[str, Any]) -> None:
        c["entries"][0]["doi"] = "   "

    def _m10_duplicate_purpose_item(c: dict[str, Any]) -> None:
        c["entries"][0]["allowed_purposes"] = ["tool_integration", "tool_integration"]

    def _m11_impossible_month_day(c: dict[str, Any]) -> None:
        c["entries"][0]["last_checked"] = "2026-13-45"

    def _m12_non_leap_feb_29(c: dict[str, Any]) -> None:
        c["entries"][0]["last_checked"] = "2026-02-29"

    def _m13_unknown_spdx_id(c: dict[str, Any]) -> None:
        c["entries"][0]["spdx_license"] = "UnknownMadeUp-9.9"

    def _m14_lowercase_or_operator(c: dict[str, Any]) -> None:
        c["entries"][0]["spdx_license"] = "MIT or Apache-2.0"

    def _m15_unbalanced_spdx_parens(c: dict[str, Any]) -> None:
        c["entries"][0]["spdx_license"] = "(MIT OR Apache-2.0"

    def _m16_loopback_link(c: dict[str, Any]) -> None:
        c["entries"][0]["links"][0]["url"] = "https://127.0.0.1/internal"

    def _m17_localhost_link(c: dict[str, Any]) -> None:
        c["entries"][0]["links"][0]["url"] = "https://localhost/internal"

    def _m18_private_ip_evidence(c: dict[str, Any]) -> None:
        c["entries"][0]["license_evidence"] = "https://10.0.0.8/LICENSE"

    def _m19_duplicate_entry_id(c: dict[str, Any]) -> None:
        c["entries"][1]["id"] = c["entries"][0]["id"]

    def _m20_duplicate_platform_id(c: dict[str, Any]) -> None:
        ot = next(x for x in c["entries"] if x["id"] == "opentrons")
        ot["hardware_capabilities"]["profiles"][1]["platform_id"] = "opentrons_ot2"

    def _m21_inverted_volume_bounds(c: dict[str, Any]) -> None:
        ot = next(x for x in c["entries"] if x["id"] == "opentrons")
        ot["hardware_capabilities"]["min_volume_ul"] = 2000.0
        ot["hardware_capabilities"]["max_volume_ul"] = 10.0

    def _m22_inverted_temp_bounds(c: dict[str, Any]) -> None:
        ot = next(x for x in c["entries"] if x["id"] == "opentrons")
        ot["hardware_capabilities"]["min_temp_c"] = 120.0
        ot["hardware_capabilities"]["max_temp_c"] = 20.0

    def _m23_undeclared_category(c: dict[str, Any]) -> None:
        c["categories"] = [cat for cat in c["categories"] if cat["id"] != "dataset"]

    def _m24_share_alike_train_commercial(c: dict[str, Any]) -> None:
        ord_e = next(x for x in c["entries"] if x["id"] == "open-reaction-database")
        ord_e["allowed_purposes"] = ["train_commercial", "train_academic"]

    def _m25_generic_deed_dataset_evidence(c: dict[str, Any]) -> None:
        wlp = next(x for x in c["entries"] if x["id"] == "wlp")
        wlp["license_evidence"] = "https://creativecommons.org/licenses/by/4.0/"

    return [
        ("01_root_extra_property", _m01_root_extra, True, True),
        ("02_entry_extra_property", _m02_entry_extra, True, True),
        ("03_bad_schema_version", _m03_bad_schema_version, True, True),
        ("04_bad_entry_id_slug", _m04_bad_id_slug, True, True),
        ("05_http_scheme_link", _m05_http_link, True, True),
        ("06_bad_modality_enum", _m06_bad_modality, True, True),
        ("07_eval_only_null_warning", _m07_eval_only_null_warning, True, True),
        ("08_empty_huggingface_id", _m08_empty_huggingface_id, True, True),
        ("09_whitespace_only_doi", _m09_whitespace_doi, True, True),
        ("10_duplicate_purpose_item", _m10_duplicate_purpose_item, True, True),
        ("11_impossible_month_day_date", _m11_impossible_month_day, True, True),
        ("12_non_leap_feb_29_date", _m12_non_leap_feb_29, True, False),
        ("13_unknown_spdx_id", _m13_unknown_spdx_id, True, False),
        ("14_lowercase_or_operator", _m14_lowercase_or_operator, True, False),
        ("15_unbalanced_spdx_parens", _m15_unbalanced_spdx_parens, True, False),
        ("16_loopback_ip_link", _m16_loopback_link, True, False),
        ("17_localhost_link", _m17_localhost_link, True, False),
        ("18_private_ip_license_evidence", _m18_private_ip_evidence, True, False),
        ("19_duplicate_entry_id", _m19_duplicate_entry_id, True, False),
        ("20_duplicate_platform_id", _m20_duplicate_platform_id, True, False),
        ("21_inverted_volume_bounds", _m21_inverted_volume_bounds, True, False),
        ("22_inverted_temp_bounds", _m22_inverted_temp_bounds, True, False),
        ("23_undeclared_root_category", _m23_undeclared_category, True, False),
        ("24_share_alike_train_commercial", _m24_share_alike_train_commercial, True, False),
        ("25_generic_deed_dataset_evidence", _m25_generic_deed_dataset_evidence, True, False),
    ]


@pytest.mark.parametrize(
    ("name", "mutator", "expected_py_rejects", "expected_schema_rejects"),
    _build_25_catalog_mutations(),
    ids=[item[0] for item in _build_25_catalog_mutations()],
)
def test_issue_34_differential_25_mutations_python_vs_json_schema(
    name: str,
    mutator: Callable[[dict[str, Any]], None],
    expected_py_rejects: bool,
    expected_schema_rejects: bool,
) -> None:
    """Issue #34: Differential validation matrix across 25 single-field catalog mutations."""
    _ = name
    base_catalog = load_catalog(validate=False)
    schema = load_schema()
    assert "Python-only" in schema["description"]

    mutated = copy.deepcopy(base_catalog)
    mutator(mutated)

    py_rejects = bool(validate_catalog(mutated))
    schema_rejects = bool(list(jsonschema.Draft202012Validator(schema).iter_errors(mutated)))

    assert py_rejects is expected_py_rejects
    assert schema_rejects is expected_schema_rejects


def test_issue_35_no_generic_deed_or_bare_arxiv_evidence_and_fixed_records(
    tmp_path: Path,
) -> None:
    """Issue #35: Enforce upstream-only dataset license_evidence, fixed records, and check_licenses.py."""
    catalog = load_catalog()
    by_id = {e["id"]: e for e in catalog["entries"]}

    for entry in catalog["entries"]:
        if entry["category"] in ("dataset", "chemistry_and_procurement"):
            assert not is_generic_or_bare_arxiv_license_evidence(entry["license_evidence"]), (
                f"{entry['id']} uses generic deed or bare arXiv URL: {entry['license_evidence']}"
            )

    for forbidden_ev in (
        "https://creativecommons.org/licenses/by/4.0/",
        "https://creativecommons.org/publicdomain/zero/1.0/",
        "https://spdx.org/licenses/CDLA-Sharing-1.0.html",
        "https://opensource.org/licenses/MIT",
        "https://arxiv.org/abs/2407.10362",
    ):
        assert is_generic_or_bare_arxiv_license_evidence(forbidden_ev) is True
        mut = copy.deepcopy(catalog)
        wlp = next(x for x in mut["entries"] if x["id"] == "wlp")
        wlp["license_evidence"] = forbidden_ev
        assert any("license_evidence" in err for err in validate_catalog(mut))

    # Fixed upstream license and role assertions
    assert by_id["aqsoldb"]["spdx_license"] == "CC0-1.0"
    assert "10.7910/DVN/OVHAW8" in by_id["aqsoldb"]["license_evidence"]

    assert by_id["calisol-23"]["spdx_license"] == "NOASSERTION"
    assert by_id["calisol-23"]["commercial_use_ok"] is False
    assert "train_commercial" not in by_id["calisol-23"]["allowed_purposes"]

    assert by_id["matterix"]["spdx_license"] == "NOASSERTION"
    assert by_id["matterix"]["commercial_use_ok"] is False

    assert by_id["droid"]["huggingface_id"] is None
    assert by_id["droid"]["license_evidence"] == "https://droid-dataset.github.io/"

    assert by_id["multimodal-spectroscopic-dataset"]["license_evidence"] == "https://zenodo.org/records/11611178"
    assert by_id["dcase-task2-asd"]["license_evidence"] == "https://zenodo.org/records/10902294"

    pt_role = by_id["labbench-posttrain"]["role"]
    for supported in ("SFT", "DPO", "GRPO", "GDPO"):
        assert supported in pt_role
    for overclaimed in ("MPO", "TROPD", "PPO", "DAPO"):
        assert overclaimed not in pt_role

    wf_role = by_id["wignerflow"]["role"].lower()
    assert "argon" in wf_role

    # Offline check_licenses.py execution + mismatch unit check
    out_json = tmp_path / "license_status.json"
    assert check_licenses_mod.main(["--offline", "--json-out", str(out_json)]) == 0
    assert out_json.is_file()

    ok_match, st_match = check_licenses_mod.spdx_matches_upstream("CC-BY-4.0", "cc-by-4.0")
    assert ok_match is True and st_match == "match"
    ok_mis, st_mis = check_licenses_mod.spdx_matches_upstream("CC-BY-4.0", "mit")
    assert ok_mis is False and st_mis == "mismatch"


def test_issue_36_generated_lean_parity_260_guards_drift_detection_and_docs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Issue #36: Verify 260 generated Lean #guard lines, drift detection on Python mutation, and docs."""
    parity_path = REPO_ROOT / "lean" / "LabAtlasLean" / "Parity.lean"
    assert parity_path.is_file()
    committed = parity_path.read_text(encoding="utf-8")
    regenerated = gen_lean_parity_mod.render_lean_parity_guards()
    assert committed == regenerated

    guard_lines = [ln for ln in committed.splitlines() if ln.startswith("#guard ")]
    assert len(guard_lines) == 260
    assert sum(1 for ln in guard_lines if "checkAtlasResource" in ln) == 160
    assert sum(1 for ln in guard_lines if "LicenseClass.conj" in ln) == 25
    assert sum(1 for ln in guard_lines if "LicenseClass.disj" in ln) == 25
    assert sum(1 for ln in guard_lines if "checkMcpToolCall" in ln) == 50

    assert gen_lean_parity_mod.main(["--check"]) == 0

    # Mutating Python policy without regenerating Parity.lean must fail --check
    monkeypatch.setattr(
        gen_lean_parity_mod,
        "check_atlas_resource_policy",
        lambda **_kw: "https_ssrf_guard",
    )
    assert gen_lean_parity_mod.main(["--check"]) == 1

    for doc_rel in ("README.md", "docs/ARCHITECTURE_AND_HISTORY.md", "lean/README.md"):
        doc_text = (REPO_ROOT / doc_rel).read_text(encoding="utf-8").lower()
        assert "boolean" in doc_text
        assert "url" in doc_text
        assert "spdx" in doc_text
