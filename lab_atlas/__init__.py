"""lab_atlas: Machine-readable catalog, schema validator, and link auditor for lab-automation-atlas."""

from .catalog import (
    ALLOWED_CATEGORIES,
    ALLOWED_LAYERS,
    ALLOWED_PURPOSES,
    ALLOWED_SCRAPING_POLICIES,
    ALLOWED_STATUSES,
    build_compatibility_matrix,
    dump_catalog_yaml,
    filter_entries,
    load_catalog,
    load_schema,
    validate_catalog,
)
from .linkcheck import (
    DEFAULT_USER_AGENT,
    WAF_403_ALLOWLIST_DOMAINS,
    LinkCheckResult,
    LocalLinkResult,
    audit_markdown_files,
    check_local_link,
    check_url,
     check_urls_concurrent,
    extract_links,
    extract_urls,
    validate_url_target,
    write_link_report,
)
from .render import (
    check_readme_sync,
    render_catalog_markdown,
    render_compatibility_markdown,
    sync_readme,
)

__version__ = "0.2.0"

__all__ = [
    "__version__",
    "ALLOWED_CATEGORIES",
    "ALLOWED_LAYERS",
    "ALLOWED_PURPOSES",
    "ALLOWED_SCRAPING_POLICIES",
    "ALLOWED_STATUSES",
    "DEFAULT_USER_AGENT",
    "WAF_403_ALLOWLIST_DOMAINS",
    "LinkCheckResult",
    "LocalLinkResult",
    "audit_markdown_files",
    "build_compatibility_matrix",
    "check_local_link",
    "check_readme_sync",
    "check_url",
    "check_urls_concurrent",
    "dump_catalog_yaml",
    "extract_links",
    "extract_urls",
    "filter_entries",
    "load_catalog",
    "load_schema",
    "render_catalog_markdown",
    "render_compatibility_markdown",
    "sync_readme",
    "validate_catalog",
    "validate_url_target",
    "write_link_report",
]
