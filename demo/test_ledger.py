"""Unit tests of independent example code, not the client system."""

import unittest
from decimal import Decimal

from demo.ledger import LedgerError, ReviewLedger, valid_amount


class AmountTests(unittest.TestCase):
    def test_exact_decimal_amounts(self) -> None:
        self.assertEqual(valid_amount("12.30"), Decimal("12.30"))

    def test_reject_binary_floats(self) -> None:
        with self.assertRaises(LedgerError):
            valid_amount(0.1)

    def test_reject_nonfinite_zero_and_excess_precision(self) -> None:
        for amount in ("NaN", "Infinity", "0", "-1", "12.345", "not money"):
            with self.subTest(amount=amount), self.assertRaises(LedgerError):
                valid_amount(amount)


class ReviewLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ledger = ReviewLedger()

    def fund(self, amount: str = "100.00") -> None:
        self.ledger.request_deposit("deposit-1", amount)
        self.ledger.decide("deposit-1", approve=True)

    def test_pending_deposit_is_not_spendable(self) -> None:
        self.ledger.request_deposit("deposit-1", "100.00")
        self.assertEqual(self.ledger.available_balance, Decimal("0.00"))

    def test_approved_deposit_increases_balance(self) -> None:
        self.fund()
        self.assertEqual(self.ledger.approved_balance, Decimal("100.00"))

    def test_rejected_deposit_does_not_increase_balance(self) -> None:
        self.ledger.request_deposit("deposit-1", "100.00")
        self.ledger.decide("deposit-1", approve=False)
        self.assertEqual(self.ledger.approved_balance, Decimal("0.00"))

    def test_pending_withdrawal_reserves_funds(self) -> None:
        self.fund()
        self.ledger.request_withdrawal("withdraw-1", "65.50")
        self.assertEqual(self.ledger.available_balance, Decimal("34.50"))
        self.assertEqual(self.ledger.approved_balance, Decimal("100.00"))

    def test_second_withdrawal_cannot_exceed_unreserved_balance(self) -> None:
        self.fund()
        self.ledger.request_withdrawal("withdraw-1", "80.00")
        with self.assertRaises(LedgerError):
            self.ledger.request_withdrawal("withdraw-2", "30.00")
        self.assertEqual(self.ledger.available_balance, Decimal("20.00"))
        self.assertEqual(len(self.ledger.events), 3)

    def test_approved_withdrawal_reduces_booked_balance_once(self) -> None:
        self.fund()
        self.ledger.request_withdrawal("withdraw-1", "75.00")
        self.ledger.decide("withdraw-1", approve=True)
        self.assertEqual(self.ledger.approved_balance, Decimal("25.00"))
        self.assertEqual(self.ledger.reserved_for_withdrawals, Decimal("0.00"))

    def test_rejection_releases_reservation(self) -> None:
        self.fund()
        self.ledger.request_withdrawal("withdraw-1", "75.00")
        self.ledger.decide("withdraw-1", approve=False)
        self.assertEqual(self.ledger.available_balance, Decimal("100.00"))

    def test_duplicate_reference_cannot_create_another_request(self) -> None:
        self.fund()
        with self.assertRaises(LedgerError):
            self.ledger.request_deposit("deposit-1", "100.00")

    def test_final_decision_cannot_be_repeated(self) -> None:
        self.fund()
        with self.assertRaises(LedgerError):
            self.ledger.decide("deposit-1", approve=True)

    def test_audit_events_have_sequential_numbers(self) -> None:
        self.fund()
        self.assertEqual([e.sequence for e in self.ledger.events], [1, 2])

    def test_negative_withdrawal_does_not_modify_state(self) -> None:
        self.fund()
        before = (self.ledger.available_balance, len(self.ledger.events))
        with self.assertRaises(LedgerError):
            self.ledger.request_withdrawal("withdraw-invalid", "-10")
        self.assertEqual((self.ledger.available_balance, len(self.ledger.events)), before)


if __name__ == "__main__":
    unittest.main()
