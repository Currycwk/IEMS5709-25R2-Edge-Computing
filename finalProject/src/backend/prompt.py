def build_prompt(context: str, question: str) -> str:
    return (
        "你是一个基于本地知识库进行问答的助手。\n"
        "请严格依据提供的上下文回答用户问题。\n"
        "如果上下文中没有足够信息，请明确说明“我无法从当前知识库中找到足够依据”。\n"
        "不要编造事实。\n\n"
        f"上下文：\n{context}\n\n问题：\n{question}"
    )
