import hashlib, json, time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.database import get_redis, AsyncSessionLocal
from app.models.error_pattern import ErrorPattern
from app.services.rag_service import search_knowledge_base

SYSTEM_PROMPT = """You are an expert IT support engineer at a corporate helpdesk.
Given an error description and device info, provide:
1. A plain-English diagnosis (1-2 sentences)
2. Numbered step-by-step fix instructions (max 5 steps)
3. A suggested IT assignment group if escalation needed
Be concise. Avoid jargon. Use simple language an employee can follow."""


async def run_diagnosis(session_id: str, payload: dict) -> dict:
    t0 = time.time()
    error_text = payload.get("error_text", "")
    device_info = payload.get("device_info", {})

    # 1. Redis cache check
    cache_key = f"diag:{_hash(error_text)}"
    try:
        redis = await get_redis()
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:
        pass

    # 2. Rule-based match against error_patterns table
    rule_result = await _rule_match(error_text, device_info)
    if rule_result["confidence"] >= 0.55:  # rule engine is high-precision; use at lower threshold
        rule_result["processing_ms"] = int((time.time() - t0) * 1000)
        _try_cache(cache_key, rule_result)
        return rule_result

    # 3. RAG lookup
    rag_context = await search_knowledge_base(error_text, top_k=settings.rag_top_k)

    # 4. LLM inference (Groq) — graceful fallback if key missing
    result = await _llm_diagnose(payload, rag_context)
    result["processing_ms"] = int((time.time() - t0) * 1000)
    _try_cache(cache_key, result)
    return result


def _normalise_fix_steps(raw: list) -> list[str]:
    """Convert fix_steps from any format to a flat list of strings."""
    if not raw:
        return []
    result = []
    for item in raw:
        if isinstance(item, dict):
            # {"step": 1, "instruction": "..."} or {"text": "..."}
            text = item.get("instruction") or item.get("text") or str(item)
            result.append(text)
        else:
            result.append(str(item))
    return result


async def _rule_match(error_text: str, device_info: dict) -> dict:
    text_lower = error_text.lower()
    # Build word set AND keep full text for multi-word phrase matching
    words = {w for w in text_lower.split() if len(w) > 2}

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ErrorPattern).where(ErrorPattern.is_active == True)
        )
        patterns = result.scalars().all()

    best_score = 0.0
    best_pattern = None
    for p in patterns:
        kw = [k.lower() for k in (p.keywords or [])]
        hits = 0
        for k in kw:
            if " " in k:
                # Multi-word phrase: check full text
                if k in text_lower:
                    hits += 1
            else:
                # Single word: check word set
                if k in words or any(k in w for w in words):
                    hits += 1
        score = hits / max(len(kw), 1)
        if score > best_score:
            best_score = score
            best_pattern = p

    if best_pattern and best_score >= 0.35:
        confidence = min(best_score * 1.6, 0.95)
        fix_steps = _normalise_fix_steps(best_pattern.fix_steps)
        return {
            "diagnosis": best_pattern.description,
            "confidence": confidence,
            "severity": best_pattern.severity,
            "fix_steps": fix_steps,
            "kb_references": [],
            "suggested_group": "IT_SD",
            "action": "self_resolve" if confidence >= 0.75 else "guided_fix",
            "llm_model": "rule_engine",
        }

    return {"confidence": 0.0, "action": "create_ticket"}


async def _llm_diagnose(payload: dict, rag_context: list) -> dict:
    key = settings.groq_api_key
    if not key:
        return _mock_diagnosis(payload)

    context_str = "\n".join(
        [f"- {r['title']}: {r['resolution']}" for r in rag_context]
    ) or "No past resolutions found."

    user_msg = (
        f"Error description: {payload.get('error_text', 'Unknown error')}\n"
        f"Device info: {json.dumps(payload.get('device_info', {}))}\n"
        f"Similar past resolutions:\n{context_str}"
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ]

    try:
        if key.startswith("xai-"):
            # xAI / Grok — OpenAI-compatible endpoint
            import httpx
            resp = httpx.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": settings.xai_model, "messages": messages, "max_tokens": 800, "temperature": 0.2},
                timeout=settings.llm_timeout_secs,
            )
            resp.raise_for_status()
            data = resp.json()
            text = data["choices"][0]["message"]["content"]
            model_used = settings.xai_model
            tokens = data.get("usage", {}).get("total_tokens")
        else:
            # Groq (gsk_... keys)
            from groq import Groq
            client = Groq(api_key=key)
            resp = client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                max_tokens=800,
                temperature=0.2,
                timeout=settings.llm_timeout_secs,
            )
            text = resp.choices[0].message.content
            model_used = settings.groq_model
            tokens = resp.usage.total_tokens if resp.usage else None

        result = _parse_llm_response(text)
        result["llm_model"] = model_used
        result["llm_tokens_used"] = tokens
        return result

    except Exception as e:
        # Graceful fallback — never crash the user flow
        return _mock_diagnosis(payload)


def _mock_diagnosis(payload: dict) -> dict:
    error_text = payload.get("error_text", "").lower()
    if "wifi" in error_text or "network" in error_text or "internet" in error_text:
        return {
            "diagnosis": "A network connectivity issue was detected on your device.",
            "confidence": 0.72,
            "severity": "medium",
            "fix_steps": [
                "Click the Wi-Fi icon in the taskbar and disconnect from the current network.",
                "Wait 10 seconds, then reconnect to the corporate Wi-Fi.",
                "If the issue persists, open Settings > Network & Internet > Network Reset.",
                "Restart your device and try connecting again.",
            ],
            "kb_references": [{"id": "KB001", "title": "Wi-Fi Troubleshooting Guide", "url": "#"}],
            "suggested_group": "IT_Network",
            "action": "guided_fix",
            "llm_model": "mock",
        }
    if "password" in error_text or "login" in error_text or "locked" in error_text:
        return {
            "diagnosis": "Your account may be locked or your password has expired.",
            "confidence": 0.85,
            "severity": "high",
            "fix_steps": [
                "Go to the self-service portal at password.company.com.",
                "Click 'Unlock Account' or 'Reset Password'.",
                "Follow the on-screen steps to verify your identity.",
                "Once reset, try logging in again.",
            ],
            "kb_references": [{"id": "KB002", "title": "Password Reset Guide", "url": "#"}],
            "suggested_group": "IT_IAM",
            "action": "guided_fix",
            "llm_model": "mock",
        }
    if "slow" in error_text or "freeze" in error_text or "crash" in error_text:
        return {
            "diagnosis": "Your device is experiencing performance issues, possibly due to high CPU or memory usage.",
            "confidence": 0.68,
            "severity": "medium",
            "fix_steps": [
                "Press Ctrl+Shift+Esc to open Task Manager.",
                "Click the CPU or Memory column to find high-usage processes.",
                "Right-click any unnecessary process and select 'End Task'.",
                "Restart your device to clear cached memory.",
                "Run Windows Update to ensure all drivers are current.",
            ],
            "kb_references": [],
            "suggested_group": "IT_SD",
            "action": "guided_fix",
            "llm_model": "mock",
        }
    return {
        "diagnosis": "The issue could not be automatically identified from the description provided.",
        "confidence": 0.3,
        "severity": "medium",
        "fix_steps": [
            "Note any error codes or messages displayed on screen.",
            "Try restarting your device.",
            "If the issue persists, the Service Desk will assist you.",
        ],
        "kb_references": [],
        "suggested_group": "IT_SD",
        "action": "create_ticket",
        "llm_model": "mock",
    }


def _parse_llm_response(text: str) -> dict:
    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    fix_steps = [l for l in lines if l and (l[0].isdigit() or l.startswith("-"))]
    diagnosis = next((l for l in lines if not (l[0].isdigit() or l.startswith("-"))), lines[0] if lines else "")
    return {
        "diagnosis": diagnosis,
        "confidence": 0.65,
        "severity": "medium",
        "fix_steps": fix_steps,
        "kb_references": [],
        "suggested_group": "IT_SD",
        "action": "guided_fix",
    }


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _try_cache(key: str, value: dict):
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_async_cache(key, value))
    except Exception:
        pass


async def _async_cache(key: str, value: dict):
    try:
        redis = await get_redis()
        await redis.setex(key, 86400, json.dumps(value))
    except Exception:
        pass
