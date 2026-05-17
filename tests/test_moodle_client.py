import httpx
import pytest

from moodle_mcp.moodle import MoodleClient, MoodleError


@pytest.mark.asyncio
async def test_get_site_info_posts_to_moodle_rest_endpoint():
    async def handler(request: httpx.Request) -> httpx.Response:
        body = request.content.decode()
        assert "wsfunction=core_webservice_get_site_info" in body
        assert request.url.path == "/webservice/rest/server.php"
        return httpx.Response(200, json={"userid": 1, "username": "admin"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = MoodleClient(base_url="https://moodle.example", token="token", client=http_client)
        user = await client.get_site_info()

    assert user.userid == 1
    assert user.username == "admin"


@pytest.mark.asyncio
async def test_moodle_exception_payload_raises_error():
    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "exception": "moodle_exception",
                "errorcode": "invalidtoken",
                "message": "Invalid token",
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = MoodleClient(base_url="https://moodle.example", token="bad", client=http_client)
        with pytest.raises(MoodleError, match="Invalid token"):
            await client.get_site_info()


@pytest.mark.asyncio
async def test_get_users_by_field_posts_indexed_values():
    async def handler(request: httpx.Request) -> httpx.Response:
        body = request.content.decode()
        assert "wsfunction=core_user_get_users_by_field" in body
        assert "field=username" in body
        assert "values%5B0%5D=teacher1" in body
        return httpx.Response(200, json=[{"id": 3, "userid": 3, "username": "teacher1"}])

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = MoodleClient(base_url="https://moodle.example", token="token", client=http_client)
        users = await client.get_users_by_field(field="username", values=["teacher1"])

    assert users[0].username == "teacher1"


@pytest.mark.asyncio
async def test_add_page_resource_posts_page_payload():
    async def handler(request: httpx.Request) -> httpx.Response:
        body = request.content.decode()
        assert "wsfunction=mod_page_add_instance" in body
        assert "content=Welcome" in body
        return httpx.Response(200, json={"id": 9})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = MoodleClient(base_url="https://moodle.example", token="token", client=http_client)
        result = await client.add_page_resource(
            courseid=1,
            section=0,
            name="Overview",
            content="Welcome",
        )

    assert result["id"] == 9
