"""Community-inspired L5 hardware-MCP capability extensions for lab-automation-atlas."""

from __future__ import annotations

from community_extensions.mcp_capability_cards import (
    CompiledMcpCapabilityCard,
    HardwareCapabilitySpec,
    McpCallDecision,
    McpCardCompilationError,
    audit_mcp_tool_descriptor,
    build_prompt_only_schema,
    compile_mcp_capability_card,
    run_benchmark,
    validate_with_prompt_only_schema,
    validate_with_typed_lean_mcp_card,
)

__all__ = [
    "CompiledMcpCapabilityCard",
    "HardwareCapabilitySpec",
    "McpCallDecision",
    "McpCardCompilationError",
    "audit_mcp_tool_descriptor",
    "build_prompt_only_schema",
    "compile_mcp_capability_card",
    "run_benchmark",
    "validate_with_prompt_only_schema",
    "validate_with_typed_lean_mcp_card",
]
