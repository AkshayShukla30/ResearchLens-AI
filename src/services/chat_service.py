from __future__ import annotations

from google import genai

SYSTEM_PROMPT = """You are ResearchLens AI, an academic research assistant.
Answer questions using the supplied evidence from uploaded research papers.

Rules:
1. Ground factual claims in the supplied evidence.
2. Do not invent paper details, page numbers, datasets, metrics, or citations.
3. If evidence is insufficient, clearly say that the uploaded papers do not provide enough information.
4. For comparison questions, distinguish each paper explicitly.
5. Prefer precise, structured answers suitable for research notes.
"""

class ChatService:
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        if not api_key:
            raise ValueError("GEMINI_API_KEY is missing.")
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate(self, prompt: str, system_instruction: str = SYSTEM_PROMPT) -> str:
        response = self.client.models.generate_content(
            model=self.model, contents=prompt,
            config={"system_instruction": system_instruction, "temperature": 0.1},
        )
        if not response.text:
            raise RuntimeError("Gemini returned an empty response.")
        return response.text

    def answer(self, query, retrieved, history):
        evidence=[]
        for i,item in enumerate(retrieved,1):
            page=f"page {item['page']}" if item.get('page') else "page unavailable"
            evidence.append(f"[Evidence {i}] {item['source']} | {page}\n{item['text']}")
        previous=[f"{m['role'].upper()}: {m['content'][:1800]}" for m in history[-6:]]
        prompt=(f"Research question:\n{query}\n\nPrevious conversation context:\n"
                f"{chr(10).join(previous) if previous else 'None'}\n\n"
                "Retrieved evidence from uploaded research papers:\n"+"\n\n".join(evidence))
        return self.generate(prompt)
