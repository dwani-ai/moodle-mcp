from typing import Any

from mcp.server.fastmcp import FastMCP

from moodle_mcp.config import get_settings
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

mcp = FastMCP("moodle-mcp")


def _context(role: str, user_id: int | None = None) -> ToolContext:
    return ToolContext(role=UserRole(role), user_id=user_id)


async def _client() -> MoodleClient:
    settings = get_settings()
    return MoodleClient(
        base_url=str(settings.moodle_base_url),
        token=settings.moodle_token_value,
        rest_format=settings.moodle_rest_format,
    )


@mcp.tool()
async def get_current_user(role: str = "student", user_id: int | None = None) -> dict[str, Any]:
    async with await _client() as client:
        return await moodle_get_current_user(client, _context(role, user_id))


@mcp.tool()
async def list_course_categories(role: str = "student", user_id: int | None = None) -> list[dict[str, Any]]:
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


if __name__ == "__main__":
    mcp.run()
