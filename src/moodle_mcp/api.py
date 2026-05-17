import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from moodle_mcp.adk.runtime import AdkChatRuntime
from moodle_mcp.agent import ChatResult, MoodleAgent
from moodle_mcp.config import get_settings
from moodle_mcp.mcp_client import mcp_client_session
from moodle_mcp.moodle import MoodleClient, MoodleError
from moodle_mcp.tools import UserRole

settings = get_settings()
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


@app.get("/", include_in_schema=False)
async def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/healthz")
async def healthz() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/readyz")
async def readyz() -> HealthResponse:
    try:
        if settings.mcp_server_url:
            async with mcp_client_session(
                str(settings.mcp_server_url),
                settings.mcp_client_transport,
            ) as session:
                await session.call_tool("get_current_user", {"role": "student"})
        else:
            async with MoodleClient(
                base_url=str(settings.moodle_base_url),
                token=settings.moodle_token_value,
                rest_format=settings.moodle_rest_format,
            ) as client:
                await client.get_site_info()
    except (MoodleError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return HealthResponse(status="ready")


@app.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResult:
    try:
        if settings.agent_runtime == "adk":
            if adk_runtime is None:
                raise RuntimeError("ADK runtime is not initialized.")
            result = await adk_runtime.chat(
                role=request.role,
                message=request.message,
                user_id=request.user_id,
            )
            return ChatResult(role=request.role, answer=result.answer, tool_results=result.events)

        agent = MoodleAgent(settings)
        return await agent.chat(
            role=request.role,
            message=request.message,
            user_id=request.user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (MoodleError, RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
