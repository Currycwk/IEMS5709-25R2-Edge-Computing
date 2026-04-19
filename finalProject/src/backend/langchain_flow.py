from __future__ import annotations

try:
    from langchain_core.prompts import ChatPromptTemplate

    LANGCHAIN_CORE_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency
    ChatPromptTemplate = None
    LANGCHAIN_CORE_AVAILABLE = False


SYSTEM_PROMPT = (
    "你是一个基于本地知识库进行问答的助手。"
    "请严格依据提供的上下文回答用户问题。"
    "如果上下文中没有足够信息，请明确说明“我无法从当前知识库中找到足够依据”。"
    "不要编造事实。"
)


class PromptOrchestrator:
    def __init__(self):
        self.backend = "langchain-core" if LANGCHAIN_CORE_AVAILABLE else "native"
        self._template = None

        if LANGCHAIN_CORE_AVAILABLE:
            self._template = ChatPromptTemplate.from_messages(
                [
                    ("system", SYSTEM_PROMPT),
                    ("human", "上下文：\n{context}\n\n问题：\n{question}"),
                ]
            )

    def render(self, context: str, question: str) -> str:
        if self._template is not None:
            messages = self._template.format_messages(context=context, question=question)
            # For OpenAI-compatible chat API, pass a compact single prompt string.
            return "\n\n".join(message.content for message in messages)

        return (
            f"{SYSTEM_PROMPT}\n\n"
            f"上下文：\n{context}\n\n"
            f"问题：\n{question}"
        )
