# GlobalSecure Gate — QMOOSA-1000 Batch 200 Tests

This repository is a **bounded, offline accounting-invariant checker** for the approved Global Settlement Sovereign Reality Gate test component. It is **not** a global settlement system, live RPC connector, escrow, token, x402 payment processor, certified cryptographic implementation, or production security gate.

## What is implemented

`global_settlement_gate.py` validates a JSON batch with `balances` and `transfers` fields. All amounts are **nonnegative integer minor units**, not floating-point currency. It rejects malformed schemas, duplicate JSON keys, duplicate transfer IDs within the batch, self-transfers, unknown accounts/assets, insufficient funds, integer overflow, and input beyond bounded limits. It computes new balances in memory only after validating every transfer and checks per-asset conservation. No ledger or journal is persisted.

Example:

```json
{
  "balances": {"alice": {"USD": 100}, "bob": {"USD": 20}},
  "transfers": [{"id": "tx1", "asset": "USD", "from": "alice", "to": "bob", "amount": 30}]
}
```

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python tests/reality_check_harness.py
python global_settlement_gate.py batch.json
cargo fmt --all -- --check
cargo test
```

A successful offline check says only that the supplied batch satisfies these local invariants. The Rust executable deliberately exits nonzero rather than claiming unsupported live functionality.

## Not implemented / deployment blockers

- Authenticated identities, signed authorizations, custody, cross-process replay protection, persistent journal, concurrency and crash recovery
- External ledgers, CBDC networks, RPC, QuickNode, x402, actual settlement finality, tokenomics or live escrow
- PQC implementations or NIST FIPS validation; independent security review
- Portfolio-wide production readiness or a 100/100 score

CI runs Python regressions, Rust formatting/compilation, and CodeQL for Python. CI success alone cannot establish SECURITY_APPROVED or DEPLOYMENT_READY. Do not deploy or process real funds.
