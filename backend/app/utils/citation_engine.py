class CitationEngine:
    def __init__(self):
        self.citation_map = {
            "policies": "Attendance Policy",
            "employee_summaries": "Employee Data",
            "department_reports": "Department Report",
        }

    def format_citations(self, sources: list[dict]) -> str:
        if not sources:
            return ""

        citations = []
        seen = set()

        for source in sources:
            title = source.get("title", "Unknown")
            header = source.get("header", "")
            doc_type = source.get("doc_type", "")

            if title in seen:
                continue
            seen.add(title)

            if header:
                citation = f"According to {title} - {header}"
            else:
                citation = f"According to {title}"

            citations.append(citation)

        if not citations:
            return ""

        return "\n\nSources:\n" + "\n".join([f"[{i+1}] {c}" for i, c in enumerate(citations)])

    def extract_source_references(self, text: str, sources: list[dict]) -> list[dict]:
        references = []
        for i, source in enumerate(sources):
            references.append({
                "index": i + 1,
                "title": source.get("title", "Unknown"),
                "header": source.get("header", ""),
                "doc_type": source.get("doc_type", ""),
                "relevance": source.get("relevance", 0),
            })
        return references

    def build_grounded_prompt(self, query: str, context: str, sources: list[dict]) -> str:
        source_list = "\n".join([
            f"[{i+1}] {s.get('title', 'Unknown')} - {s.get('header', '')}: {s.get('content', '')[:200]}..."
            for i, s in enumerate(sources[:5])
        ])

        return f"""Based on the following context, answer the user's question.

CONTEXT:
{context}

SOURCES:
{source_list}

RULES:
1. Answer ONLY based on the provided context
2. If context is insufficient, say "I don't have enough information to answer that question"
3. Include source references in your answer using [1], [2], etc.
4. Be helpful and professional
5. Never fabricate information

QUESTION: {query}

ANSWER:"""


citation_engine = CitationEngine()
