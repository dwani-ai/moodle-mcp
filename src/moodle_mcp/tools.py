from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl

from moodle_mcp.moodle import MoodleClient


class UserRole(StrEnum):
    CREATOR = "creator"
    STUDENT = "student"


class ToolContext(BaseModel):
    role: UserRole
    user_id: int | None = None


class CreateCourseInput(BaseModel):
    fullname: str = Field(min_length=3)
    shortname: str = Field(min_length=2)
    categoryid: int = Field(gt=0)
    summary: str = ""
    visible: bool = True


class AddUrlResourceInput(BaseModel):
    courseid: int = Field(gt=0)
    section: int = Field(ge=0)
    name: str = Field(min_length=2)
    externalurl: HttpUrl
    intro: str = ""


class AddPageResourceInput(BaseModel):
    courseid: int = Field(gt=0)
    section: int = Field(ge=0)
    name: str = Field(min_length=2)
    content: str = Field(min_length=1)
    intro: str = ""


class CourseContentsInput(BaseModel):
    courseid: int = Field(gt=0)


class CompletionStatusInput(BaseModel):
    courseid: int = Field(gt=0)
    userid: int | None = Field(default=None, gt=0)


class UserLookupInput(BaseModel):
    field: str = Field(pattern="^(id|username|email)$")
    values: list[str] = Field(min_length=1, max_length=25)


def require_creator(context: ToolContext) -> None:
    if context.role != UserRole.CREATOR:
        raise PermissionError("Only Moodle creator users can perform this action.")


async def moodle_get_current_user(client: MoodleClient, _: ToolContext) -> dict[str, Any]:
    user = await client.get_site_info()
    return user.model_dump()


async def moodle_list_course_categories(client: MoodleClient, _: ToolContext) -> list[dict[str, Any]]:
    categories = await client.get_course_categories()
    return [category.model_dump() for category in categories]


async def moodle_create_course(
    client: MoodleClient,
    context: ToolContext,
    payload: CreateCourseInput,
) -> dict[str, Any]:
    require_creator(context)
    course = await client.create_course(**payload.model_dump())
    return course.model_dump()


async def moodle_add_url_resource(
    client: MoodleClient,
    context: ToolContext,
    payload: AddUrlResourceInput,
) -> dict[str, Any]:
    require_creator(context)
    return await client.add_url_resource(**payload.model_dump(mode="json"))


async def moodle_add_page_resource(
    client: MoodleClient,
    context: ToolContext,
    payload: AddPageResourceInput,
) -> dict[str, Any]:
    require_creator(context)
    return await client.add_page_resource(**payload.model_dump(mode="json"))


async def moodle_list_my_courses(client: MoodleClient, context: ToolContext) -> list[dict[str, Any]]:
    user = await client.get_site_info()
    userid = context.user_id or user.userid
    courses = await client.get_user_courses(userid)
    return [course.model_dump() for course in courses]


async def moodle_get_course_contents(
    client: MoodleClient,
    _: ToolContext,
    payload: CourseContentsInput,
) -> list[dict[str, Any]]:
    return await client.get_course_contents(payload.courseid)


async def moodle_get_activities_completion_status(
    client: MoodleClient,
    context: ToolContext,
    payload: CompletionStatusInput,
) -> dict[str, Any]:
    user = await client.get_site_info()
    userid = payload.userid or context.user_id or user.userid
    return await client.get_activities_completion_status(courseid=payload.courseid, userid=userid)


async def moodle_get_users_by_field(
    client: MoodleClient,
    context: ToolContext,
    payload: UserLookupInput,
) -> list[dict[str, Any]]:
    require_creator(context)
    users = await client.get_users_by_field(field=payload.field, values=payload.values)
    return [user.model_dump() for user in users]
