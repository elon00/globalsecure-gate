# Security and Limitations

This repository currently implements only bounded offline accounting invariants. It does **not** implement, test or certify NIST FIPS 203, FIPS 204, FIPS 205, cryptographic signing, cross-chain finality, custody, escrow, or settlement authorization.

Known gaps: replay protection is only within one input batch, no durable transaction journal, no concurrency control, no authenticated caller, no cross-ledger reconciliation, no independent audit. Never process real funds with this code.

Report suspected vulnerabilities through GitHub's private vulnerability reporting feature if enabled, or open a minimal issue without including secrets or exploit data. No bug-bounty promise or private contact address is asserted here.

**Security acceptance: NOT APPROVED. Deployment readiness: NOT APPROVED.**
