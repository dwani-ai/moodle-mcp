import json
from typing import Any

from openai import AsyncOpenAI
from pydantic import BaseModel

from moodle_mcp.config import Settings, get_settings
from moodle_mcp.moodle import MoodleClient
from moodle_mcp.tools import (
    AddUrlResourceInput,
    CourseContentsInput,
    CreateCourseInput,
    ToolContext,
    UserRole,
    moodle_add_url_resource,
    moodle_create_course,
    moodle_get_course_contents,
    moodle_get_current_user,
    moodle_list_course_categories,
    moodle_list_my_courses,
)


class ChatResult(BaseModel):
    role: UserRole
    answer: str
    tool_results: list[dict[str, Any]] = []


TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "moodle_get_current_user",
            "description": "Get the current Moodle Web Services user.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "moodle_list_course_categories",
            "description": "List Moodle course categories.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "moodle_create_course",
            "description": "Create a Moodle course. Only creator users may use this tool.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fullname": {"type": "string"},
                    "shortname": {"type": "string"},
                    "categoryid": {"type": "integer"},
                    "summary": {"type": "string"},
                    "visible": {"type": "boolean"},
                },
                "required": ["fullname", "shortname", "categoryid"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "moodle_add_url_resource",
            "description": "Add a URL resource to a Moodle course section. Only creators may use it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "courseid": {"type": "integer"},
                    "section": {"type": "integer"},
                    "name": {"type": "string"},
                    "externalurl": {"type": "string"},
                    "intro": {"type": "string"},
                },
                "required": ["courseid", "section", "name", "externalurl"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "moodle_list_my_courses",
            "description": "List the Moodle courses available to the current user.",
            "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "moodle_get_course_contents",
            "description": "Get sections and modules for a Moodle course.",
            "parameters": {
                "type": "object",
                "properties": {"courseid": {"type": "integer"}},
                "required": ["courseid"],
                "additionalProperties": False,
            },
        },
    },
]


class MoodleAgent:
    """OpenAI-compatible chat orchestrator for the ADK-facing Moodle agent.

    Google ADK can host this orchestration through the optional `build_google_adk_agent`
    factory below. Keeping the Moodle tools in plain async functions also makes them
    straightforward to expose through MCP and test independently.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.openai = AsyncOpenAI(
            api_key=self.settings.llm_api_key_value,
            base_url=str(self.settings.llm_base_url),
        )

    async def chat(self, *, role: UserRole, message: str, user_id: int | None = None) -> ChatResult:
        context = ToolContext(role=role, user_id=user_id)
        system_prompt = self._system_prompt(role)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ]
        completion = await self.openai.chat.completions.create(
            model=self.settings.llm_model,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )
        assistant_message = completion.choices[0].message
        tool_results = await self._run_tool_calls(assistant_message.tool_calls or [], context)

        if not tool_results:
            return ChatResult(role=role, answer=assistant_message.content or "", tool_results=[])

        messages.append(assistant_message.model_dump(exclude_none=True))
        for result in tool_results:
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": result["tool_call_id"],
                    "content": json.dumps(result["result"], default=str),
                }
            )
        final = await self.openai.chat.completions.create(
            model=self.settings.llm_model,
            messages=messages,
        )
        return ChatResult(
            role=role,
            answer=final.choices[0].message.content or "",
            tool_results=tool_results,
        )

    async def _run_tool_calls(
        self,
        tool_calls: list[Any],
        context: ToolContext,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        async with MoodleClient(
            base_url=str(self.settings.moodle_base_url),
            token=self.settings.moodle_token_value,
            rest_format=self.settings.moodle_rest_format,
        ) as moodle:
            for call in tool_calls:
                name = call.function.name
                arguments = json.loads(call.function.arguments or "{}")
                result = await self._dispatch_tool(moodle, context, name, arguments)
                results.append(
                    {"tool_call_id": call.id, "tool_name": name, "arguments": arguments, "result": result}
                )
        return results

    async def _dispatch_tool(
        self,
        moodle: MoodleClient,
        context: ToolContext,
        name: str,
        arguments: dict[str, Any],
    ) -> Any:
        if name == "moodle_get_current_user":
            return await moodle_get_current_user(moodle, context)
        if name == "moodle_list_course_categories":
            return await moodle_list_course_categories(moodle, context)
        if name == "moodle_create_course":
            return await moodle_create_course(moodle, context, CreateCourseInput(**arguments))
        if name == "moodle_add_url_resource":
            return await moodle_add_url_resource(moodle, context, AddUrlResourceInput(**arguments))
        if name == "moodle_list_my_courses":
            return await moodle_list_my_courses(moodle, context)
        if name == "moodle_get_course_contents":
            return await moodle_get_course_contents(moodle, context, CourseContentsInput(**arguments))
        raise ValueError(f"Unknown tool: {name}")

    def _system_prompt(self, role: UserRole) -> str:
        shared = (
            "You are a Moodle assistant. Use Moodle tools whenever course data or mutations are "
            "needed. Ask for missing required fields before creating anything. Keep responses concise."
        )
        if role == UserRole.CREATOR:
            return (
                f"{shared} The user is a creator. They may create courses and add basic URL "
                "resources. Confirm the intended course details before destructive or visible changes."
            )
        return (
            f"{shared} The user is a student. They may discover and consume courses, but must not "
            "create or change Moodle content."
        )


def build_google_adk_agent() -> Any:
    """Create a Google ADK Agent when the optional ADK package is installed."""

    try:
        from google.adk.agents import Agent
    except ImportError as exc:
        raise RuntimeError("Install the optional ADK dependency with `pip install .[adk]`.") from exc

    return Agent(
        name="moodle_agent",
        model=get_settings().llm_model,
        instruction=(
            "You are a Moodle agent with creator and student flows. Use the configured MCP "
            "Moodle tools for all Moodle state and content operations."
        ),
    )
