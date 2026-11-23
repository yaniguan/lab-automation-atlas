"""Validate atlas.json, synchronize package resources, and regenerate README.md catalog tables."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from lab_atlas.catalog import RESOURCE_DIR, validate_catalog  # noqa: E402
from lab_atlas.render import check_readme_sync, sync_readme  # noqa: E402


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Synchronize or verify README.md and package resources against atlas.json."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify byte-for-byte synchronization without modifying files.",
    )
    args = parser.parse_args(argv)

    catalog_path = ROOT / "atlas.json"
    schema_path = ROOT / "schema" / "atlas.schema.json"
    readme_path = ROOT / "README.md"
    pkg_catalog_path = RESOURCE_DIR / "atlas.json"
    pkg_schema_path = RESOURCE_DIR / "atlas.schema.json"

    catalog_text = catalog_path.read_text(encoding="utf-8")
    schema_text = schema_path.read_text(encoding="utf-8")
    catalog = json.loads(catalog_text)

    errors = validate_catalog(catalog)
    if errors:
        for err in errors:
            print(f"SCHEMA ERROR: {err}", file=sys.stderr)
        return 1

    if args.check:
        ok = True
        if not pkg_catalog_path.is_file() or pkg_catalog_path.read_text(encoding="utf-8") != catalog_text:
            print("DRIFT: lab_atlas/resources/atlas.json differs from atlas.json", file=sys.stderr)
            ok = False
        if not pkg_schema_path.is_file() or pkg_schema_path.read_text(encoding="utf-8") != schema_text:
            print("DRIFT: lab_atlas/resources/atlas.schema.json differs from schema/atlas.schema.json", file=sys.stderr)
            ok = False
        if not check_readme_sync(readme_path, catalog):
            print("DRIFT: README.md catalog tables differ from atlas.json", file=sys.stderr)
            ok = False
        if not ok:
            return 1
        print(f"OK: {len(catalog['entries'])} entries synchronized across atlas.json, resources, and README.md.")
        return 0

    RESOURCE_DIR.mkdir(parents=True, exist_ok=True)
    pkg_catalog_path.write_text(catalog_text, encoding="utf-8")
    pkg_schema_path.write_text(schema_text, encoding="utf-8")
    changed = sync_readme(readme_path, catalog)
    print(
        f"Synchronized {len(catalog['entries'])} entries "
        f"(README.md {'updated' if changed else 'unchanged'})."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
