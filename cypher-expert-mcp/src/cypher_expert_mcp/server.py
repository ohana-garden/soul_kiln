"""MCP Server for Cypher Expert - World-class Cypher query generation and optimization."""

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Resource, TextContent, Tool

from .tools.query import (
    CypherResult,
    ExecutionResult,
    ChatResponse,
    generate_cypher_impl,
    execute_cypher_impl,
    cypher_chat_impl,
)
from .tools.schema import (
    SchemaInfo,
    IndexSuggestion,
    introspect_schema_impl,
    suggest_indexes_impl,
)
from .tools.validate import (
    AnalysisResult,
    LintResult,
    analyze_query_impl,
    lint_cypher_impl,
    dry_run_impl,
)
from .knowledge import load_reference_docs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """Configuration for the Cypher Expert MCP server."""

    host: str = "localhost"
    port: int = 6379
    graph_name: str = "virtue_basin"
    max_result_rows: int = 1000
    query_timeout_ms: int = 30000


# Global server instance
server = Server("cypher-expert")

# Global configuration (can be updated via environment or config file)
config = ServerConfig()


def set_config(new_config: ServerConfig) -> None:
    """Update server configuration."""
    global config
    config = new_config


# ============================================================================
# Tool Definitions
# ============================================================================

TOOLS = [
    Tool(
        name="generate_cypher",
        description=(
            "Generate optimized Cypher queries from natural language requests. "
            "Automatically fetches schema context and applies optimization patterns. "
            "Returns the query with explanation and confidence score."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "request": {
                    "type": "string",
                    "description": "Natural language description of the query you need",
                },
                "schema_context": {
                    "type": "boolean",
                    "description": "Auto-fetch current schema for context (default: true)",
                    "default": True,
                },
                "optimize": {
                    "type": "boolean",
                    "description": "Run through optimization pass (default: true)",
                    "default": True,
                },
            },
            "required": ["request"],
        },
    ),
    Tool(
        name="execute_cypher",
        description=(
            "Execute a Cypher query against the connected graph database. "
            "Includes safety rails: query plan inspection, result limiting, "
            "and parameterization enforcement."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The Cypher query to execute",
                },
                "params": {
                    "type": "object",
                    "description": "Query parameters (for $param placeholders)",
                    "default": {},
                },
                "explain_first": {
                    "type": "boolean",
                    "description": "Show query plan before running (default: true)",
                    "default": True,
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum rows to return (default: 100)",
                    "default": 100,
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="analyze_query",
        description=(
            "Analyze a Cypher query using PROFILE/EXPLAIN to identify performance "
            "bottlenecks and suggest improvements. Returns query plan, cost estimates, "
            "and optimization recommendations."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The Cypher query to analyze",
                },
                "params": {
                    "type": "object",
                    "description": "Query parameters for accurate profiling",
                    "default": {},
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="introspect_schema",
        description=(
            "Retrieve the complete schema of the connected graph database. "
            "Returns labels, relationship types, property keys, indexes, and constraints."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    Tool(
        name="suggest_indexes",
        description=(
            "Analyze query patterns and suggest indexes to improve performance. "
            "Takes into account existing indexes and query workload."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "queries": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Sample queries to analyze for index suggestions",
                },
            },
            "required": ["queries"],
        },
    ),
    Tool(
        name="cypher_chat",
        description=(
            "Multi-turn conversation for complex query building. "
            "Maintains conversation context for iterative refinement. "
            "Useful for exploring data, understanding schema, or building complex queries step-by-step."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Your message or question about Cypher queries",
                },
                "conversation_id": {
                    "type": "string",
                    "description": "ID to continue a previous conversation (optional)",
                },
            },
            "required": ["message"],
        },
    ),
    Tool(
        name="lint_cypher",
        description=(
            "Validate Cypher syntax and check for common anti-patterns. "
            "Returns syntax errors, warnings, and style suggestions."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The Cypher query to lint",
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="dry_run",
        description=(
            "Execute a Cypher query in dry-run mode (EXPLAIN without execution). "
            "Validates query structure without modifying data."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The Cypher query to dry-run",
                },
                "params": {
                    "type": "object",
                    "description": "Query parameters",
                    "default": {},
                },
            },
            "required": ["query"],
        },
    ),
]


# ============================================================================
# Tool Handlers
# ============================================================================


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    try:
        if name == "generate_cypher":
            result = await generate_cypher_impl(
                request=arguments["request"],
                schema_context=arguments.get("schema_context", True),
                optimize=arguments.get("optimize", True),
                config=config,
            )
            return [TextContent(type="text", text=result.to_json())]

        elif name == "execute_cypher":
            result = await execute_cypher_impl(
                query=arguments["query"],
                params=arguments.get("params", {}),
                explain_first=arguments.get("explain_first", True),
                limit=arguments.get("limit", 100),
                config=config,
            )
            return [TextContent(type="text", text=result.to_json())]

        elif name == "analyze_query":
            result = await analyze_query_impl(
                query=arguments["query"],
                params=arguments.get("params", {}),
                config=config,
            )
            return [TextContent(type="text", text=result.to_json())]

        elif name == "introspect_schema":
            result = await introspect_schema_impl(config=config)
            return [TextContent(type="text", text=result.to_json())]

        elif name == "suggest_indexes":
            result = await suggest_indexes_impl(
                queries=arguments["queries"],
                config=config,
            )
            return [TextContent(type="text", text=result.to_json())]

        elif name == "cypher_chat":
            result = await cypher_chat_impl(
                message=arguments["message"],
                conversation_id=arguments.get("conversation_id"),
                config=config,
            )
            return [TextContent(type="text", text=result.to_json())]

        elif name == "lint_cypher":
            result = await lint_cypher_impl(query=arguments["query"])
            return [TextContent(type="text", text=result.to_json())]

        elif name == "dry_run":
            result = await dry_run_impl(
                query=arguments["query"],
                params=arguments.get("params", {}),
                config=config,
            )
            return [TextContent(type="text", text=result.to_json())]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        logger.exception(f"Error in tool {name}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


# ============================================================================
# Resource Definitions
# ============================================================================


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="cypher://reference",
            name="Cypher Reference Documentation",
            description="Complete Cypher syntax reference and best practices",
            mimeType="text/markdown",
        ),
        Resource(
            uri="cypher://schema",
            name="Current Graph Schema",
            description="Live schema introspection from connected database",
            mimeType="application/json",
        ),
        Resource(
            uri="cypher://optimization",
            name="Optimization Patterns",
            description="Query optimization patterns and rewrite rules",
            mimeType="text/markdown",
        ),
        Resource(
            uri="cypher://examples",
            name="Common Query Examples",
            description="50+ annotated Cypher query examples",
            mimeType="text/markdown",
        ),
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource by URI."""
    docs = load_reference_docs()

    if uri == "cypher://reference":
        return docs.get("cypher_reference", "Reference documentation not found")

    elif uri == "cypher://schema":
        schema = await introspect_schema_impl(config=config)
        return schema.to_json()

    elif uri == "cypher://optimization":
        return docs.get("optimization_patterns", "Optimization patterns not found")

    elif uri == "cypher://examples":
        return docs.get("common_queries", "Common queries not found")

    else:
        return f"Unknown resource: {uri}"


# ============================================================================
# Main Entry Point
# ============================================================================


async def main():
    """Run the MCP server."""
    logger.info("Starting Cypher Expert MCP Server")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def run():
    """Entry point for the server."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
