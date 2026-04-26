import re

from config import settings
from embedding_client import EmbeddingClient
from langchain_flow import PromptOrchestrator
from llm_client import LLMClient
from loader import (
    list_external_code_projects,
    load_documents,
    load_external_code_project_documents,
)
from splitter import split_documents
from vector_store import create_vector_store

TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


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
        local_mode = settings.llm_mode.strip().lower() == "local"
        llm_max_tokens = settings.local_max_tokens if local_mode else settings.api_max_tokens
        self.llm_client = LLMClient(
            settings.qwen_base_url,
            settings.qwen_model,
            api_key=settings.qwen_api_key,
            health_path=settings.qwen_health_path,
            max_tokens=llm_max_tokens,
            enable_thinking=None,
        )
        self.active_corpus = "knowledge"
        self.active_code_project: str | None = None

    def build_index(self, corpus: str = "knowledge", code_project: str | None = None) -> dict:
        documents = self._load_corpus_documents(corpus=corpus, code_project=code_project)
        chunks = split_documents(documents)
        self.vector_store.add_documents(chunks, self.embedding_client)

        self.active_corpus = corpus
        self.active_code_project = code_project if corpus == "external_code" else None

        doc_types: dict[str, int] = {}
        for doc in documents:
            doc_type = doc.metadata.get("doc_type", "unknown")
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

        return {
            "documents": len(documents),
            "chunks": len(chunks),
            "index_ready": self.vector_store.is_ready(),
            "doc_types": doc_types,
            "corpus": corpus,
            "code_project": self.active_code_project,
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
            "llm_mode": settings.llm_mode,
            "llm_base_url": settings.qwen_base_url,
            "llm_model": settings.qwen_model,
            "llm_max_tokens": self.llm_client.max_tokens,
            "llm_enable_thinking": self.llm_client.enable_thinking,
            "retrieval_strategy": settings.retrieval_strategy,
            "retrieval_fetch_k": settings.retrieval_fetch_k,
            "expand_adjacent_chunks": settings.expand_adjacent_chunks,
            "active_corpus": self.active_corpus,
            "active_code_project": self.active_code_project,
            "available_code_projects": list_external_code_projects(settings.code_projects_dir),
        }

    def clear_index(self) -> None:
        self.vector_store.clear()
        self.active_corpus = "knowledge"
        self.active_code_project = None

    def chat_stream(
        self,
        question: str,
        top_k: int | None = None,
        corpus: str | None = None,
        code_project: str | None = None,
    ) -> tuple:
        prompt, sources = self._prepare_prompt_and_sources(
            question,
            top_k=top_k,
            corpus=corpus,
            code_project=code_project,
        )
        token_stream = self.llm_client.stream_answer(prompt)
        return token_stream, sources

    def _prepare_prompt_and_sources(
        self,
        question: str,
        top_k: int | None = None,
        corpus: str | None = None,
        code_project: str | None = None,
    ) -> tuple[str, list[dict]]:
        if not self.vector_store.is_ready():
            raise RuntimeError("Index not built yet")

        if corpus and corpus != self.active_corpus:
            raise RuntimeError("当前索引语料与提问模式不一致，请先重新构建索引")
        if corpus == "external_code" and code_project and code_project != self.active_code_project:
            raise RuntimeError("当前索引项目与提问项目不一致，请先重新构建索引")

        requested_top_k = top_k or settings.top_k
        fetch_k = max(requested_top_k, settings.retrieval_fetch_k)

        initial_results = self.vector_store.similarity_search(
            question,
            self.embedding_client,
            top_k=fetch_k,
        )

        reranked = self._rerank_results(question, initial_results)
        selected = reranked[:requested_top_k]

        if settings.expand_adjacent_chunks:
            selected = self._expand_with_adjacent_chunks(selected, requested_top_k)

        context = "\n\n".join(item["page_content"] for item in selected if item["page_content"])
        prompt = self.prompt_orchestrator.render(context, question)
        sources = [
            {
                "source": item["metadata"].get("source", "unknown"),
                "content": item["page_content"],
                "score": round(float(item.get("score", 0.0)), 4),
                "doc_type": item["metadata"].get("doc_type", "unknown"),
                "page": item["metadata"].get("page"),
                "chunk_index": item["metadata"].get("chunk_index"),
                "project": item["metadata"].get("project"),
                "language": item["metadata"].get("language"),
                "corpus": item["metadata"].get("corpus", self.active_corpus),
            }
            for item in selected
        ]
        return prompt, sources

    def _load_corpus_documents(self, corpus: str, code_project: str | None = None):
        normalized = (corpus or "knowledge").strip().lower()
        if normalized == "knowledge":
            return load_documents(settings.data_dir)
        if normalized == "external_code":
            return load_external_code_project_documents(settings.code_projects_dir, project_name=code_project)
        raise RuntimeError(f"Unsupported corpus: {corpus}")

    def _rerank_results(self, question: str, candidates: list[dict]) -> list[dict]:
        strategy = settings.retrieval_strategy.strip().lower()
        if strategy in {"vector", "dense"}:
            return sorted(candidates, key=lambda item: item.get("score", 0.0), reverse=True)

        query_term_set = set(_tokenize(question))

        reranked = []
        for item in candidates:
            dense_score = float(item.get("score", 0.0))
            lexical_score = _lexical_overlap_score(query_term_set, item.get("page_content", ""))
            hybrid_score = 0.72 * dense_score + 0.28 * lexical_score
            enriched = dict(item)
            enriched["dense_score"] = dense_score
            enriched["lexical_score"] = lexical_score
            enriched["score"] = hybrid_score
            reranked.append(enriched)

        reranked.sort(key=lambda item: item.get("score", 0.0), reverse=True)
        return reranked

    def _expand_with_adjacent_chunks(self, selected: list[dict], requested_top_k: int) -> list[dict]:
        if not selected:
            return selected

        seen_ids = {int(item.get("entry_id", -1)) for item in selected if "entry_id" in item}
        expanded = list(selected)

        for item in list(selected):
            metadata = item.get("metadata", {})
            chunk_index = metadata.get("chunk_index")
            source_doc_id = metadata.get("source_doc_id")
            if chunk_index is None or source_doc_id is None:
                continue

            for delta in (-1, 1):
                if len(expanded) >= requested_top_k:
                    break

                candidate_entry = self.vector_store.get_entry_by_id(int(item.get("entry_id", -1)) + delta)
                if candidate_entry is None:
                    continue
                candidate_id = int(candidate_entry.get("entry_id", -1))
                if candidate_id in seen_ids:
                    continue

                candidate_meta = candidate_entry.get("metadata", {})
                if candidate_meta.get("source_doc_id") != source_doc_id:
                    continue
                if candidate_meta.get("chunk_index") != chunk_index + delta:
                    continue

                candidate_entry["score"] = max(0.0, float(item.get("score", 0.0)) * 0.96)
                expanded.append(candidate_entry)
                seen_ids.add(candidate_id)

        expanded.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return expanded[:requested_top_k]


pipeline = RAGPipeline()


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


def _lexical_overlap_score(query_terms: set[str], passage: str) -> float:
    if not query_terms:
        return 0.0
    passage_terms = set(_tokenize(passage))
    if not passage_terms:
        return 0.0
    hit = len(query_terms.intersection(passage_terms))
    return hit / max(1, len(query_terms))
