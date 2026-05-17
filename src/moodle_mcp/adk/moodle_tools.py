from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from moodle_mcp.config import Settings
    from moodle_mcp.tools import UserRole


@dataclass(frozen=True)
class MoodleToolContext:
    settings: "Settings"
    role: "UserRole"
    user_id: int | None


_tool_context: ContextVar[MoodleToolContext | None] = ContextVar("moodle_tool_context", default=None)


@contextmanager
def bind_moodle_tool_context(context: MoodleToolContext):
    token = _tool_context.set(context)
    try:
        yield
    finally:
        _tool_context.reset(token)


def _current_context() -> MoodleToolContext:
    context = _tool_context.get()
    if context is None:
        raise RuntimeError("Moodle tool context is not bound for this ADK invocation.")
    return context


async def _call_mcp_tool(name: str, arguments: dict[str, Any] | None = None) -> Any:
    from moodle_mcp.mcp_client import mcp_client_session, serialize_mcp_result

    context = _current_context()
    if not context.settings.mcp_server_url:
        raise RuntimeError("MCP_SERVER_URL is required for ADK Moodle tools.")

    tool_arguments = dict(arguments or {})
    tool_arguments["role"] = context.role.value
    if context.user_id is not None:
        tool_arguments["user_id"] = context.user_id

    async with mcp_client_session(
        str(context.settings.mcp_server_url),
        context.settings.mcp_client_transport,
    ) as session:
        result = await session.call_tool(name, tool_arguments)
    return serialize_mcp_result(result)


async def get_current_user() -> Any:
    """Get the current Moodle Web Services user."""

    return await _call_mcp_tool("get_current_user")


async def list_course_categories() -> Any:
    """List Moodle course categories."""

    return await _call_mcp_tool("list_course_categories")


async def create_course(
    fullname: str,
    shortname: str,
    categoryid: int,
    summary: str = "",
    visible: bool = True,
) -> Any:
    """Create a Moodle course shell. Only creator users may use this tool."""

    return await _call_mcp_tool(
        "create_course",
        {
            "fullname": fullname,
            "shortname": shortname,
            "categoryid": categoryid,
            "summary": summary,
            "visible": visible,
        },
    )


async def add_url_resource(
    courseid: int,
    section: int,
    name: str,
    externalurl: str,
    intro: str = "",
) -> Any:
    """Add a URL resource to a Moodle course section. Only creator users may use this tool."""

    return await _call_mcp_tool(
        "add_url_resource",
        {
            "courseid": courseid,
            "section": section,
            "name": name,
            "externalurl": externalurl,
            "intro": intro,
        },
    )


async def add_page_resource(
    courseid: int,
    section: int,
    name: str,
    content: str,
    intro: str = "",
) -> Any:
    """Add a Moodle page resource to a course section. Only creator users may use this tool."""

    return await _call_mcp_tool(
        "add_page_resource",
        {
            "courseid": courseid,
            "section": section,
            "name": name,
            "content": content,
            "intro": intro,
        },
    )


async def list_my_courses() -> Any:
    """List the Moodle courses available to the bound user."""

    return await _call_mcp_tool("list_my_courses")


async def get_course_contents(courseid: int) -> Any:
    """Get Moodle course sections and modules."""

    return await _call_mcp_tool("get_course_contents", {"courseid": courseid})


async def get_activities_completion_status(courseid: int, userid: int | None = None) -> Any:
    """Get activity completion status for a Moodle course and user."""

    arguments: dict[str, Any] = {"courseid": courseid}
    if userid is not None:
        arguments["userid"] = userid
    return await _call_mcp_tool("get_activities_completion_status", arguments)


async def get_users_by_field(field: str, values: list[str]) -> Any:
    """Look up Moodle users by id, username, or email. Only creator users may use this tool."""

    return await _call_mcp_tool("get_users_by_field", {"field": field, "values": values})


ADK_MOODLE_TOOLS = {
    "get_current_user": get_current_user,
    "list_course_categories": list_course_categories,
    "create_course": create_course,
    "add_url_resource": add_url_resource,
    "add_page_resource": add_page_resource,
    "list_my_courses": list_my_courses,
    "get_course_contents": get_course_contents,
    "get_activities_completion_status": get_activities_completion_status,
    "get_users_by_field": get_users_by_field,
}
