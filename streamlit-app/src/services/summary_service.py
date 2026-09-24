SUMMARY_PROMPT = """You are ResearchLens AI, an academic research-paper summarizer.
Create a grounded research summary using only the supplied paper text.
Use exactly these headings:
## Overview
## Key Contributions
## Methodology
## Results
## Limitations
## Conclusion
Do not fabricate missing details. If a section cannot be supported, explicitly say so.
"""

class SummaryService:
    def __init__(self, chat_service):
        self.chat_service = chat_service

    def summarize(self, filename: str, content: str) -> str:
        prompt=f"Paper filename: {filename}\n\nPaper content:\n{content[:50000]}"
        return self.chat_service.generate(prompt, system_instruction=SUMMARY_PROMPT)
