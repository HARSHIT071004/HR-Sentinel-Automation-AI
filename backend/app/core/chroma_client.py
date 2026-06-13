from app.config import settings


class MockChromaCollection:
    def __init__(self, name):
        self.name = name
        self._docs = []

    def add(self, documents=None, metadatas=None, ids=None):
        if documents:
            for i, doc in enumerate(documents):
                self._docs.append({
                    "id": ids[i] if ids else str(len(self._docs)),
                    "document": doc,
                    "metadata": metadatas[i] if metadatas else {},
                })

    def query(self, query_texts=None, n_results=5, where=None):
        if not self._docs:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        results = self._docs[:n_results]
        return {
            "documents": [[r["document"] for r in results]],
            "metadatas": [[r["metadata"] for r in results]],
            "distances": [[0.5 * i for i in range(len(results))]],
        }


class MockChromaClient:
    def __init__(self):
        self._collections = {}

    def get_or_create_collection(self, name, metadata=None):
        if name not in self._collections:
            self._collections[name] = MockChromaCollection(name)
        return self._collections[name]

    def list_collections(self):
        return list(self._collections.values())

    def delete_collection(self, name):
        self._collections.pop(name, None)


class ChromaService:
    def __init__(self):
        self.client = MockChromaClient()

    def get_or_create_collection(self, name: str):
        return self.client.get_or_create_collection(name)

    async def get_embedding(self, text: str) -> list[float]:
        return [0.1] * 1536

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 1536 for _ in texts]

    def add_documents(self, collection_name: str, documents: list[str], metadatas: list[dict], ids: list[str]):
        collection = self.get_or_create_collection(collection_name)
        collection.add(documents=documents, metadatas=metadatas, ids=ids)

    def search(self, collection_name: str, query: str, n_results: int = 5) -> dict:
        collection = self.get_or_create_collection(collection_name)
        return collection.query(query_texts=[query], n_results=n_results)

    def search_with_filter(self, collection_name: str, query: str, where: dict, n_results: int = 5) -> dict:
        collection = self.get_or_create_collection(collection_name)
        return collection.query(query_texts=[query], where=where, n_results=n_results)

    def delete_collection(self, name: str):
        self.client.delete_collection(name)

    def list_collections(self) -> list[str]:
        return [c.name for c in self.client.list_collections()]


chroma_service = ChromaService()
