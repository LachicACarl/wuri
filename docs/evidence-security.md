# Evidence security requirements

Research dataset creation and approval fail closed for registered
institutional documents unless all three document states are `verified`:

- institutional authorization;
- permission for research use; and
- document review.

The checks run in the database/service layer during dataset creation and
again inside the approval transaction. A later change to a document's
permission or review state therefore prevents approval of a submitted
dataset. Inline text without a registered source document remains a
synthetic/candidate-data path and cannot satisfy institutional provenance
requirements for approval.

Session cookies use `Secure` by default. An insecure cookie is permitted only
when both `SESSION_COOKIE_SECURE=false` and
`WURI_ENVIRONMENT=development` are explicitly configured. Production
deployments must use HTTPS and retain the secure default. The application
does not independently verify DUAs, legal source rights, ethics approval, or
malware safety; those remain deployment and institutional controls.
