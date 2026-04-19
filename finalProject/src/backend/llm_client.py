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

    def answer(self, question: str, context: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个基于本地知识库进行问答的助手。请严格依据上下文回答，不要编造事实。",
                },
                {
                    "role": "user",
                    "content": f"上下文：\n{context}\n\n问题：{question}",
                },
            ],
            "temperature": 0.2,
            "max_tokens": 300,
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
            return self._fallback_answer(question, context)

    def _fallback_answer(self, question: str, context: str) -> str:
        if not context.strip():
            return "我无法从当前知识库中找到足够依据。"
        preview = context.strip().replace("\n", " ")[:240]
        return f"当前未连接到 Qwen3 服务，以下是与问题“{question}”最相关的知识库内容摘要：{preview}"
