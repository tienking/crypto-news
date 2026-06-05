"""Chat provider dispatcher — routes to Grok or Gemini per the active AI settings."""
from database import get_ai_settings
from grok import grok_chat
from gemini import gemini_chat


async def ai_chat(system_prompt: str, conversation: list[dict]) -> tuple[str, str]:
    """Returns (reply, provider)."""
    s = await get_ai_settings()
    provider = s.get("provider", "grok")
    if provider == "gemini":
        reply = await gemini_chat(system_prompt, conversation, s.get("gemini_model", "gemini-2.5-flash"))
    else:
        provider = "grok"
        reply = await grok_chat(system_prompt, conversation, s.get("grok_model", "grok-3"))
    return reply, provider
