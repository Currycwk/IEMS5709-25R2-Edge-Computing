# Sample Knowledge Base

RAG stands for Retrieval-Augmented Generation. It combines information retrieval with large language model generation.

A typical RAG pipeline includes document loading, text splitting, embedding generation, vector search, and answer generation.

Qwen3-4B can be used as the generation model, while BGE-M3 can be used as the embedding model in a local deployment.


RAG（检索增强生成）是一种结合信息检索与文本生成的技术，通过“先查资料后回答”机制解决传统模型知识更新滞后及幻觉问题。其核心流程包括：1) 检索：从外部知识库中查找相关文本片段；2) 生成：将检索结果与用户查询输入给大语言模型生成回答。RAG利用Embedding模型将文本转为向量，通过语义匹配实现高效检索，提供更准确、实时的回答。