import pytest

from moodle_mcp.tools import (
    CreateCourseInput,
    ToolContext,
    UserRole,
    moodle_create_course,
    moodle_list_my_courses,
)


class FakeMoodleClient:
    async def create_course(self, **payload):
        return type("Course", (), {"model_dump": lambda self: {"id": 42, **payload}})()

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
