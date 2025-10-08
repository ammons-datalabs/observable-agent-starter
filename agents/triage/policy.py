# Put any routing heuristics or policies here if you want lightweight rules in front of the LLM.
def neutral_policy(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["invoice", "charge", "refund", "billing"]):
        return "billing"
    if any(w in t for w in ["error", "bug", "doesn't work", "crash", "api"]):
        return "tech"
    if any(w in t for w in ["pricing", "quote", "demo", "trial"]):
        return "sales"
    return "tech"  # default
