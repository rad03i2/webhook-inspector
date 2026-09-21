# Contributing

Contributions are welcome when they keep Webhook Inspector small, local-first, testable, and safe.

1. Fork the repository and create a focused branch.
2. Use Python 3.10+ and avoid unnecessary runtime dependencies.
3. Install development requirements with `python -m pip install -e . pytest`.
4. Run `python -m pytest -q` before submitting changes.
5. Add tests for behavior changes and update both English and Arabic README sections when user-facing behavior changes.
6. Never commit webhook secrets, production payloads, tokens, local databases, or personal data.

Keep pull requests focused and explain the user-visible behavior, tests, and security implications.
