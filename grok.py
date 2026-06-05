"""Grok (xAI) chat client — OpenAI-compatible API."""
import httpx
from config import XAI_API_KEY, XAI_BASE_URL


async def grok_chat(system_prompt: str, conversation: list[dict], model: str, temperature: float = 0.5) -> str:
    """conversation = [{role: user|assistant, content}, ...]"""
    messages = [{"role": "system", "content": system_prompt}] + [
        {"role": ("assistant" if m["role"] == "assistant" else "user"), "content": m["content"]}
        for m in conversation
    ]
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            XAI_BASE_URL,
            headers={"Authorization": f"Bearer {XAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": model, "messages": messages, "temperature": temperature, "stream": False},
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
