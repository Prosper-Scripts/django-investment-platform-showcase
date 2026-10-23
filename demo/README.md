# Independent Python example: request-based ledger

This is a **newly written educational example**, not a copy of the client application. It models one fictional account, a balance, pending requests, and an audit event list.

```bash
python -m unittest discover -s demo -p "test_*.py" -v
python -m demo.example
```

Use Python 3.11+. No dependencies are required.

The ledger runs in memory and is single-process. It has **no** authentication, persistent database, transactional locking, concurrency protection, payment integration, return calculation, or compliance framework. It must not manage real funds.
