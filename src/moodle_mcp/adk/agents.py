from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from moodle_mcp.adk.moodle_tools import ADK_MOODLE_TOOLS
from moodle_mcp.adk.skills import SKILLS_BY_NAME, skill_instruction

if TYPE_CHECKING:
    from moodle_mcp.config import Settings


@dataclass(frozen=True)
class EducationAgentSpec:
    name: str
    description: str
    skill_names: tuple[str, ...]
    role_instruction: str

    def instruction(self) -> str:
        return (
            f"{self.role_instruction}\n\n"
            "Use the Moodle MCP tool names listed in each skill when a tool is available. "
            "If a needed Moodle capability is listed as a future tool, produce a plan or draft "
            "and say that Moodle write-back requires additional Web Services integration.\n\n"
            f"{skill_instruction(self.skill_names)}"
        )


EDUCATION_AGENT_SPECS: tuple[EducationAgentSpec, ...] = (
    EducationAgentSpec(
        name="course_creator_agent",
        description="Plans and creates Moodle course shells, lessons, and starter resources.",
        skill_names=("course-creation-skill", "lesson-planning-skill", "content-curator-skill"),
        role_instruction=(
            "You are a course creator agent for instructors and instructional designers. "
            "Prioritize clear learning outcomes, Moodle-ready structure, and explicit confirmation "
            "before creating visible course content."
        ),
    ),
    EducationAgentSpec(
        name="assessment_builder_agent",
        description="Designs quizzes, rubrics, assignments, and assessment plans.",
        skill_names=("assessment-builder-skill", "lesson-planning-skill"),
        role_instruction=(
            "You are an assessment builder agent. Create fair, outcome-aligned assessment drafts "
            "and distinguish draft content from Moodle changes that require future tools."
        ),
    ),
    EducationAgentSpec(
        name="student_tutor_agent",
        description="Helps learners understand Moodle course content and choose next study steps.",
        skill_names=("student-tutor-skill", "support-assistant-skill"),
        role_instruction=(
            "You are a student tutor agent. Ground guidance in visible Moodle course contents, "
            "keep explanations supportive, and never perform creator or administrator actions."
        ),
    ),
    EducationAgentSpec(
        name="admin_enrollment_agent",
        description="Guides enrollment, access, roles, cohorts, and Moodle administration workflows.",
        skill_names=("admin-enrollment-skill", "support-assistant-skill"),
        role_instruction=(
            "You are an admin enrollment agent. Treat enrollment and role changes as sensitive, "
            "require explicit confirmation, and provide manual Moodle steps when direct tools are missing."
        ),
    ),
    EducationAgentSpec(
        name="progress_monitor_agent",
        description="Reviews engagement signals and recommends learner support interventions.",
        skill_names=("progress-engagement-skill", "student-tutor-skill"),
        role_instruction=(
            "You are a progress monitor agent. Separate observed Moodle data from inference, "
            "avoid fabricated grades or completion claims, and recommend supportive interventions."
        ),
    ),
    EducationAgentSpec(
        name="content_curator_agent",
        description="Finds, organizes, and adds learning resources to Moodle courses.",
        skill_names=("content-curator-skill", "course-creation-skill"),
        role_instruction=(
            "You are a content curator agent. Choose resources that fit the objective, learner level, "
            "and license constraints, and only add URL resources after target placement is clear."
        ),
    ),
)


def build_litellm_model(settings: "Settings | None" = None) -> Any:
    try:
        from google.adk.models.lite_llm import LiteLlm
    except ImportError as exc:
        raise RuntimeError("Install the optional ADK dependency with `pip install .[adk]`.") from exc

    from moodle_mcp.config import get_settings

    resolved_settings = settings or get_settings()
    return LiteLlm(
        model=resolved_settings.litellm_model,
        api_base=str(resolved_settings.llm_base_url),
        api_key=resolved_settings.llm_api_key_value,
    )


def _skill_supported_tools(skill_names: tuple[str, ...]) -> list[str]:
    return sorted(
        {
            tool
            for skill_name in skill_names
            for tool in SKILLS_BY_NAME[skill_name].supported_tools
        }
    )


def _tools_for_agent(settings: "Settings", skill_names: tuple[str, ...]) -> list[Any]:
    settings.validate_runtime()
    return [ADK_MOODLE_TOOLS[tool_name] for tool_name in _skill_supported_tools(skill_names)]


def build_education_sub_agents(settings: "Settings | None" = None) -> list[Any]:
    try:
        from google.adk.agents import Agent
    except ImportError as exc:
        raise RuntimeError("Install the optional ADK dependency with `pip install .[adk]`.") from exc

    from moodle_mcp.config import get_settings

    resolved_settings = settings or get_settings()
    return [
        Agent(
            name=spec.name,
            model=build_litellm_model(resolved_settings),
            description=spec.description,
            instruction=spec.instruction(),
            tools=_tools_for_agent(resolved_settings, spec.skill_names),
        )
        for spec in EDUCATION_AGENT_SPECS
    ]
