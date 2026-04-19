from config import settings
from embedding_client import EmbeddingClient
from llm_client import LLMClient
from loader import load_documents
from prompt import build_prompt
from splitter import split_documents
from vector_store import SimpleVectorStore


class RAGPipeline:
    def __init__(self):
        self.embedding_client = EmbeddingClient(settings.embedding_model_path)
        self.vector_store = SimpleVectorStore(settings.vector_db_dir)
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
        }

    def chat(self, question: str, top_k: int | None = None) -> dict:
        if not self.vector_store.is_ready():
            raise RuntimeError("Index not built yet")

        results = self.vector_store.similarity_search(
            question,
            self.embedding_client,
            top_k=top_k or settings.top_k,
        )
        context = "\n\n".join(item["page_content"] for item in results if item["page_content"])
        prompt = build_prompt(context, question)
        answer = self.llm_client.answer(question, prompt)
        sources = [
            {
                "source": item["metadata"].get("source", "unknown"),
                "content": item["page_content"],
                "score": round(item["score"], 4),
            }
            for item in results
        ]
        return {
            "answer": answer,
            "sources": sources,
        }


pipeline = RAGPipeline()
