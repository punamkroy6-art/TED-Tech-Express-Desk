from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.database import AsyncSessionLocal
from app.models.error_pattern import ErrorPattern

# Lightweight keyword-based RAG — no vector DB required in Phase 1
async def search_knowledge_base(error_text: str, top_k: int = 3) -> list[dict]:
    """Return the top_k matching error patterns as KB context objects."""
    async with AsyncSessionLocal() as db:
        try:
            # Attempt full-text search (PostgreSQL)
            rows = await db.execute(
                text("""
                    SELECT description, fix_steps, severity, keywords
                    FROM error_patterns
                    WHERE is_active = true
                    ORDER BY similarity(array_to_string(keywords, ' '), :q) DESC
                    LIMIT :k
                """),
                {"q": error_text, "k": top_k},
            )
            results = rows.mappings().all()
        except Exception:
            # SQLite fallback — simple LIKE search
            words = [w.lower() for w in error_text.split() if len(w) > 3]
            results = []
            if words:
                result = await db.execute(select(ErrorPattern).where(ErrorPattern.is_active == True))
                patterns = result.scalars().all()
                scored = []
                for p in patterns:
                    kw = " ".join(p.keywords or []).lower()
                    score = sum(1 for w in words if w in kw)
                    if score:
                        scored.append((score, p))
                scored.sort(key=lambda x: -x[0])
                results = [
                    {"description": p.description, "fix_steps": p.fix_steps,
                     "severity": p.severity, "keywords": p.keywords}
                    for _, p in scored[:top_k]
                ]

        return [
            {
                "title": r.get("description", "") if isinstance(r, dict) else r["description"],
                "resolution": str(r.get("fix_steps", "") if isinstance(r, dict) else r["fix_steps"]),
            }
            for r in results
        ]
