import pytest

from moodle_mcp.tools import (
    AddPageResourceInput,
    CreateCourseInput,
    ToolContext,
    UserRole,
    UserLookupInput,
    moodle_add_page_resource,
    moodle_create_course,
    moodle_get_users_by_field,
    moodle_list_my_courses,
)


class FakeMoodleClient:
    async def create_course(self, **payload):
        return type("Course", (), {"model_dump": lambda self: {"id": 42, **payload}})()

    async def add_page_resource(self, **payload):
        return {"id": 99, **payload}

    async def get_site_info(self):
        return type("User", (), {"userid": 7})()

    async def get_user_courses(self, userid):
        return [
            type(
                "Course",
                (),
                {"model_dump": lambda self: {"id": 10, "fullname": "Intro", "userid": userid}},
            )()
        ]

    async def get_users_by_field(self, **payload):
        return [
            type(
                "User",
                (),
                {"model_dump": lambda self: {"id": 7, "username": payload["values"][0]}},
            )()
        ]


@pytest.mark.asyncio
async def test_student_cannot_create_course():
    with pytest.raises(PermissionError):
        await moodle_create_course(
            FakeMoodleClient(),
            ToolContext(role=UserRole.STUDENT),
            CreateCourseInput(fullname="Physics 101", shortname="PHY101", categoryid=1),
        )


@pytest.mark.asyncio
async def test_creator_can_create_course():
    result = await moodle_create_course(
        FakeMoodleClient(),
        ToolContext(role=UserRole.CREATOR),
        CreateCourseInput(fullname="Physics 101", shortname="PHY101", categoryid=1),
    )

    assert result["id"] == 42
    assert result["fullname"] == "Physics 101"


@pytest.mark.asyncio
async def test_student_courses_default_to_moodle_user():
    result = await moodle_list_my_courses(FakeMoodleClient(), ToolContext(role=UserRole.STUDENT))

    assert result == [{"id": 10, "fullname": "Intro", "userid": 7}]


@pytest.mark.asyncio
async def test_creator_can_add_page_resource():
    result = await moodle_add_page_resource(
        FakeMoodleClient(),
        ToolContext(role=UserRole.CREATOR),
        AddPageResourceInput(courseid=1, section=0, name="Overview", content="Welcome"),
    )

    assert result["id"] == 99
    assert result["content"] == "Welcome"


@pytest.mark.asyncio
async def test_student_cannot_lookup_users():
    with pytest.raises(PermissionError):
        await moodle_get_users_by_field(
            FakeMoodleClient(),
            ToolContext(role=UserRole.STUDENT),
            UserLookupInput(field="username", values=["student1"]),
        )
