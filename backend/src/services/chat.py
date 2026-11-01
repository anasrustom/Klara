from typing import Dict, List, Optional, Any
import json

from src.services.rag import rag_service
from src.services.llm import json_model, generate_json, LLMError
from src.utils.text import grounded_snippet

SYSTEM_QA_INSTRUCTIONS = (
    "You are an AI contract analyst. Answer the user's question STRICTLY from the provided CHUNKS. "
    "If the answer is not present in the chunks, say you cannot find it in the contract text. "
    "Answer in the same language as the question, in two to five sentences, and name the clause or section when the text gives one. "
    "Return ONLY JSON with keys: answer (string), citations (list of {chunk_id, quote}), confidence (0..1). "
    "Each citation must use a chunk_id from the input, and quote must be copied verbatim from that chunk (at most 200 characters). "
    "HISTORY holds earlier turns of this conversation for context only; never cite it."
)

_SNIPPET_MAX = 240


def _grounded_snippet(chunk_text: str, quote: Any) -> str:
    """Copy the quoted span from the chunk; never show the model's own wording as a quote."""
    return grounded_snippet(chunk_text, quote, _SNIPPET_MAX)


class ChatService:
    """
    Service for handling natural language questions about contracts.
    """

    # Guardrail bounds
    _MAX_CITATIONS = 4
    _MAX_OUTPUT_TOKENS = 2048
    _HISTORY_TURNS = 4

    def __init__(self):
        self.model = json_model(self._MAX_OUTPUT_TOKENS)

    async def answer_question(
        self,
        question: str,
        contract_id: Optional[str] = None,
        user_id: Optional[str] = None,
        previous_messages: Optional[List[Dict]] = None,
        contract_titles: Optional[Dict[str, str]] = None,
    ) -> Dict:
        """
        If contract_id is provided, search only that contract; otherwise search
        the contracts indexed for user_id.
        Returns {answer, citations: [{chunk_id, page, snippet, contract_id, contract_title}], sources, confidence}.
        """
        if not self.model:
            return {
                "answer": "Chat service is not configured. Please add GEMINI_API_KEY to backend/.env.",
                "citations": [],
                "sources": [],
                "confidence": 0.0,
            }

        # 1) Retrieve relevant chunks via RAG
        if contract_id:
            hits = await rag_service.search_contract(str(contract_id), question, top_k=8)
            for h in hits:
                h["contract_id"] = str(contract_id)
        else:
            hits = await rag_service.search_all_contracts(question, user_id=user_id, top_k=10)

        if not hits:
            return {
                "answer": "I couldn't find relevant text in your contracts to answer that.",
                "citations": [],
                "sources": [],
                "confidence": 0.0,
            }

        # Chunk ids repeat across contracts, so give each hit a unique key for the model
        keyed = {}
        for i, h in enumerate(hits):
            key = h["chunk_id"] if contract_id else f"{i}:{h['chunk_id']}"
            keyed[key] = h
        titles = contract_titles or {}

        history = [
            {"question": m.get("message"), "answer": m.get("response")}
            for m in (previous_messages or [])[-self._HISTORY_TURNS:]
        ]
        payload = {
            "question": question,
            "HISTORY": history,
            "chunks": [
                {
                    "chunk_id": key,
                    "page": h.get("page"),
                    **({"contract": titles.get(h.get("contract_id"), "")} if not contract_id else {}),
                    "text": h["text"],
                }
                for key, h in keyed.items()
            ],
        }

        try:
            data = await generate_json(
                self.model,
                [{"text": SYSTEM_QA_INSTRUCTIONS}, {"text": json.dumps(payload, ensure_ascii=False)}],
                retries=1,
            )
            if not isinstance(data, dict):
                raise LLMError("Model returned JSON that is not an object")
        except LLMError:
            # Still useful: show the passages the answer would have come from
            fallback = [self._citation(key, h, None, titles) for key, h in list(keyed.items())[:3]]
            return {
                "answer": "I had trouble generating an answer. Here are the most relevant passages.",
                "citations": fallback,
                "sources": self.format_sources(fallback),
                "confidence": 0.0,
            }

        citations = []
        seen = set()
        for item in data.get("citations") or []:
            if not isinstance(item, dict):
                continue
            key = str(item.get("chunk_id") or "").strip()
            if key not in keyed or key in seen:
                continue
            seen.add(key)
            citations.append(self._citation(key, keyed[key], item.get("quote"), titles))
            if len(citations) >= self._MAX_CITATIONS:
                break

        answer = data.get("answer") or "I couldn't find that in the provided context."
        try:
            confidence = float(data.get("confidence", 0.5))
        except (TypeError, ValueError):
            confidence = 0.5

        return {
            "answer": answer,
            "citations": citations,
            "sources": self.format_sources(citations),
            "confidence": max(0.0, min(1.0, confidence)),
        }

    async def answer_contract_question(
        self,
        question: str,
        contract_id: str,
        previous_messages: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Contract-scoped Q&A. Delegates to answer_question with contract_id.
        """
        return await self.answer_question(
            question=question, contract_id=contract_id, previous_messages=previous_messages
        )

    async def answer_general_question(
        self,
        question: str,
        user_id: str,
        previous_messages: Optional[List[Dict]] = None,
        contract_titles: Optional[Dict[str, str]] = None,
    ) -> Dict:
        """
        Portfolio-wide Q&A across the user's own indexed contracts.
        """
        return await self.answer_question(
            question=question,
            user_id=user_id,
            previous_messages=previous_messages,
            contract_titles=contract_titles,
        )

    def format_sources(self, citations: List[Dict[str, Any]]) -> List[str]:
        """
        Plain-text form of the citations, kept for older clients.
        """
        return [
            f"{c['chunk_id']} p.{c['page'] if c.get('page') else '?'}: {c['snippet']}"
            for c in citations
        ]

    # ---------- Internal helpers ----------

    def _citation(self, key: str, hit: Dict[str, Any], quote: Any, titles: Dict[str, str]) -> Dict[str, Any]:
        cid = hit.get("contract_id")
        return {
            "chunk_id": hit["chunk_id"],
            "page": hit.get("page"),
            "snippet": _grounded_snippet(hit.get("text", ""), quote),
            "contract_id": cid,
            "contract_title": titles.get(cid) if cid else None,
        }


chat_service = ChatService()
