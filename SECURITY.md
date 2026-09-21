# Security Policy

## Scope
Webhook Inspector is a local developer tool. It listens on `127.0.0.1` by default and stores captured headers and bodies in a local SQLite database.

## Safe use
- Treat captured webhook data as sensitive: payloads and headers may contain tokens or personal data.
- Do not expose the receiver to an untrusted network without an authenticated reverse proxy and network controls.
- Keep signing secrets in environment variables; never place them in commands, source code, examples, or commits.
- Review an event before replaying it. Replay sends the captured body and most original headers to the destination.
- Delete or prune captures when they are no longer needed.

## Reporting
Please report suspected vulnerabilities privately through GitHub's security reporting facilities when available. Do not publish credentials or real captured webhook payloads in an issue.
