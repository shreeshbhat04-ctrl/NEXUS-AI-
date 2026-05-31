from sqlalchemy.orm import Session

from nexus_ai.adapters.ticketing import RoutineTask
from nexus_ai.adapters.notifications import MockNotificationAdapter
from nexus_ai.services.brain import BrainCondition, BrainPatientProfile
from nexus_ai.services.model_routing import ModelRoutingService
from nexus_ai.db.models import Notification


class CommunicationsAgent:
    def __init__(self, notification_adapter: MockNotificationAdapter | None = None) -> None:
        self.notification_adapter = notification_adapter or MockNotificationAdapter()
        self.model_routing = ModelRoutingService()

    def notify(self, db: Session, patient_id: int, channel: str, message_type: str, message_body: str) -> Notification:
        result = self.notification_adapter.send(channel=channel, message_body=message_body)
        notification = Notification(
            patient_id=patient_id,
            channel=result.channel,
            message_type=message_type,
            body=message_body,
            delivery_status=result.delivery_status,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    def compose_daily_checkin(
        self,
        profile: BrainPatientProfile | None,
        conditions: list[BrainCondition],
        routine_tasks: list[RoutineTask],
    ) -> str:
        patient_name = profile.full_name if profile is not None else "there"
        condition_summary = ", ".join(condition.name for condition in conditions[:3]) if conditions else "your current care plan"
        pending_tasks = [task.name for task in routine_tasks if not task.completed][:3]
        task_summary = "; ".join(pending_tasks) if pending_tasks else "no pending routine tasks today"
        return (
            f"Hi {patient_name}, just checking in on your day. "
            f"I'm keeping an eye on {condition_summary}. "
            f"Today's routine focus is: {task_summary}. "
            "Let me know how you're feeling and whether you took your medicines."
        )

    def build_conversation_plan(self, message: str, profile: BrainPatientProfile | None = None) -> dict[str, object]:
        route = self.model_routing.route_general_conversation(message)
        
        # Actually generate the response using Gemini
        try:
            from nexus_ai.config import get_settings
            settings = get_settings()
            system_instruction = (
                "You are an empathetic, calm, and highly capable medical assistant named nexus_ai Copilot. "
                "Keep responses concise, conversational, and friendly (1-2 short sentences max). "
            )
            if profile:
                system_instruction += f"\nThe patient's name is {profile.full_name}. Summary: {profile.summary}"

            generated_message = self._generate_gemini_text(message=message, system_instruction=system_instruction)
        except Exception as e:
            generated_message = f"I'm here for you! I heard: {message} (But my generative engine hit an error: {e})"

        return {
            "message": generated_message,
            "route_type": route["route_type"],
            "primary_model": route["primary_model"],
            "support_model": route["support_model"],
            "reason": route["reason"],
            "suggested_response_style": "calm, reassuring, and patient-friendly",
            "execution_plan": route["execution_plan"],
        }

    def _generate_gemini_text(self, message: str, system_instruction: str) -> str:
        from google import genai
        from nexus_ai.config import get_settings

        settings = get_settings()
        client = genai.Client(api_key=settings.google_api_key)
        last_error: Exception | None = None

        for model_id in settings.gemini_fast_model_candidates:
            try:
                response = client.models.generate_content(
                    model=model_id,
                    contents=message,
                    config=genai.types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.7,
                    ),
                )
                return (response.text or "").strip()
            except Exception as error:
                last_error = error

        raise last_error or RuntimeError("Gemini generation failed.")

    @staticmethod
    def _extract_generated_text(result: object) -> str:
        if isinstance(result, dict) and isinstance(result.get("text"), str):
            return result["text"].strip()
        if isinstance(result, list):
            return str(result)
        if isinstance(result, dict):
            return str(result)
        return "" if result is None else str(result)
