"""Run a fully synthetic example using the educational ledger."""

from .ledger import ReviewLedger


def main() -> None:
    ledger = ReviewLedger()
    ledger.request_deposit("DEMO-001", "1250.00")
    ledger.decide("DEMO-001", approve=True)
    ledger.request_withdrawal("DEMO-002", "175.50")
    print("Approved balance:", ledger.approved_balance)
    print("Available balance:", ledger.available_balance)
    print("Pending withdrawal reserved:", ledger.reserved_for_withdrawals)
    ledger.decide("DEMO-002", approve=True)
    print("After review:", ledger.approved_balance)
    print("Audit events:", len(ledger.events))


if __name__ == "__main__":
    main()
