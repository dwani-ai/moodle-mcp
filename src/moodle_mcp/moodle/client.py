from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict


class MoodleError(RuntimeError):
    """Raised when Moodle returns a transport or Web Services error."""


class MoodleUser(BaseModel):
    model_config = ConfigDict(extra="allow")

    userid: int
    id: int | None = None
    username: str | None = None
    fullname: str | None = None
    email: str | None = None
    siteurl: str | None = None


class CourseCategory(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    name: str
    parent: int | None = None


class CourseSummary(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int
    fullname: str | None = None
    shortname: str | None = None
    summary: str | None = None


class MoodleClient:
    """Small async wrapper around Moodle's REST Web Services endpoint."""

    def __init__(
        self,
        *,
        base_url: str,
        token: str,
        rest_format: str = "json",
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.rest_format = rest_format
        self._client = client
        self._owns_client = client is None

    async def __aenter__(self) -> "MoodleClient":
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30)
        return self

    async def __aexit__(self, *_: object) -> None:
        if self._owns_client and self._client is not None:
            await self._client.aclose()
        self._client = None

    async def call(self, function: str, **params: Any) -> Any:
        client = self._client or httpx.AsyncClient(timeout=30)
        close_client = self._client is None
        payload = {
            "wstoken": self.token,
            "wsfunction": function,
            "moodlewsrestformat": self.rest_format,
            **params,
        }
        try:
            response = await client.post(f"{self.base_url}/webservice/rest/server.php", data=payload)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as exc:
            raise MoodleError(f"Moodle request failed for {function}: {exc}") from exc
        finally:
            if close_client:
                await client.aclose()

        if isinstance(data, dict) and data.get("exception"):
            message = data.get("message") or data.get("errorcode") or "unknown Moodle error"
            raise MoodleError(f"Moodle Web Services error for {function}: {message}")
        return data

    async def get_site_info(self) -> MoodleUser:
        data = await self.call("core_webservice_get_site_info")
        return MoodleUser.model_validate(data)

    async def get_users_by_field(self, *, field: str, values: list[str]) -> list[MoodleUser]:
        payload = {"field": field}
        payload.update({f"values[{index}]": value for index, value in enumerate(values)})
        data = await self.call("core_user_get_users_by_field", **payload)
        return [MoodleUser.model_validate(item) for item in data]

    async def get_course_categories(self) -> list[CourseCategory]:
        data = await self.call("core_course_get_categories")
        return [CourseCategory.model_validate(item) for item in data]

    async def create_course(
        self,
        *,
        fullname: str,
        shortname: str,
        categoryid: int,
        summary: str = "",
        visible: bool = True,
    ) -> CourseSummary:
        data = await self.call(
            "core_course_create_courses",
            **{
                "courses[0][fullname]": fullname,
                "courses[0][shortname]": shortname,
                "courses[0][categoryid]": categoryid,
                "courses[0][summary]": summary,
                "courses[0][visible]": 1 if visible else 0,
            },
        )
        if not data:
            raise MoodleError("Moodle did not return the created course.")
        return CourseSummary.model_validate(data[0])

    async def add_url_resource(
        self,
        *,
        courseid: int,
        section: int,
        name: str,
        externalurl: str,
        intro: str = "",
    ) -> dict[str, Any]:
        return await self.call(
            "mod_url_add_instance",
            course=courseid,
            section=section,
            name=name,
            externalurl=externalurl,
            intro=intro,
            introformat=1,
        )

    async def add_page_resource(
        self,
        *,
        courseid: int,
        section: int,
        name: str,
        content: str,
        intro: str = "",
    ) -> dict[str, Any]:
        return await self.call(
            "mod_page_add_instance",
            course=courseid,
            section=section,
            name=name,
            intro=intro,
            introformat=1,
            content=content,
            contentformat=1,
        )

    async def get_user_courses(self, userid: int) -> list[CourseSummary]:
        data = await self.call("core_enrol_get_users_courses", userid=userid)
        return [CourseSummary.model_validate(item) for item in data]

    async def get_course_contents(self, courseid: int) -> list[dict[str, Any]]:
        data = await self.call("core_course_get_contents", courseid=courseid)
        if not isinstance(data, list):
            raise MoodleError("Unexpected course content response from Moodle.")
        return data

    async def get_activities_completion_status(self, *, courseid: int, userid: int) -> dict[str, Any]:
        data = await self.call(
            "core_completion_get_activities_completion_status",
            courseid=courseid,
            userid=userid,
        )
        if not isinstance(data, dict):
            raise MoodleError("Unexpected completion status response from Moodle.")
        return data
