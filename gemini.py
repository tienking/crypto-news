"""Gemini (Google) chat client."""
from google import genai
from google.genai import types
from config import GEMINI_API_KEY

_client = None

def _get_client():
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError("GEMINI_API_KEY is not set")
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


async def gemini_chat(system_prompt: str, conversation: list[dict], model: str, temperature: float = 0.5) -> str:
    """conversation = [{role: user|assistant, content}, ...]"""
    contents = [
        types.Content(
            role=("model" if m["role"] == "assistant" else "user"),
            parts=[types.Part(text=m["content"])],
        )
        for m in conversation
    ]
    resp = _get_client().models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(system_instruction=system_prompt, temperature=temperature),
    )
    return resp.text
