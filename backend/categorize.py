from typing import List, Dict, Any, Optional


DEFAULT_CATEGORIES = [
    "Meals & Entertainment",
    "Travel",
    "Office Supplies",
    "Software & Subscriptions",
    "Utilities",
    "Income",
    "Transfers",
    "Other",
]


KEYWORD_MAP = {
    "STARBUCKS": "Meals & Entertainment",
    "UBER": "Travel",
    "LYFT": "Travel",
    "AMZN": "Office Supplies",
    "AMAZON": "Office Supplies",
    "MICROSOFT": "Software & Subscriptions",
    "SUBSCRIPTION": "Software & Subscriptions",
    "WIRE IN": "Income",
    "ACH IN": "Income",
    "TRANSFER": "Transfers",
}


def categorize_transactions(
    transactions: List[Dict[str, Any]],
    *,
    categories: Optional[List[str]] = None,
    use_llm: bool = False,
) -> List[Dict[str, Any]]:
    """
    MVP categorization: simple keyword heuristics.
    If use_llm=True, wire this to Azure OpenAI later.
    Returns list of {category, confidence, rationale} matching the input order.
    """
    cats = categories or DEFAULT_CATEGORIES

    results: List[Dict[str, Any]] = []

    for tx in transactions:
        desc = (tx.get("description") or "").upper()
        matched: Optional[str] = None
        for kw, cat in KEYWORD_MAP.items():
            if kw in desc:
                if cat in cats:
                    matched = cat
                    break
        if matched is None:
            # Simple rule: deposits default to Income if positive
            deposits = tx.get("deposits")
            withdrawals = tx.get("withdrawals")
            if deposits and float(deposits) > 0 and "Income" in cats:
                matched = "Income"
            else:
                matched = "Other" if "Other" in cats else cats[0]

        results.append(
            {
                "category": matched,
                "confidence": 0.65 if matched != "Other" else 0.4,
                "rationale": "Keyword/amount-based heuristic (MVP)",
            }
        )

    # Placeholder: if use_llm, this is where you'd call Azure OpenAI
    # and merge/override results with LLM predictions.
    return results


def build_llm_prompt(transactions: List[Dict[str, Any]], categories: List[str]) -> str:
    return (
        "Categorize the following transactions into one of these categories: "
        + ", ".join(categories)
        + ".\nReturn JSON list with objects {category, confidence, rationale}.\n\nTransactions:\n"
        + str(transactions)
    )

