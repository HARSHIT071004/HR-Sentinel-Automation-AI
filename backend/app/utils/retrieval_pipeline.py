from app.core.chroma_client import chroma_service


class RetrievalPipeline:
    def __init__(self):
        self.collections = ["policies", "employee_summaries", "department_reports"]

    def search_policies(self, query: str, n_results: int = 3) -> list[dict]:
        results = chroma_service.search("policies", query, n_results=n_results)
        return self._format_results(results)

    def search_employee_summaries(self, query: str, n_results: int = 3) -> list[dict]:
        results = chroma_service.search("employee_summaries", query, n_results=n_results)
        return self._format_results(results)

    def search_department_reports(self, query: str, n_results: int = 3) -> list[dict]:
        results = chroma_service.search("department_reports", query, n_results=n_results)
        return self._format_results(results)

    def hybrid_search(self, query: str, collections: list[str] | None = None, n_results: int = 5) -> list[dict]:
        if collections is None:
            collections = self.collections

        all_results = []
        for collection in collections:
            try:
                results = chroma_service.search(collection, query, n_results=n_results)
                formatted = self._format_results(results)
                all_results.extend(formatted)
            except Exception:
                continue

        # Sort by relevance (distance)
        all_results.sort(key=lambda x: x.get("distance", 1.0))

        return all_results[:n_results]

    def search_by_type(self, query: str, doc_type: str, n_results: int = 5) -> list[dict]:
        all_results = []
        for collection in self.collections:
            try:
                results = chroma_service.search_with_filter(
                    collection, query, where={"doc_type": doc_type}, n_results=n_results
                )
                formatted = self._format_results(results)
                all_results.extend(formatted)
            except Exception:
                continue

        all_results.sort(key=lambda x: x.get("distance", 1.0))
        return all_results[:n_results]

    def _format_results(self, results: dict) -> list[dict]:
        formatted = []
        if not results or not results.get("documents"):
            return formatted

        documents = results["documents"][0] if results["documents"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []
        distances = results["distances"][0] if results.get("distances") else []

        for i in range(len(documents)):
            meta = metadatas[i] if i < len(metadatas) else {}
            distance = distances[i] if i < len(distances) else 1.0

            formatted.append({
                "content": documents[i],
                "title": meta.get("title", "Unknown"),
                "header": meta.get("header", ""),
                "doc_type": meta.get("doc_type", "unknown"),
                "document_id": meta.get("document_id", ""),
                "distance": distance,
                "relevance": max(0, 1 - distance),
            })

        return formatted


retrieval_pipeline = RetrievalPipeline()
