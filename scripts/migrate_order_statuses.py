"""One-off migration: normalize order statuses to pending or completed only."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from models import normalize_order_statuses, get_order_status_counts


def main() -> int:
    if normalize_order_statuses():
        counts = get_order_status_counts()
        print("Order statuses updated.")
        print(f"  Total:     {counts['total']}")
        print(f"  Pending:   {counts['pending']}")
        print(f"  Completed: {counts['completed']}")
        return 0
    print("Migration failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
