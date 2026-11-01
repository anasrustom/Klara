"""
RAG (Retrieval-Augmented Generation) Service
- Chunking, embeddings (multilingual), FAISS vector index
- Per-contract semantic search and context assembly
"""

from typing import List, Dict, Optional, Tuple, Any
import os
import math
import numpy as np
import faiss

import google.generativeai as genai
from sentence_transformers import SentenceTransformer

from src.config.settings import get_settings

settings = get_settings()

DEFAULT_EMBEDDINGS_MODEL = getattr(
    settings, "embeddings_model", "intfloat/multilingual-e5-small"
)

def _normalize_embeddings(X: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(X, axis=1, keepdims=True) + 1e-12
    return X / norms

def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) + 1e-12
    return float(np.dot(a, b) / denom)

# e5 models are trained with these prefixes; using them improves retrieval
_PASSAGE_PREFIX = "passage: "
_QUERY_PREFIX = "query: "

def _word_chunks(
    text: str,
    approx_tokens: int = 220,
    overlap: int = 30,
    page_offsets: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """
    Rough token-aware chunking by words with overlap.
    If page_offsets is provided (list of starting char positions per page in normalized text),
    we approximate the chunk's 1-based page from its starting char; otherwise page is None.
    """
    words = (text or "").split()
    if not words:
        return []

    # Prefix char lengths to estimate starting char at word index i
    prefix = [0]
    for w in words:
        prefix.append(prefix[-1] + len(w) + 1)  # +1 for space/newline approx

    def page_for_char(start_char: int) -> Optional[int]:
        if not page_offsets:
            return None
        page = 0
        for p, off in enumerate(page_offsets):
            if off <= start_char:
                page = p
            else:
                break
        return page + 1

    chunks: List[Dict[str, Any]] = []
    step = max(1, approx_tokens - overlap)
    i = 0
    cid = 0
    while i < len(words):
        j = min(len(words), i + approx_tokens)
        seg = " ".join(words[i:j]).strip()
        if seg:
            start_char = prefix[i]
            page = page_for_char(start_char)
            chunks.append(
                {
                    "chunk_id": f"c_{cid:05d}",
                    "page": page,
                    "section": None,
                    "text": seg,
                }
            )
            cid += 1
        i += step
    return chunks


class RAGService:
    """
    Retrieval-Augmented Generation:
    - Build per-contract FAISS index
    - Semantic search within a contract
    - Global search across all indexed contracts
    """

    def __init__(self):
        if getattr(settings, "gemini_api_key", None):
            genai.configure(api_key=settings.gemini_api_key)

        self.model_name = DEFAULT_EMBEDDINGS_MODEL
        self.model: Optional[SentenceTransformer] = None
        try:
            self.model = SentenceTransformer(self.model_name)
        except Exception:
            self.model = None

        self._store: Dict[str, Dict[str, Any]] = {}

    async def index_contract(
        self,
        contract_id: str,
        text: str,
        language: str = "en",
        page_offsets: Optional[List[int]] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """
        Build/replace the FAISS index for a contract.
        Steps:
        1) chunk (page-aware if page_offsets provided)
        2) embed
        3) index (cosine similarity via inner product on normalized embeddings)
        """
        if not text or not text.strip():
            return False

        if self.model is None:
            try:
                self.model = SentenceTransformer(self.model_name)
            except Exception:
                return False

        # Page-aware chunking (uses page_offsets when provided)
        chunks = _word_chunks(text, approx_tokens=220, overlap=30, page_offsets=page_offsets)
        if not chunks:
            chunks = [{"chunk_id": "c_00000", "page": None, "section": None, "text": text[:2000]}]

        # Embed chunks (cosine via normalized + IndexFlatIP)
        texts = [_PASSAGE_PREFIX + c["text"] for c in chunks]
        vecs = self.model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        dim = vecs.shape[1]

        index = faiss.IndexFlatIP(dim)
        index.add(vecs)

        # Store in-memory index
        self._store[str(contract_id)] = {
            "index": index,
            "embeddings": vecs,
            "chunks": chunks,
            "language": language,
            "user_id": str(user_id) if user_id is not None else None,
        }
        return True

    def has_index(self, contract_id: str) -> bool:
        return str(contract_id) in self._store

    def get_chunks(self, contract_id: str) -> List[Dict[str, Any]]:
        entry = self._store.get(str(contract_id))
        return list(entry["chunks"]) if entry else []

    async def search_contract(self, contract_id: str, query: str, top_k: int = 5) -> List[Dict]:
        """
        Return top_k relevant chunks for a single contract.
        Each result: {chunk_id, text, score, page, section}
        """
        entry = self._store.get(str(contract_id))
        if entry is None or self.model is None:
            return []

        q = self.model.encode([_QUERY_PREFIX + query], normalize_embeddings=True, convert_to_numpy=True)
        D, I = entry["index"].search(q, min(top_k, len(entry["chunks"])))
        idxs = I[0].tolist()
        sims = D[0].tolist()

        results: List[Dict] = []
        for pos, score in zip(idxs, sims):
            if pos < 0:
                continue
            c = entry["chunks"][pos]
            results.append(
                {
                    "chunk_id": c["chunk_id"],
                    "text": c["text"],
                    "score": float(score),
                    "page": c.get("page"),
                    "section": c.get("section"),
                }
            )
        return results

    async def search_all_contracts(
        self,
        query: str,
        user_id: Optional[str] = None,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Search across the contracts indexed for one user. Returns top_k across their indices.
        Without a user_id nothing is searched, so one user can never see another's text.
        Each result: {contract_id, chunk_id, text, score, page, section}
        """
        if self.model is None or not self._store or user_id is None:
            return []

        q = self.model.encode([_QUERY_PREFIX + query], normalize_embeddings=True, convert_to_numpy=True)[0]
        results: List[Tuple[str, int, float]] = []

        for cid, entry in self._store.items():
            if entry.get("user_id") != str(user_id):
                continue
            index: faiss.IndexFlatIP = entry["index"]
            chunks = entry["chunks"]
            k = min(top_k, len(chunks))
            D, I = index.search(q.reshape(1, -1), k)
            for pos, score in zip(I[0].tolist(), D[0].tolist()):
                if pos < 0:
                    continue
                results.append((cid, pos, float(score)))

        results.sort(key=lambda t: t[2], reverse=True)
        results = results[:top_k]

        out: List[Dict] = []
        for cid, pos, score in results:
            c = self._store[cid]["chunks"][pos]
            out.append(
                {
                    "contract_id": cid,
                    "chunk_id": c["chunk_id"],
                    "text": c["text"],
                    "score": score,
                    "page": c.get("page"),
                    "section": c.get("section"),
                }
            )
        return out

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
        """
        Backwards-compatible API (character-based), wraps the word-based chunker.
        """
        return _word_chunks(text, approx_tokens=220, overlap=30)

    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate a single embedding vector for arbitrary text.
        """
        if self.model is None:
            try:
                self.model = SentenceTransformer(self.model_name)
            except Exception:
                return None
        v = self.model.encode([_QUERY_PREFIX + text], normalize_embeddings=True, convert_to_numpy=True)[0]
        return v.tolist()

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Cosine similarity between two vectors.
        """
        a = np.asarray(embedding1, dtype=np.float32)
        b = np.asarray(embedding2, dtype=np.float32)
        return _cosine_similarity(a, b)

    async def get_relevant_context(
        self,
        contract_id: str,
        query: str,
        max_context_length: int = 2000
    ) -> str:
        """
        Concatenate top chunks until max_context_length. Include simple headers for clarity.
        """
        hits = await self.search_contract(contract_id=contract_id, query=query, top_k=8)
        if not hits:
            return ""

        buf: List[str] = []
        total = 0
        for h in hits:
            piece = f"[{h.get('chunk_id')}] (p.{h.get('page') or '?'}): {h.get('text','').strip()}"
            if not piece:
                continue
            if total + len(piece) + 2 > max_context_length:
                break
            buf.append(piece)
            total += len(piece) + 2

        return "\n\n".join(buf)

    async def remove_contract_from_index(self, contract_id: str) -> bool:
        """
        Remove a contract from memory index.
        """
        if str(contract_id) in self._store:
            del self._store[str(contract_id)]
            return True
        return False

rag_service = RAGService()
