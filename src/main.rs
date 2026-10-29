// This Rust binary is not a settlement engine. Keep its CLI fail-closed.
// The bounded offline invariant implementation is global_settlement_gate.py.
fn main() {
    eprintln!("UNSUPPORTED: no live settlement, PQC, RPC or escrow verification is implemented");
    eprintln!("Run: python -m unittest discover -s tests -p 'test_*.py' -v");
    std::process::exit(2);
}
