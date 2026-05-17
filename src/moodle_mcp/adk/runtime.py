from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from uuid import uuid4

if TYPE_CHECKING:
    from moodle_mcp.config import Settings
    from moodle_mcp.tools import UserRole


APP_NAME = "moodle_mcp_education"


@dataclass(frozen=True)
class AdkChatResponse:
    answer: str
    events: list[dict[str, Any]]


class AdkChatRuntime:
    """Runs the Google ADK education orchestrator for FastAPI chat requests."""

    def __init__(self, settings: "Settings | None" = None) -> None:
        from moodle_mcp.config import get_settings

        self.settings = settings or get_settings()
        self._runner: Any | None = None

    def _build_runner(self) -> Any:
        try:
            from google.adk.runners import Runner
            from google.adk.sessions import InMemorySessionService
        except ImportError as exc:
            raise RuntimeError("Install the optional ADK dependency with `pip install .[adk]`.") from exc

        from moodle_mcp.adk import build_education_orchestrator

        agent = build_education_orchestrator(self.settings)
        session_service = InMemorySessionService()
        try:
            return Runner(
                agent=agent,
                app_name=APP_NAME,
                session_service=session_service,
                auto_create_session=True,
            )
        except TypeError:
            return Runner(agent=agent, app_name=APP_NAME, session_service=session_service)

    @property
    def runner(self) -> Any:
        if self._runner is None:
            self._runner = self._build_runner()
        return self._runner

    async def chat(
        self,
        *,
        role: "UserRole",
        message: str,
        user_id: int | None = None,
    ) -> AdkChatResponse:
        try:
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("Install the optional ADK dependency with `pip install .[adk]`.") from exc

        from moodle_mcp.adk.moodle_tools import MoodleToolContext, bind_moodle_tool_context

        session_user_id = str(user_id or "anonymous")
        session_id = f"{role.value}-{session_user_id}"
        content = types.Content(
            role="user",
            parts=[
                types.Part(
                    text=(
                        f"Moodle role: {role.value}\n"
                        f"Moodle user_id: {user_id if user_id is not None else 'not provided'}\n\n"
                        f"{message}"
                    )
                )
            ],
        )
        final_answer = ""
        event_summaries: list[dict[str, Any]] = []
        await self._ensure_session(user_id=session_user_id, session_id=session_id)
        with bind_moodle_tool_context(
            MoodleToolContext(settings=self.settings, role=role, user_id=user_id)
        ):
            async for event in self.runner.run_async(
                user_id=session_user_id,
                session_id=session_id,
                invocation_id=str(uuid4()),
                new_message=content,
            ):
                event_text = self._event_text(event)
                event_summaries.append(
                    {
                        "author": getattr(event, "author", None),
                        "text": event_text,
                        "final": self._is_final_response(event),
                    }
                )
                if event_text and (self._is_final_response(event) or not final_answer):
                    final_answer = event_text

        return AdkChatResponse(
            answer=final_answer or "The ADK agent finished without a text response.",
            events=event_summaries,
        )

    async def _ensure_session(self, *, user_id: str, session_id: str) -> None:
        session_service = getattr(self.runner, "session_service", None)
        if session_service is None:
            return
        get_session = getattr(session_service, "get_session", None)
        create_session = getattr(session_service, "create_session", None)
        if not callable(get_session) or not callable(create_session):
            return
        session = await get_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)
        if not session:
            await create_session(app_name=APP_NAME, user_id=user_id, session_id=session_id)

    def _is_final_response(self, event: Any) -> bool:
        is_final = getattr(event, "is_final_response", None)
        return bool(is_final()) if callable(is_final) else False

    def _event_text(self, event: Any) -> str:
        content = getattr(event, "content", None)
        parts = getattr(content, "parts", None) or []
        text_parts = [getattr(part, "text", "") for part in parts]
        return "\n".join(part for part in text_parts if part)
