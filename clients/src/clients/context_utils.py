
from pydantic_ai import RunContext
from typing import List, Optional

MISSING_PHRASES = [
    "i did not find any information",
    "jag hittade ingen information",
]

def find_matching_phrases(text: str) -> List[str]:
    txt = (text or "").lower()
    return [p for p in MISSING_PHRASES if p in txt]

def extract_user_query_from_ctx(ctx: Optional[RunContext]) -> str:
    """Try several plausible locations in ctx to find the original user query."""
    if not ctx:
        return ""

    try:
        req = getattr(ctx, "request", None) or getattr(ctx, "model_request", None)
        if req is not None:
            parts = getattr(req, "parts", None)
            if parts:
                for p in parts:
                    if getattr(p, "part_kind", "") == "user-prompt":
                        return getattr(p, "content", "") or getattr(p, "text", "") or ""
                # fallback: join all user-like parts
                texts = [getattr(p, "content", "") or getattr(p, "text", "") for p in parts
                         if getattr(p, "part_kind", "") in {"user-prompt", "text"}]
                joined = " ".join([t for t in texts if t])
                if joined:
                    return joined
            # some versions have `.prompt` or `.input`
            if getattr(req, "prompt", None):
                return req.prompt
            if getattr(req, "input", None):
                return req.input
    except Exception:
        pass

    try:
        msgs = getattr(ctx, "message_history", None) or getattr(ctx, "messages", None)
        if msgs:
            # iterate backwards to find latest user prompt
            for m in reversed(msgs):
                parts = getattr(m, "parts", None)
                if parts:
                    for p in parts:
                        if getattr(p, "part_kind", "") == "user-prompt":
                            return getattr(p, "content", "") or getattr(p, "text", "") or ""
    except Exception:
        pass

    try:
        deps = getattr(ctx, "deps", None)
        if isinstance(deps, dict):
            for k in ("user_input", "input", "query", "prompt"):
                if k in deps:
                    return deps[k]
    except Exception:
        pass
    
    return ""
