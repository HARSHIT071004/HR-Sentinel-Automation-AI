import time
import json
import hashlib
import logging
import importlib
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)


def _hash_embedding(text: str, dim: int = 1536) -> list[float]:
    """Deterministic fallback embedding using MD5 hashing."""
    raw = hashlib.md5(text.encode("utf-8")).digest()
    seed = int.from_bytes(raw[:4], "little")
    try:
        np = importlib.import_module("numpy")
        rng = np.random.default_rng(seed)
        vec = rng.normal(0, 0.1, dim).astype(np.float32)
        norm = np.linalg.norm(vec)
        return (vec / norm).tolist() if norm > 0 else [0.0] * dim
    except ModuleNotFoundError:
        import random
        rng = random.Random(seed)
        vec = [rng.gauss(0, 0.1) for _ in range(dim)]
        mag = sum(v * v for v in vec) ** 0.5
        return [v / mag for v in vec] if mag > 0 else [0.0] * dim


class AIClient:
    def __init__(self):
        self._has_openai = bool(settings.OPENAI_API_KEY)
        if self._has_openai:
            self.client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_BASE_URL,
            )
        else:
            self.client = None
        self.model = settings.OPENAI_MODEL
        self.embed_model = "text-embedding-3-small"

    async def generate(self, system_prompt: str, user_prompt: str, model: str | None = None, temperature: float = 0.3, max_tokens: int = 2000, retries: int = 2) -> dict:
        use_model = model or self.model
        if not self.client:
            return self._fallback(use_model, system_prompt, user_prompt)

        last_error = None
        for attempt in range(retries + 1):
            start_time = time.time()
            try:
                response = await self.client.chat.completions.create(
                    model=use_model,
                    messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                    temperature=temperature, max_tokens=max_tokens,
                )
                latency_ms = int((time.time() - start_time) * 1000)
                choice = response.choices[0]
                usage = response.usage
                return {"content": choice.message.content, "model": use_model, "prompt_tokens": usage.prompt_tokens if usage else 0, "completion_tokens": usage.completion_tokens if usage else 0, "total_tokens": (usage.prompt_tokens + usage.completion_tokens) if usage else 0, "cost_usd": 0.0, "latency_ms": latency_ms}
            except Exception as e:
                last_error = e
                if attempt < retries:
                    time.sleep(1)
        return self._fallback(use_model, system_prompt, user_prompt)

    def _fallback(self, model: str, system_prompt: str, user_prompt: str) -> dict:
        return {"content": None, "model": model, "prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "cost_usd": 0.0, "latency_ms": 0, "error": "API unavailable"}

    async def generate_json(self, system_prompt: str, user_prompt: str, model: str | None = None, temperature: float = 0.3) -> dict:
        result = await self.generate(system_prompt=system_prompt, user_prompt=user_prompt, model=model, temperature=temperature)
        if result.get("error") or not result.get("content"):
            return {"data": None, "model": result["model"], "tokens": 0, "cost": 0.0, "latency": 0, "error": result.get("error")}
        try:
            data = json.loads(result["content"])
        except json.JSONDecodeError:
            content = result["content"]
            if "```json" in content:
                data = json.loads(content.split("```json")[1].split("```")[0].strip())
            elif "```" in content:
                data = json.loads(content.split("```")[1].split("```")[0].strip())
            else:
                data = {"raw": content}
        return {"data": data, "model": result["model"], "tokens": result["total_tokens"], "cost": 0.0, "latency": result["latency_ms"], "error": None}


    async def embed(self, text: str) -> list[float]:
        if self._has_openai:
            try:
                resp = await self.client.embeddings.create(
                    model=self.embed_model, input=text
                )
                return resp.data[0].embedding
            except Exception as e:
                logger.warning(f"OpenAI embedding failed, using fallback: {e}")
        return _hash_embedding(text)

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if self._has_openai and len(texts) > 0:
            try:
                resp = await self.client.embeddings.create(
                    model=self.embed_model, input=texts
                )
                return [d.embedding for d in resp.data]
            except Exception as e:
                logger.warning(f"OpenAI batch embedding failed, using fallback: {e}")
        return [_hash_embedding(t) for t in texts]


ai_client = AIClient()
