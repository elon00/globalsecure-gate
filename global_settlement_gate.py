"""Bounded offline accounting-invariant checker; NOT a settlement or security certificate."""

import json
import re
import sys
from pathlib import Path

MAX_MINOR_UNITS = (1 << 63) - 1
MAX_JSON_BYTES = 1_048_576
MAX_ACCOUNTS = 1000
MAX_ASSETS = 32
MAX_TRANSFERS = 1000
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}\Z")


class GateError(ValueError):
    """Fail-closed validation error."""


def _require(condition, code):
    if not condition:
        raise GateError(code)


def _identifier(value):
    return isinstance(value, str) and IDENTIFIER.fullmatch(value) is not None


def _integer(value, *, positive=False):
    return type(value) is int and (0 < value <= MAX_MINOR_UNITS if positive else 0 <= value <= MAX_MINOR_UNITS)


def _exact_keys(obj, required):
    return type(obj) is dict and set(obj) == set(required)


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, "DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def parse_batch(data: bytes):
    _require(type(data) is bytes and len(data) <= MAX_JSON_BYTES, "INPUT_TOO_LARGE_OR_INVALID")
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_unique_pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(GateError("NONFINITE_NUMBER")))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise GateError("INVALID_JSON") from exc


def validate_batch(batch):
    """Return new balances only if all transfers satisfy bounded offline invariants."""
    _require(_exact_keys(batch, {"balances", "transfers"}), "INVALID_BATCH_SCHEMA")
    initial, transfers = batch["balances"], batch["transfers"]
    _require(type(initial) is dict and 0 < len(initial) <= MAX_ACCOUNTS, "INVALID_ACCOUNTS")
    _require(type(transfers) is list and len(transfers) <= MAX_TRANSFERS, "INVALID_TRANSFERS")
    balances = {}
    assets = set()
    for account, holdings in initial.items():
        _require(_identifier(account) and type(holdings) is dict and 0 < len(holdings) <= MAX_ASSETS,
                 "INVALID_ACCOUNT_OR_HOLDINGS")
        balances[account] = {}
        for asset, value in holdings.items():
            _require(_identifier(asset) and _integer(value), "INVALID_ASSET_OR_BALANCE")
            balances[account][asset] = value
            assets.add(asset)
    _require(len(assets) <= MAX_ASSETS, "TOO_MANY_ASSETS")
    totals = {asset: sum(holdings.get(asset, 0) for holdings in balances.values()) for asset in assets}
    seen = set()
    for transfer in transfers:
        _require(_exact_keys(transfer, {"id", "asset", "from", "to", "amount"}), "INVALID_TRANSFER_SCHEMA")
        txid, asset, source, target, amount = (transfer[k] for k in ("id", "asset", "from", "to", "amount"))
        _require(_identifier(txid) and txid not in seen, "INVALID_OR_REPLAYED_ID")
        seen.add(txid)
        _require(_identifier(asset) and asset in assets, "UNKNOWN_ASSET")
        _require(_identifier(source) and _identifier(target) and source != target and
                 source in balances and target in balances, "INVALID_TRANSFER_PARTICIPANTS")
        _require(_integer(amount, positive=True), "INVALID_TRANSFER_AMOUNT")
        available = balances[source].get(asset, 0)
        receiving = balances[target].get(asset, 0)
        _require(available >= amount, "INSUFFICIENT_FUNDS")
        _require(receiving <= MAX_MINOR_UNITS - amount, "BALANCE_OVERFLOW")
        balances[source][asset] = available - amount
        balances[target][asset] = receiving + amount
    _require(all(sum(h.get(a, 0) for h in balances.values()) == total
                 for a, total in totals.items()), "ASSET_CONSERVATION_FAILURE")
    return balances


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("usage: python global_settlement_gate.py BATCH.json", file=sys.stderr)
        return 2
    try:
        path = Path(argv[0])
        _require(path.is_file() and path.stat().st_size <= MAX_JSON_BYTES, "INPUT_FILE_INVALID_OR_TOO_LARGE")
        result = validate_batch(parse_batch(path.read_bytes()))
    except (GateError, OSError) as exc:
        print(f"OFFLINE_GATE_REJECTED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": "PASS", "scope": "offline-accounting-invariants-only", "balances": result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
