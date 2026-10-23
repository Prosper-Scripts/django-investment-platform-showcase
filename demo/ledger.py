"""An in-memory, educational request ledger using synthetic data only.

This is independently authored portfolio code, not the client application.
It must not be used to manage real funds.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from typing import Literal


MoneyInput = Decimal | str | int
Kind = Literal["deposit", "withdrawal"]
Status = Literal["pending", "approved", "rejected"]
CENT = Decimal("0.01")
ZERO = Decimal("0.00")


class LedgerError(ValueError):
    """An invalid request or state transition."""


@dataclass(frozen=True)
class Request:
    reference: str
    kind: Kind
    amount: Decimal
    status: Status = "pending"


@dataclass(frozen=True)
class AuditEvent:
    sequence: int
    reference: str
    action: str
    amount: Decimal


def valid_amount(value: MoneyInput) -> Decimal:
    """Validate a positive, finite amount with no more than two decimals."""
    if isinstance(value, bool) or isinstance(value, float):
        raise LedgerError("Use Decimal, string, or integer amounts, not floats")
    if not isinstance(value, (Decimal, str, int)):
        raise LedgerError("Unsupported amount type")
    try:
        amount = Decimal(str(value))
        if not amount.is_finite() or amount <= ZERO or amount != amount.quantize(CENT):
            raise LedgerError("Amount must be finite, positive, and have at most two decimals")
    except (InvalidOperation, ValueError) as exc:
        if isinstance(exc, LedgerError):
            raise
        raise LedgerError("Invalid monetary amount") from exc
    return amount.quantize(CENT)


class ReviewLedger:
    """Single-account model for demonstrations and unit tests only."""

    def __init__(self) -> None:
        self._balance = ZERO
        self._requests: dict[str, Request] = {}
        self._events: list[AuditEvent] = []

    @property
    def approved_balance(self) -> Decimal:
        return self._balance

    @property
    def reserved_for_withdrawals(self) -> Decimal:
        return sum(
            (
                item.amount
                for item in self._requests.values()
                if item.kind == "withdrawal" and item.status == "pending"
            ),
            ZERO,
        )

    @property
    def available_balance(self) -> Decimal:
        return self._balance - self.reserved_for_withdrawals

    @property
    def events(self) -> tuple[AuditEvent, ...]:
        return tuple(self._events)

    def request(self, reference: str) -> Request:
        try:
            return self._requests[reference]
        except KeyError as exc:
            raise LedgerError("Unknown request reference") from exc

    def _record(self, reference: str, action: str, amount: Decimal) -> None:
        self._events.append(AuditEvent(len(self._events) + 1, reference, action, amount))

    def _new(self, reference: str, kind: Kind, amount: MoneyInput) -> Request:
        if not isinstance(reference, str) or not reference.strip():
            raise LedgerError("Reference must be a nonempty string")
        if reference in self._requests:
            raise LedgerError("Duplicate request reference")
        money = valid_amount(amount)
        if kind == "withdrawal" and money > self.available_balance:
            raise LedgerError("Insufficient available balance")
        entry = Request(reference, kind, money)
        self._requests[reference] = entry
        self._record(reference, f"{kind}_requested", money)
        return entry

    def request_deposit(self, reference: str, amount: MoneyInput) -> Request:
        return self._new(reference, "deposit", amount)

    def request_withdrawal(self, reference: str, amount: MoneyInput) -> Request:
        return self._new(reference, "withdrawal", amount)

    def decide(self, reference: str, *, approve: bool) -> Request:
        entry = self.request(reference)
        if entry.status != "pending":
            raise LedgerError("Only pending requests may be reviewed")
        if approve:
            if entry.kind == "deposit":
                self._balance += entry.amount
            else:
                self._balance -= entry.amount
        updated = replace(entry, status="approved" if approve else "rejected")
        self._requests[reference] = updated
        self._record(reference, updated.status, entry.amount)
        return updated
