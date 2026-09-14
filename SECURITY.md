# Security Policy

## Purpose

ZeroGate is a cybersecurity hackathon project and Zero Trust Network Access (ZTNA) simulation platform.

It demonstrates:

- Context-aware access control
- Risk-based authorization
- Adaptive MFA
- Policy enforcement
- Microsegmentation
- Auditability

## Reporting a Security Issue

If you discover a security issue in this project, please avoid publicly disclosing sensitive details before the issue can be reviewed.

For hackathon and demonstration deployments, security issues should be reported to the project maintainers through the repository's private communication channels where available.

## Demo Credentials

The credentials documented in the README are intended only for local demonstration.

They must not be reused in production environments.

## Secrets

Do not commit sensitive information such as:

- `.env` files
- JWT secrets
- Production passwords
- Database credentials
- API keys
- Cloud credentials
- Private certificates

Use environment variables or an appropriate secret-management solution.

## Production Disclaimer

ZeroGate is a simulation and demonstration platform.

It should not be deployed as a production ZTNA gateway without additional security review, hardened infrastructure, production identity integration, secure secret management, monitoring, and penetration testing.
