"""Grok (xAI) chat client — OpenAI-compatible API."""
import httpx
from config import XAI_API_KEY, GROK_MODEL, XAI_BASE_URL


async def grok_chat(messages: list[dict], temperature: float = 0.5) -> str:
    """messages = [{role: system|user|assistant, content: str}, ...]"""
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            XAI_BASE_URL,
            headers={
                "Authorization": f"Bearer {XAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": GROK_MODEL,
                "messages": messages,
                "temperature": temperature,
                "stream": False,
            },
        )
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"]
