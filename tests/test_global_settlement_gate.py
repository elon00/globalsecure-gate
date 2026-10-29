"""Negative and positive tests for offline accounting invariants only."""

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from global_settlement_gate import GateError, MAX_MINOR_UNITS, parse_batch, validate_batch


class GlobalSettlementGateTests(unittest.TestCase):
    def setUp(self):
        self.batch = {"balances": {"alice": {"USD": 100}, "bob": {"USD": 20}},
                      "transfers": [{"id": "tx1", "asset": "USD", "from": "alice", "to": "bob", "amount": 30}]}

    def rejects(self, code):
        with self.assertRaisesRegex(GateError, code):
            validate_batch(self.batch)

    def test_valid_batch_and_no_mutation(self):
        original = copy.deepcopy(self.batch)
        self.assertEqual(validate_batch(self.batch), {"alice": {"USD": 70}, "bob": {"USD": 50}})
        self.assertEqual(self.batch, original)

    def test_empty_batch(self):
        self.batch["transfers"] = []
        self.assertEqual(validate_batch(self.batch), self.batch["balances"])

    def test_replay_id_rejected(self):
        self.batch["transfers"].append(dict(self.batch["transfers"][0]))
        self.rejects("INVALID_OR_REPLAYED_ID")

    def test_insufficient_funds(self):
        self.batch["transfers"][0]["amount"] = 101
        self.rejects("INSUFFICIENT_FUNDS")

    def test_negative_amount(self):
        self.batch["transfers"][0]["amount"] = -1
        self.rejects("INVALID_TRANSFER_AMOUNT")

    def test_zero_amount(self):
        self.batch["transfers"][0]["amount"] = 0
        self.rejects("INVALID_TRANSFER_AMOUNT")

    def test_boolean_amount(self):
        self.batch["transfers"][0]["amount"] = True
        self.rejects("INVALID_TRANSFER_AMOUNT")

    def test_self_transfer(self):
        self.batch["transfers"][0]["to"] = "alice"
        self.rejects("INVALID_TRANSFER_PARTICIPANTS")

    def test_unknown_account(self):
        self.batch["transfers"][0]["to"] = "eve"
        self.rejects("INVALID_TRANSFER_PARTICIPANTS")

    def test_unknown_asset(self):
        self.batch["transfers"][0]["asset"] = "EUR"
        self.rejects("UNKNOWN_ASSET")

    def test_overflow(self):
        self.batch["balances"]["bob"]["USD"] = MAX_MINOR_UNITS
        self.rejects("BALANCE_OVERFLOW")

    def test_extra_field(self):
        self.batch["transfers"][0]["signature"] = "pretend"
        self.rejects("INVALID_TRANSFER_SCHEMA")

    def test_duplicate_json_key(self):
        with self.assertRaisesRegex(GateError, "DUPLICATE_JSON_KEY"):
            parse_batch(b'{"balances":{},"balances":{},"transfers":[]}')

    def test_invalid_json(self):
        with self.assertRaisesRegex(GateError, "INVALID_JSON"):
            parse_batch(b'{bad json')

    def test_nonfinite_number(self):
        with self.assertRaisesRegex(GateError, "NONFINITE_NUMBER"):
            parse_batch(b'{"balances":{"a":{"USD":NaN}},"transfers":[]}')

    def test_oversized_input(self):
        with self.assertRaisesRegex(GateError, "INPUT_TOO_LARGE_OR_INVALID"):
            parse_batch(b" " * (1_048_576 + 1))

    def test_cli_accepts_valid_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.json"
            path.write_text(json.dumps(self.batch))
            result = subprocess.run([sys.executable, "global_settlement_gate.py", str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["scope"], "offline-accounting-invariants-only")

    def test_cli_rejects_invalid_batch(self):
        self.batch["transfers"][0]["amount"] = 9999
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "batch.json"
            path.write_text(json.dumps(self.batch))
            result = subprocess.run([sys.executable, "global_settlement_gate.py", str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("INSUFFICIENT_FUNDS", result.stderr)


if __name__ == "__main__":
    unittest.main()
