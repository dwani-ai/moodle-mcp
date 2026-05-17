"""Google ADK education agent builders and skill metadata."""

from moodle_mcp.adk.skills import EDUCATION_SKILLS, EducationSkill

__all__ = ["EDUCATION_SKILLS", "EducationSkill", "build_education_orchestrator"]


def __getattr__(name: str):
    if name == "build_education_orchestrator":
        from moodle_mcp.adk.orchestrator import build_education_orchestrator

        return build_education_orchestrator
    raise AttributeError(name)
