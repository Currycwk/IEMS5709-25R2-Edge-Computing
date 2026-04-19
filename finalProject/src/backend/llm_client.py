import json

import httpx


class LLMClient:
    def __init__(self, base_url: str, model: str, timeout: float = 20.0):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def health(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/models", timeout=3.0)
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    def answer(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个基于本地知识库进行问答的助手。请严格依据上下文回答，不要编造事实。",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 512,
        }
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
            return self._fallback_answer(prompt)

    def stream_answer(self, prompt: str):
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个基于本地知识库进行问答的助手。请严格依据上下文回答，不要编造事实。",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 512,
            "stream": True,
        }

        try:
            with httpx.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=self.timeout,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    if not line.startswith("data:"):
                        continue

                    data = line[len("data:"):].strip()
                    if data == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0].get("delta", {}).get("content", "")
                    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
                        delta = ""

                    if delta:
                        yield delta
        except httpx.HTTPError:
            yield self._fallback_answer(prompt)

    def _fallback_answer(self, prompt: str) -> str:
        if not prompt.strip():
            return "我无法从当前知识库中找到足够依据。"
        preview = prompt.strip().replace("\n", " ")[:240]
        return f"当前未连接到 Qwen3 服务，以下是基于检索上下文的摘要：{preview}"
