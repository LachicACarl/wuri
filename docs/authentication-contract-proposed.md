# WURI DSS Authentication Contract (Proposed — Not Implemented)

**Status:** DESIGN ONLY — SECURITY HOLD / NO-GO
**Purpose:** Define a reviewable server-side authentication boundary before implementation. No identity provider, session, API route, or credential store is configured by this document.

## 1. Non-negotiable requirements

- Use an approved identity provider or independently reviewed server-side identity implementation. Do not implement password handling in the React application.
- The browser must never decide whether a user is authenticated or authorized. React route guards are presentation only.
- Do not store passwords, session identifiers, refresh tokens, or bearer tokens in localStorage/sessionStorage.
- Prefer server-managed sessions in HttpOnly, Secure, appropriately SameSite cookies, with CSRF protection for state-changing requests.
- Enforce HTTPS in every non-local environment.
- Apply rate limits and abuse monitoring to login, recovery, and session endpoints.
- Use generic authentication errors that do not disclose whether an account exists.
- Record security-relevant events without recording passwords, cookies, tokens, recovery codes, or secrets.
- Require multi-factor authentication for privileged accounts if mandated by the institution's security policy.

## 2. Proposed endpoint surface

| Method | Path | Purpose | Access |
|---|---|---|---|
| GET | /api/auth/session | Return current authenticated user's minimal profile and memberships | Valid session |
| POST | /api/auth/login | Begin identity-provider login or server-managed session | Public, rate limited |
| POST | /api/auth/logout | Revoke current session | Valid session |
| POST | /api/auth/refresh | Refresh session if supported by approved provider | Valid session, CSRF protected |
| POST | /api/auth/recovery | Begin account recovery using approved provider flow | Public, rate limited |

The exact provider flow may use redirects, PKCE, or provider SDK endpoints instead of these literal routes. Do not create duplicate credential systems merely to match this proposal.

## 3. Session response (illustrative shape)

```json
{
  "authenticated": true,
  "user": { "id": "provider-issued-opaque-id", "display_name": "Verified account display name" },
  "memberships": [{ "institution_id": "opaque-institution-id", "role": "evaluator" }],
  "session_expires_at": "RFC-3339 timestamp"
}
```

This example is a shape illustration, not a real user, credential, or active session. Do not include secrets or provider tokens in the response.

## 4. Authorization decision

For every protected request, the server must:
1. Validate the session cryptographically or through the approved provider.
2. Resolve the user and active institution membership from trusted server-side records.
3. Check the required role and resource-level institution ownership.
4. Check whether the requested action is permitted in the current research/operational approval state.
5. Deny by default when identity, membership, role, institution, or approval cannot be established.
6. Write a redacted audit event for privileged actions and authorization failures as policy requires.

Proposed roles: administrator, evaluator, viewer. Role assignment must be performed through a controlled administrative process and must not be accepted from client request bodies.

## 5. Cookie and browser protections

- Session cookie: opaque, unpredictable, server-revocable; set HttpOnly, Secure, and an approved SameSite policy.
- Cookie path/domain must be as narrow as practical.
- Rotate session identifiers after authentication and privilege changes.
- Revoke sessions when an account is disabled, membership is removed, a role is downgraded, or a suspected compromise is handled; define whether a role upgrade also forces re-authentication.
- Define single-session versus multi-session policy, administrative session revocation, and the maximum revocation propagation delay.
- Ensure password/identity-provider recovery and security-factor changes invalidate or re-verify active sessions according to the selected provider's capabilities.
- Expire idle and absolute sessions according to institutional policy.
- Protect state-changing cookie-authenticated requests against CSRF; validate origin/referer as defense in depth.
- Configure CORS to exact approved origins; never combine credentialed requests with wildcard origins.
- Avoid exposing detailed authentication provider errors to the browser.

## 6. Session lifecycle decisions required before implementation

The following are mandatory design decisions, not assumptions supplied by this proposal:

- Absolute and idle session lifetimes, including privileged-account policy.
- Whether refresh-token/session rotation is supported and how reuse is detected.
- Session revocation behavior on role/membership changes, account disablement, password reset, and suspected compromise.
- Administrative visibility and revocation of active sessions without exposing session secrets.
- Behavior when the identity provider is unavailable, including fail-closed behavior for protected operations.

These values must be approved by the institution and documented against the chosen identity provider before coding.

## 7. Error behavior

- 401: no valid authenticated session.
- 403: authenticated but not authorized for the requested action/resource.
- 429: rate limit reached; include a safe retry policy where appropriate.
- 5xx: generic service failure with a request identifier; no stack traces or secret values.

The exact error envelope and provider-specific behavior must be finalized with the API contract.

## 8. Frontend integration expectations

Until an approved backend exists:
- Keep the workspace locked.
- Do not display a credential form that cannot authenticate.
- Do not accept a frontend boolean as proof of login.
- Do not store a fabricated user or demo session.
- Do not enable upload, assessment, evidence, or history routes based solely on client state.

After approval, the frontend may call the session endpoint to render authenticated state, but every protected backend route remains authoritative.

## 9. Required review and approvals

Before implementation:
- independent security review of the suspicious repository history and exact target commit;
- confirmation from the authorized provider owner that exposed credentials have been revoked/contained;
- identity-provider and session threat-model review;
- written implementation authorization for a named isolated branch and exact scope;
- separate runtime authorization for dependency installation and testing;
- privacy/security approval for account data and audit retention.

**This document does not authorize identity-provider configuration, credential rotation, database access, code implementation, dependency installation, tests, or deployment.**