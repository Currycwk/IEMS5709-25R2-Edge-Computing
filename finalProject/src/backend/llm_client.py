import json

import httpx


class LLMClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout: float = 20.0,
        api_key: str = "",
        health_path: str = "/models",
        max_tokens: int = 2048,
        enable_thinking: bool | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.api_key = api_key.strip()
        self.health_path = health_path if health_path.startswith("/") else f"/{health_path}"
        self.max_tokens = max_tokens
        self.enable_thinking = enable_thinking

    def _headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _build_payload(self, prompt: str, stream: bool = False) -> dict:
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
            "max_tokens": self.max_tokens,
        }
        if stream:
            payload["stream"] = True
        if self.enable_thinking is not None:
            payload["chat_template_kwargs"] = {"enable_thinking": self.enable_thinking}
        return payload

    def _describe_http_error(self, exc: Exception) -> str:
        if isinstance(exc, httpx.HTTPStatusError):
            response = exc.response
            detail = ""
            try:
                response.read()
            except Exception:
                pass
            try:
                payload = response.json()
                detail = payload.get("error", {}).get("message") or payload.get("detail") or ""
            except Exception:
                try:
                    detail = response.text.strip()
                except Exception:
                    detail = ""
            if detail:
                return f"Qwen 服务请求失败：{detail}"
            return f"Qwen 服务请求失败：HTTP {response.status_code}"
        if isinstance(exc, httpx.HTTPError):
            return f"Qwen 服务请求失败：{exc}"
        return "Qwen 服务请求失败。"

    def health(self) -> bool:
        try:
            response = httpx.get(
                f"{self.base_url}{self.health_path}",
                headers=self._headers(),
                timeout=3.0,
            )
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    def answer(self, prompt: str) -> str:
        payload = self._build_payload(prompt, stream=False)
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except httpx.HTTPError as exc:
            return self._describe_http_error(exc)
        except (KeyError, IndexError, TypeError, ValueError):
            return "Qwen 服务返回了无法解析的响应。"

    def stream_answer(self, prompt: str):
        payload = self._build_payload(prompt, stream=True)

        try:
            truncated = False
            with httpx.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._headers(),
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
                        choice = chunk["choices"][0]
                        delta = choice.get("delta", {}).get("content", "")
                        finish_reason = choice.get("finish_reason")
                    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError):
                        delta = ""
                        finish_reason = None

                    if delta:
                        yield {"type": "token", "token": delta}
                    if finish_reason == "length":
                        truncated = True
            if truncated:
                yield {"type": "warning", "message": "回答可能因输出长度限制被截断。"}
        except httpx.HTTPError as exc:
            yield {"type": "error", "message": self._describe_http_error(exc)}

    def _fallback_answer(self, prompt: str) -> str:
        if not prompt.strip():
            return "我无法从当前知识库中找到足够依据。"
        preview = prompt.strip().replace("\n", " ")[:240]
        return f"当前未连接到 Qwen 服务，以下是基于检索上下文的摘要：{preview}"
