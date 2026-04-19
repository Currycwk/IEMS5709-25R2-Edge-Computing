from config import settings
from embedding_client import EmbeddingClient
from langchain_flow import PromptOrchestrator
from llm_client import LLMClient
from loader import load_documents
from splitter import split_documents
from vector_store import create_vector_store


class RAGPipeline:
    def __init__(self):
        self.embedding_client = EmbeddingClient(
            settings.embedding_model_path,
            backend=settings.embedding_backend,
        )
        self.vector_store, self.vector_backend = create_vector_store(
            settings.vector_db_dir,
            backend=settings.vector_backend,
        )
        self.prompt_orchestrator = PromptOrchestrator()
        self.llm_client = LLMClient(settings.qwen_base_url, settings.qwen_model)

    def build_index(self) -> dict:
        documents = load_documents(settings.data_dir)
        chunks = split_documents(documents)
        self.vector_store.add_documents(chunks, self.embedding_client)
        return {
            "documents": len(documents),
            "chunks": len(chunks),
            "index_ready": self.vector_store.is_ready(),
        }

    def status(self) -> dict:
        return {
            "backend": True,
            "index_ready": self.vector_store.is_ready(),
            "qwen_ready": self.llm_client.health(),
            "embedding_ready": self.embedding_client.health(),
            "embedding_backend": self.embedding_client.active_backend,
            "vector_backend": self.vector_backend,
            "chain_backend": self.prompt_orchestrator.backend,
        }

    def chat(self, question: str, top_k: int | None = None) -> dict:
        prompt, sources = self._prepare_prompt_and_sources(question, top_k=top_k)
        answer = self.llm_client.answer(prompt)
        return {
            "answer": answer,
            "sources": sources,
        }

    def chat_stream(self, question: str, top_k: int | None = None) -> tuple:
        prompt, sources = self._prepare_prompt_and_sources(question, top_k=top_k)
        token_stream = self.llm_client.stream_answer(prompt)
        return token_stream, sources

    def _prepare_prompt_and_sources(self, question: str, top_k: int | None = None) -> tuple[str, list[dict]]:
        if not self.vector_store.is_ready():
            raise RuntimeError("Index not built yet")

        results = self.vector_store.similarity_search(
            question,
            self.embedding_client,
            top_k=top_k or settings.top_k,
        )
        context = "\n\n".join(item["page_content"] for item in results if item["page_content"])
        prompt = self.prompt_orchestrator.render(context, question)
        sources = [
            {
                "source": item["metadata"].get("source", "unknown"),
                "content": item["page_content"],
                "score": round(item["score"], 4),
            }
            for item in results
        ]
        return prompt, sources


pipeline = RAGPipeline()
