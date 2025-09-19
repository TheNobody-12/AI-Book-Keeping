from typing import List, Dict, Any
import os


def extract_transactions(file_path: str) -> List[Dict[str, Any]]:
    """
    MVP stub: parse uploaded file and return transactions.

    Replace this with Azure Document Intelligence (Form Recognizer) logic.
    For now, return a small, deterministic sample to unblock the frontend.
    """
    _ = os.path.basename(file_path)
    # Example structure aligned with Context/Schema.md transaction table
    return [
        {
            "date": "2025-08-02",
            "description": "STARBUCKS 1234",
            "deposits": None,
            "withdrawals": 5.60,
            "running_balance": None,
        },
        {
            "date": "2025-08-03",
            "description": "UBER *TRIP",
            "deposits": None,
            "withdrawals": 22.40,
            "running_balance": None,
        },
        {
            "date": "2025-08-05",
            "description": "WIRE IN ACME CORP",
            "deposits": 500.00,
            "withdrawals": None,
            "running_balance": None,
        },
    ]


def parse_form_recognizer_result(result: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Example mapper from Azure Document Intelligence result to normalized transaction rows.
    This is a placeholder. Adjust field paths to match your model output.
    """
    transactions: List[Dict[str, Any]] = []
    # Pseudocode:
    # for table in result.get("tables", []):
    #     for row in table.get("rows", []):
    #         transactions.append({
    #             "date": row.get("Date"),
    #             "description": row.get("Description"),
    #             "deposits": row.get("Deposits"),
    #             "withdrawals": row.get("Withdrawals"),
    #             "running_balance": row.get("RunningBalance"),
    #         })
    return transactions

