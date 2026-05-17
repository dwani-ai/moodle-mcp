import argparse
from typing import Any

from mcp.server.fastmcp import FastMCP

from moodle_mcp.config import get_settings
from moodle_mcp.moodle import MoodleClient
from moodle_mcp.tools import (
    AddUrlResourceInput,
    AddPageResourceInput,
    CompletionStatusInput,
    CourseContentsInput,
    CreateCourseInput,
    ToolContext,
    UserRole,
    UserLookupInput,
    moodle_add_url_resource,
    moodle_add_page_resource,
    moodle_create_course,
    moodle_get_activities_completion_status,
    moodle_get_course_contents,
    moodle_get_current_user,
    moodle_get_users_by_field,
    moodle_list_course_categories,
    moodle_list_my_courses,
)

def _context(role: str, user_id: int | None = None) -> ToolContext:
    return ToolContext(role=UserRole(role), user_id=user_id)


async def _client() -> MoodleClient:
    settings = get_settings()
    return MoodleClient(
        base_url=str(settings.moodle_base_url),
        token=settings.moodle_token_value,
        rest_format=settings.moodle_rest_format,
    )


def create_mcp_server(*, host: str = "127.0.0.1", port: int = 8000) -> FastMCP:
    mcp = FastMCP("moodle-mcp", host=host, port=port)

    @mcp.tool()
    async def get_current_user(role: str = "student", user_id: int | None = None) -> dict[str, Any]:
        async with await _client() as client:
            return await moodle_get_current_user(client, _context(role, user_id))

    @mcp.tool()
    async def list_course_categories(
        role: str = "student",
        user_id: int | None = None,
    ) -> list[dict[str, Any]]:
        async with await _client() as client:
            return await moodle_list_course_categories(client, _context(role, user_id))

    @mcp.tool()
    async def create_course(
        fullname: str,
        shortname: str,
        categoryid: int,
        summary: str = "",
        visible: bool = True,
        role: str = "student",
        user_id: int | None = None,
    ) -> dict[str, Any]:
        async with await _client() as client:
            return await moodle_create_course(
                client,
                _context(role, user_id),
                CreateCourseInput(
                    fullname=fullname,
                    shortname=shortname,
                    categoryid=categoryid,
                    summary=summary,
                    visible=visible,
                ),
            )

    @mcp.tool()
    async def add_url_resource(
        courseid: int,
        section: int,
        name: str,
        externalurl: str,
        intro: str = "",
        role: str = "student",
        user_id: int | None = None,
    ) -> dict[str, Any]:
        async with await _client() as client:
            return await moodle_add_url_resource(
                client,
                _context(role, user_id),
                AddUrlResourceInput(
                    courseid=courseid,
                    section=section,
                    name=name,
                    externalurl=externalurl,
                    intro=intro,
                ),
            )

    @mcp.tool()
    async def add_page_resource(
        courseid: int,
        section: int,
        name: str,
        content: str,
        intro: str = "",
        role: str = "student",
        user_id: int | None = None,
    ) -> dict[str, Any]:
        async with await _client() as client:
            return await moodle_add_page_resource(
                client,
                _context(role, user_id),
                AddPageResourceInput(
                    courseid=courseid,
                    section=section,
                    name=name,
                    content=content,
                    intro=intro,
                ),
            )

    @mcp.tool()
    async def list_my_courses(role: str = "student", user_id: int | None = None) -> list[dict[str, Any]]:
        async with await _client() as client:
            return await moodle_list_my_courses(client, _context(role, user_id))

    @mcp.tool()
    async def get_course_contents(
        courseid: int,
        role: str = "student",
        user_id: int | None = None,
    ) -> list[dict[str, Any]]:
        async with await _client() as client:
            return await moodle_get_course_contents(
                client,
                _context(role, user_id),
                CourseContentsInput(courseid=courseid),
            )

    @mcp.tool()
    async def get_activities_completion_status(
        courseid: int,
        userid: int | None = None,
        role: str = "student",
        user_id: int | None = None,
    ) -> dict[str, Any]:
        async with await _client() as client:
            return await moodle_get_activities_completion_status(
                client,
                _context(role, user_id),
                CompletionStatusInput(courseid=courseid, userid=userid),
            )

    @mcp.tool()
    async def get_users_by_field(
        field: str,
        values: list[str],
        role: str = "student",
        user_id: int | None = None,
    ) -> list[dict[str, Any]]:
        async with await _client() as client:
            return await moodle_get_users_by_field(
                client,
                _context(role, user_id),
                UserLookupInput(field=field, values=values),
            )

    return mcp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Moodle MCP server.")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport to serve. Use stdio for local clients or HTTP transports for a VM.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for HTTP MCP transports.")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP MCP transports.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    server = create_mcp_server(host=args.host, port=args.port)
    server.run(transport=args.transport)


if __name__ == "__main__":
    main()
