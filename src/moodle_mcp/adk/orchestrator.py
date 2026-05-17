from __future__ import annotations

from typing import TYPE_CHECKING, Any

from moodle_mcp.adk.agents import (
    EDUCATION_AGENT_SPECS,
    build_education_sub_agents,
    build_litellm_model,
    build_moodle_mcp_toolset,
)
from moodle_mcp.adk.skills import EDUCATION_SKILLS

if TYPE_CHECKING:
    from moodle_mcp.config import Settings


def _orchestrator_instruction() -> str:
    agent_lines = "\n".join(f"- {spec.name}: {spec.description}" for spec in EDUCATION_AGENT_SPECS)
    skill_lines = "\n".join(f"- {skill.name}: {skill.purpose}" for skill in EDUCATION_SKILLS)
    return (
        "You are the education orchestrator for Moodle. Route each request to the most relevant "
        "specialist sub-agent, or answer directly when the request is simple. Use Moodle MCP tools "
        "for Moodle facts and Moodle mutations. If the required Moodle capability is not implemented "
        "yet, provide a draft, plan, or manual Moodle workflow instead of pretending the change was made.\n\n"
        f"Available specialist agents:\n{agent_lines}\n\n"
        f"Available education skills:\n{skill_lines}"
    )


def build_education_orchestrator(settings: Settings | None = None) -> Any:
    try:
        from google.adk.agents import Agent
    except ImportError as exc:
        raise RuntimeError("Install the optional ADK dependency with `pip install .[adk]`.") from exc

    from moodle_mcp.config import get_settings

    resolved_settings = settings or get_settings()
    return Agent(
        name="education_orchestrator",
        model=build_litellm_model(resolved_settings),
        description="Routes Moodle education requests to specialist ADK agents and skills.",
        instruction=_orchestrator_instruction(),
        tools=[toolset] if (toolset := build_moodle_mcp_toolset(resolved_settings)) else [],
        sub_agents=build_education_sub_agents(resolved_settings),
    )
