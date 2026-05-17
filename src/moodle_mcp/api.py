import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from moodle_mcp.adk.runtime import AdkChatRuntime
from moodle_mcp.agent import ChatResult, MoodleAgent
from moodle_mcp.config import Settings, get_settings
from moodle_mcp.mcp_client import mcp_client_session, serialize_mcp_result
from moodle_mcp.tools import UserRole

settings = get_settings()
settings.validate_runtime()
app = FastAPI(title="Moodle MCP Agent", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

WEB_DIR = Path(os.getenv("WEB_DIR", Path(__file__).resolve().parents[2] / "web"))
if not WEB_DIR.exists() and Path("/app/web").exists():
    WEB_DIR = Path("/app/web")
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")

adk_runtime = AdkChatRuntime(settings) if settings.agent_runtime == "adk" else None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    role: UserRole
    user_id: int | None = None


class HealthResponse(BaseModel):
    status: str


async def resolve_chat_context(
    app_settings: Settings,
    requested_role: UserRole,
    requested_user_id: int | None,
) -> tuple[UserRole, int | None]:
    if not app_settings.mcp_server_url:
        raise RuntimeError("MCP_SERVER_URL is required for chat context resolution.")

    async with mcp_client_session(
        str(app_settings.mcp_server_url),
        app_settings.mcp_client_transport,
    ) as session:
        result = await session.call_tool("get_current_user", {"role": "student"})

    current_user = extract_mcp_mapping(serialize_mcp_result(result))
    effective_user_id = int(current_user["userid"])
    if app_settings.allow_user_id_override and requested_user_id is not None:
        effective_user_id = requested_user_id

    effective_role = (
        UserRole.CREATOR if effective_user_id in app_settings.creator_user_ids else UserRole.STUDENT
    )

    if app_settings.app_env == "local" and app_settings.allow_user_id_override:
        effective_role = requested_role

    return effective_role, effective_user_id


def extract_mcp_mapping(result: object) -> dict[str, object]:
    if isinstance(result, dict):
        if "userid" in result:
            return result
        structured = result.get("structuredContent")
        if isinstance(structured, dict):
            return structured
        content = result.get("content")
        if isinstance(content, list) and content:
            first = content[0]
            if isinstance(first, dict):
                if isinstance(first.get("text"), str):
                    import json

                    decoded = json.loads(first["text"])
                    if isinstance(decoded, dict):
                        return decoded
                if isinstance(first.get("data"), dict):
                    return first["data"]
    raise RuntimeError("MCP tool did not return a user mapping.")


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/healthz")
async def healthz() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/readyz")
async def readyz() -> HealthResponse:
    try:
        async with mcp_client_session(
            str(settings.mcp_server_url),
            settings.mcp_client_transport,
        ) as session:
            await session.call_tool("get_current_user", {"role": "student"})
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return HealthResponse(status="ready")


@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResult:
    try:
        effective_role, effective_user_id = await resolve_chat_context(
            settings,
            request.role,
            request.user_id,
        )
        if settings.agent_runtime == "adk":
            if adk_runtime is None:
                raise RuntimeError("ADK runtime is not initialized.")
            result = await adk_runtime.chat(
                role=effective_role,
                message=request.message,
                user_id=effective_user_id,
            )
            return ChatResult(role=effective_role, answer=result.answer, tool_results=result.events)

        agent = MoodleAgent(settings)
        return await agent.chat(
            role=effective_role,
            message=request.message,
            user_id=effective_user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
