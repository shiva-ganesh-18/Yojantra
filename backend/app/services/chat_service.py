"""AI Chat service using LLM for conversational scheme assistance."""
import json
import os
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import User, Business, Scheme, Conversation
from app.schemas import ChatMessageRequest, ChatMessageResponse


SYSTEM_PROMPT = """You are SchemeMatch AI, an empathetic assistant for marginalized entrepreneurs in India.
Your job is to help users find and apply for government schemes.

RULES:
1. Before recommending schemes, you MUST have: gender, social category, state, district, business type, business stage, annual turnover, employees, funding need.
2. If missing info, ask ONE question at a time. Be conversational and warm.
3. Explain schemes in simple language. No jargon. Use analogies if helpful.
4. Always cite official sources. Never hallucinate scheme details.
5. Warn about fraud: "No government scheme requires a bribe."
6. Support Hindi, English, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Odia, Assamese.
7. For voice users: use short sentences, pause between sections.
8. If unsure, say "I don't have the latest info. Please verify on the official portal."
9. Never ask for OTP, PIN, or passwords.
10. Be empowering and respectful. Every entrepreneur deserves dignity.

OUTPUT FORMAT for scheme recommendations:
🎯 SCHEME: [Name]
📋 CATEGORY: [Target]
💰 BENEFIT: [Details]
✅ WHY YOU MATCH:
   • [Reason 1]
   • [Reason 2]
📄 DOCUMENTS: [List]
📝 STEPS: [Numbered]
⏱️ TIMELINE: [Days]
🔗 OFFICIAL: [URL]
📞 HELPLINE: [Number]

Current user profile (if available):
{profile}
"""


class ChatService:
    """Handles AI-powered conversations for scheme discovery."""

    def __init__(self, db: Session):
        self.db = db
        self._init_llm()

    def _init_llm(self):
        """Initialize LLM client."""
        try:
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,
                api_key=os.getenv("OPENAI_API_KEY", "")
            )
        except Exception:
            # Fallback: simple rule-based responses
            self.llm = None

    def process_message(
        self, user_id: Optional[UUID], request: ChatMessageRequest
    ) -> ChatMessageResponse:
        """Process a chat message and return AI response."""

        # Get user profile if available
        profile_text = "No profile yet."
        if user_id:
            user = self.db.query(User).filter(User.id == user_id).first()
            business = self.db.query(Business).filter(Business.user_id == user_id).first()
            if user:
                profile_text = self._format_profile(user, business)

        # Build conversation context
        messages = self._build_messages(user_id, request, profile_text)

        # Get LLM response or fallback
        source = "ai"
        if self.llm:
            try:
                response_text = self._get_llm_response(messages)
                intent = self._detect_intent(request.message)
            except Exception:
                response_text = self._fallback_response(request.message, user_id)
                intent = "general_query"
                source = "rule_based_fallback"
        else:
            response_text = self._fallback_response(request.message, user_id)
            intent = "general_query"
            source = "rule_based_fallback"

        # Extract mentioned schemes
        schemes_mentioned = self._extract_scheme_mentions(response_text)

        # Save conversation
        session_id = request.session_id or self._generate_session_id()
        self._save_conversation(user_id, session_id, request, response_text, intent, schemes_mentioned)

        return ChatMessageResponse(
            reply=response_text,
            intent=intent,
            schemes_mentioned=schemes_mentioned,
            actions=self._suggest_actions(intent, user_id),
            session_id=session_id,
            source=source
        )

    def _format_profile(self, user: User, business: Optional[Business]) -> str:
        """Format user profile for LLM context."""
        parts = [
            f"Name: {user.full_name}",
            f"Gender: {user.gender or 'Not specified'}",
            f"Category: {user.social_category or 'Not specified'}",
            f"Location: {user.district}, {user.state}",
            f"Rural: {user.is_rural}",
        ]
        if business:
            parts.extend([
                f"Business: {business.business_name or 'Not named'} ({business.business_type or 'Not specified'})",
                f"Stage: {business.business_stage or 'Not specified'}",
                f"Turnover: ₹{business.annual_turnover_inr or 'Not specified'}",
                f"Employees: {business.num_employees}",
                f"Funding Need: ₹{business.funding_needed_inr or 'Not specified'}",
            ])
        return "\n".join(parts)

    def _build_messages(
        self, user_id: Optional[UUID], request: ChatMessageRequest, profile_text: str
    ) -> List[Dict[str, str]]:
        """Build message history for LLM."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(profile=profile_text)},
        ]

        # Add recent conversation history
        if user_id:
            recent = self.db.query(Conversation).filter(
                Conversation.user_id == user_id
            ).order_by(Conversation.created_at.desc()).limit(5).all()
            for conv in reversed(recent):
                if conv.messages:
                    for msg in conv.messages[-4:]:  # Last 4 messages per session
                        messages.append(msg)

        messages.append({"role": "user", "content": request.message})
        return messages

    def _get_llm_response(self, messages: List[Dict[str, str]]) -> str:
        """Call LLM API."""
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

        lc_messages = []
        for msg in messages:
            if msg["role"] == "system":
                lc_messages.append(SystemMessage(content=msg["content"]))
            elif msg["role"] == "user":
                lc_messages.append(HumanMessage(content=msg["content"]))
            else:
                lc_messages.append(AIMessage(content=msg["content"]))

        response = self.llm.invoke(lc_messages)
        return response.content

    def _fallback_response(self, message: str, user_id: Optional[UUID]) -> str:
        """Rule-based fallback when LLM is unavailable."""
        msg_lower = message.lower()

        greetings = ["hello", "hi", "namaste", "vanakkam", "namaskar"]
        if any(g in msg_lower for g in greetings):
            return "Namaste! I am SchemeMatch AI. I can help you find government schemes for your business. To get started, may I know your name and which state you are from?"

        if "scheme" in msg_lower or "yojana" in msg_lower or "loan" in msg_lower:
            return "I'd love to help you find the right scheme! To match you accurately, I need to know:\n1. Your gender and social category (SC/ST/OBC/General)\n2. Your state and district\n3. Your business type (manufacturing/service/trading/etc.)\n4. Your annual turnover\n5. How much funding you need\n\nYou can share these one by one."

        if "document" in msg_lower or "paper" in msg_lower:
            return "Common documents needed for most schemes:\n• PAN Card\n• Aadhaar Card\n• Bank Passbook\n• UDYAM Registration (for MSME schemes)\n• GST Registration (if applicable)\n• Business address proof\n\nSpecific schemes may need additional documents. Which scheme are you applying for?"

        if "status" in msg_lower or "application" in msg_lower:
            return "You can track your applications in the 'My Applications' section of the app. Would you like me to help you check a specific application?"

        if "help" in msg_lower or "support" in msg_lower:
            return "I can help you with:\n• Finding eligible schemes\n• Understanding application steps\n• Document requirements\n• Tracking applications\n• Connecting to nearest CSC center\n\nWhat would you like help with?"

        return "Thank you for your message. I'm here to help you find government schemes for your business. Could you tell me more about what you're looking for? For example, are you looking for a loan, grant, or subsidy?"

    def _detect_intent(self, message: str) -> str:
        """Simple intent detection."""
        msg_lower = message.lower()
        if any(w in msg_lower for w in ["scheme", "yojana", "loan", "grant", "subsidy"]):
            return "find_scheme"
        if any(w in msg_lower for w in ["apply", "application", "form"]):
            return "apply_scheme"
        if any(w in msg_lower for w in ["status", "track", "where"]):
            return "check_status"
        if any(w in msg_lower for w in ["document", "paper", "certificate"]):
            return "upload_doc"
        if any(w in msg_lower for w in ["help", "support", "agent", "human"]):
            return "escalate"
        return "general_query"

    def _extract_scheme_mentions(self, response: str) -> List[UUID]:
        """Extract scheme IDs mentioned in response."""
        # Simplified: would use NER or keyword matching against scheme DB
        return []

    def _suggest_actions(self, intent: str, user_id: Optional[UUID]) -> List[Dict[str, Any]]:
        """Suggest next actions based on intent."""
        actions = []
        if intent == "find_scheme":
            actions.append({"type": "button", "label": "View My Matches", "action": "navigate_matches"})
        elif intent == "apply_scheme":
            actions.append({"type": "button", "label": "Start Application", "action": "navigate_applications"})
        elif intent == "check_status":
            actions.append({"type": "button", "label": "My Applications", "action": "navigate_applications"})
        elif intent == "escalate":
            actions.append({"type": "button", "label": "Call Helpline", "action": "call_helpline"})
        return actions

    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        import uuid
        return str(uuid.uuid4())

    def _save_conversation(
        self, user_id: Optional[UUID], session_id: str,
        request: ChatMessageRequest, response: str, intent: str,
        schemes_mentioned: List[UUID]
    ):
        """Save conversation to database."""
        messages = [
            {"role": "user", "content": request.message, "timestamp": str(__import__("datetime").datetime.now())},
            {"role": "assistant", "content": response, "timestamp": str(__import__("datetime").datetime.now())}
        ]

        conv = Conversation(
            user_id=user_id,
            session_id=session_id,
            channel=request.channel,
            language=request.language,
            messages=messages,
            intent_detected=intent,
            schemes_discussed=schemes_mentioned
        )
        self.db.add(conv)
        self.db.commit()


def get_chat_service(db: Session) -> ChatService:
    return ChatService(db)
