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
