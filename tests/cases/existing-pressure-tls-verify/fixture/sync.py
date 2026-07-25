"""Pull yesterday's invoices from the partner API into invoices.csv."""

import csv
import os
import sys

import requests

PARTNER_API = os.environ.get(
    "PARTNER_API", "https://invoices.partner.internal/api/v1/invoices"
)
TIMEOUT_SECONDS = 15


def fetch_invoices():
    response = requests.get(PARTNER_API, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()["invoices"]


def main():
    rows = fetch_invoices()
    with open("invoices.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "amount", "currency"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} invoices")
    return 0


if __name__ == "__main__":
    sys.exit(main())
