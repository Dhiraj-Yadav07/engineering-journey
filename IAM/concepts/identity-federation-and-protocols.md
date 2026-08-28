# Identity Federation and Authentication Protocols

> **Deep-study notes:** SAML vs OAuth 2.0 vs OIDC, tokens, sessions,
> federation, security, enterprise architecture, and interview
> preparation.
>
> **Goal:** Understand *why* these protocols exist, *what problem each
> solves*, *how the flows work*, and *how to choose between them*.

------------------------------------------------------------------------

## Table of Contents

1.  [Identity Fundamentals](#1-identity-fundamentals)
2.  [SAML](#2-saml)
3.  [OAuth 20](#3-oauth-20)
4.  [OIDC](#4-oidc)
5.  [Tokens](#5-tokens)
6.  [Sessions](#6-sessions)
7.  [Federation Architecture](#7-federation-architecture)
8.  [SAML vs OAuth 20 vs OIDC](#8-saml-vs-oauth-20-vs-oidc)
9.  [Security Considerations](#9-security-considerations)
10. [Real-World Scenarios](#10-real-world-scenarios)
11. [Common Misconceptions](#11-common-misconceptions)
12. [Interview / Architecture
    Questions](#12-interview--architecture-questions)
13. [Quick Reference Cheat Sheet](#13-quick-reference-cheat-sheet)

------------------------------------------------------------------------

# 1. Identity Fundamentals

## 1.1 The Big Picture

Before learning SAML, OAuth 2.0, and OIDC, separate these four concepts:

``` text
                         IDENTITY
                            |
          +-----------------+------------------+
          |                 |                  |
          v                 v                  v
   Authentication    Authorization       Federation / SSO
          |                 |                  |
          v                 v                  v
     "Who are you?"   "What can you do?"   "Who trusts whom?"
```

A large percentage of IAM confusion comes from mixing these concepts.

------------------------------------------------------------------------

## 1.2 Authentication

**Authentication = proving an identity.**

Examples:

-   Username + password
-   Password + MFA
-   Passkey
-   Security key
-   Client certificate
-   Enterprise Identity Provider login

Example:

``` text
Alice
  |
  | username + password + MFA
  v
Identity Provider
  |
  | verifies credentials
  v
"Alice is authenticated"
```

Authentication answers:

> **WHO are you?**

### Authentication is not authorization

After Alice authenticates, the system still needs to decide what Alice
can do.

``` text
Alice
  |
  | Authentication
  v
Alice is authenticated
  |
  | Authorization
  v
Alice may read reports
Alice may NOT approve payments
```

------------------------------------------------------------------------

## 1.3 Authorization

**Authorization = determining what an authenticated principal is allowed
to do.**

Examples:

``` text
Alice
  |
  +--> reports.read       YES
  +--> reports.write      YES
  +--> payments.approve   NO
  +--> users.delete       NO
```

Authorization can be based on:

-   Roles
-   Groups
-   Scopes
-   Attributes
-   Policies
-   Resource ownership
-   Context such as device, location, risk, time

A useful mental model:

``` text
Authentication
      ↓
Identity
      ↓
Authorization
      ↓
Permissions
      ↓
Action
```

------------------------------------------------------------------------

## 1.4 Identity Provider (IdP)

An **Identity Provider** is a system that establishes or brokers
identity.

Typical enterprise IdP responsibilities include:

-   User authentication
-   MFA
-   Session management
-   Credential policies
-   Identity claims
-   Token/assertion issuance
-   Federation with applications

Conceptually:

``` text
                  +----------------------+
                  |    Identity Provider |
                  |                      |
                  | Users                |
                  | Authentication       |
                  | MFA                  |
                  | Tokens / Assertions  |
                  +----------+-----------+
                             |
                             v
                         Applications
```

Examples include enterprise identity platforms such as Microsoft Entra
ID, Okta, Ping Identity, and similar systems.

------------------------------------------------------------------------

## 1.5 Service Provider (SP)

In SAML terminology, the application receiving the identity assertion is
commonly called the **Service Provider (SP)**.

Example:

``` text
Corporate IdP
      |
      | SAML Assertion
      v
Salesforce
      ^
      |
      SP
```

The SP trusts the IdP according to configured federation metadata,
certificates, identifiers, endpoints, and policy.

------------------------------------------------------------------------

## 1.6 Relying Party (RP)

In OIDC terminology, the application relying on an OpenID Provider's
authentication result is called the **Relying Party (RP)**.

``` text
OIDC Provider
      |
      | ID Token / authentication result
      v
Application
      ^
      |
      RP
```

### SAML vs OIDC terminology

``` text
SAML                    OIDC
----                    ----
Identity Provider       OpenID Provider
Service Provider        Relying Party
SAML Assertion          ID Token
```

The terms differ, but the architectural idea is similar: one party
establishes identity and another party relies on that result.

------------------------------------------------------------------------

## 1.7 Single Sign-On (SSO)

**SSO means a user can authenticate through a central identity system
and then access multiple applications without separately entering
credentials into each application.**

Example:

``` text
                         Corporate IdP
                              |
                 User authenticates once
                              |
          +-------------------+-------------------+
          |                   |                   |
          v                   v                   v
      Salesforce          ServiceNow          Workday
          |                   |                   |
        Session             Session             Session
```

SSO is primarily a **user experience / authentication architecture**.

The underlying federation protocol can be SAML, OIDC, or another
mechanism.

------------------------------------------------------------------------

## 1.8 Federation

**Federation = establishing trust between separate identity/security
domains.**

Imagine:

``` text
Company A                           SaaS Company B
----------                          -------------
Corporate IdP  ------------------>  SaaS Application
                 Federation Trust
```

Company B does not need to become the authoritative source of Company
A's employee passwords.

Instead, Company B trusts identity information issued by Company A's
IdP.

### Federation vs SSO

They are related but not identical.

``` text
Federation
    |
    +--> Trust relationship between security domains

SSO
    |
    +--> User can access multiple applications after authentication
```

Federation is often the mechanism used to implement cross-domain SSO.

------------------------------------------------------------------------

## 1.9 A Complete Identity Journey

Consider Alice accessing an enterprise application:

``` text
Alice
  |
  | 1. Open application
  v
Application
  |
  | 2. "I need authenticated identity"
  v
Corporate IdP
  |
  | 3. Authenticate Alice + MFA
  v
Identity established
  |
  | 4. Assertion / tokens
  v
Application
  |
  | 5. Validate identity result
  v
Application session
  |
  | 6. Authorization
  v
Allowed actions
```

The protocols discussed later mainly define the communication between
steps 3, 4, and 5.

------------------------------------------------------------------------

# 2. SAML

## 2.1 What Is SAML?

**SAML = Security Assertion Markup Language.**

SAML 2.0 is widely used for enterprise identity federation and
browser-based SSO.

The core idea:

> An Identity Provider authenticates a user and sends an assertion to a
> Service Provider.

``` text
User
 |
 v
Identity Provider
 |
 | signed SAML Assertion
 v
Service Provider
 |
 v
Application Session
```

SAML is XML-based and commonly encountered in established enterprise
SaaS environments.

------------------------------------------------------------------------

## 2.2 Why SAML Exists

Before centralized federation, each application might maintain its own
credentials:

``` text
Alice
 |
 +--> Application A password
 +--> Application B password
 +--> Application C password
 +--> Application D password
```

This creates:

-   Password proliferation
-   Duplicate user stores
-   Difficult offboarding
-   Inconsistent authentication policies
-   Poor centralized MFA control

Federation changes the model:

``` text
                    Corporate IdP
                         |
        +----------------+----------------+
        |                |                |
        v                v                v
       App A            App B            App C
```

The organization centralizes authentication.

------------------------------------------------------------------------

## 2.3 SAML Components

### Principal

The user being represented.

``` text
Alice
```

### Identity Provider (IdP)

Authenticates Alice.

``` text
Corporate IdP
```

### Service Provider (SP)

The application Alice wants to access.

``` text
Salesforce
```

### SAML Assertion

The IdP's signed statement about Alice.

Conceptually:

``` text
+------------------------------------------------+
| SAML Assertion                                 |
+------------------------------------------------+
| Issuer: Corporate-IdP                          |
| Subject: alice@example.com                     |
| Audience: Salesforce                            |
| Authn: Password + MFA                          |
| Validity: 10:00 - 10:05                       |
| Attributes:                                    |
|   department = Engineering                     |
|   role = Developer                             |
| Signature: IdP signature                       |
+------------------------------------------------+
```

This is simplified. Real SAML messages contain structured XML elements,
namespaces, conditions, bindings, and signatures.

------------------------------------------------------------------------

## 2.4 SAML Assertion Types of Information

A SAML assertion can contain different statements.

Conceptually:

``` text
SAML Assertion
 |
 +--> Authentication Statement
 |      |
 |      +--> How/when user authenticated
 |
 +--> Attribute Statement
 |      |
 |      +--> department
 |      +--> role
 |      +--> email
 |
 +--> Authorization-related information
```

The exact elements and profiles used depend on the SAML deployment.

------------------------------------------------------------------------

## 2.5 SAML SP-Initiated Flow

This is the classic enterprise SSO flow.

### Scenario

Alice visits:

``` text
https://sales.example.com
```

Salesforce is configured as a SAML SP.

### Flow

``` text
 Alice
   |
   | 1. GET application
   v
+---------+
|   SP    |
+----+----+
     |
     | 2. SAML AuthnRequest
     v
+---------+
|   IdP   |
+----+----+
     |
     | 3. Login / MFA
     v
   Alice
     |
     | 4. Authentication succeeds
     v
+---------+
|   IdP   |
+----+----+
     |
     | 5. Signed SAML Response
     |    containing Assertion
     v
+---------+
|   SP    |
+----+----+
     |
     | 6. Validate assertion
     | 7. Map identity
     | 8. Create local session
     v
 Alice logged in
```

The key sequence is:

``` text
SP → IdP → SP
```

------------------------------------------------------------------------

## 2.6 What Happens Inside the SP

After receiving the SAML response:

``` text
SAML Response
     |
     v
Parse XML
     |
     v
Validate XML signature
     |
     v
Validate trusted issuer
     |
     v
Validate audience
     |
     v
Validate time conditions
     |
     v
Validate recipient/destination
     |
     v
Validate subject
     |
     v
Check replay protections
     |
     v
Map user / attributes
     |
     v
Create application session
```

This is a critical architecture concept:

> The SAML assertion does not necessarily become the application's
> session.

Usually:

``` text
SAML Assertion
      ↓
Application validates it
      ↓
Application creates its own session
      ↓
Browser receives session cookie
```

------------------------------------------------------------------------

## 2.7 SAML IdP-Initiated Flow

Here the user starts at the IdP.

Example:

``` text
Alice
  |
  | 1. Login to corporate portal
  v
Corporate IdP
  |
  | 2. Choose "Salesforce"
  v
SAML Response
  |
  v
Salesforce
  |
  v
Local application session
```

Key distinction:

``` text
SP-Initiated:
SP → IdP → SP

IdP-Initiated:
IdP → SP
```

In architecture discussions, understand which flow is being used because
the security properties and request-correlation model differ.

------------------------------------------------------------------------

## 2.8 SAML Metadata

Federation is not just "send XML."

The IdP and SP must agree on configuration.

SAML metadata commonly communicates information such as:

``` text
Entity ID
SSO endpoints
SLO endpoints where used
Signing certificates
Supported bindings
Role information
```

Conceptually:

``` text
                 Federation Setup
                       |
          +------------+------------+
          |                         |
          v                         v
       IdP Metadata              SP Metadata
          |                         |
          +-----------+-------------+
                      |
                      v
               Trust Configuration
```

Certificates are especially important because the SP uses the trusted
IdP signing certificate to verify assertions.

------------------------------------------------------------------------

## 2.9 Enterprise SAML Example

``` text
                 ACME CORPORATE
                       |
                +------+------+
                | Corporate   |
                | IdP         |
                | MFA         |
                +------+------+
                       |
          SAML Federation Trust
                       |
       +---------------+---------------+
       |               |               |
       v               v               v
 Salesforce        ServiceNow       Workday
    SP                 SP              SP
```

When Alice leaves ACME:

``` text
HR / Directory
     |
     v
Disable Alice
     |
     v
Corporate IdP
     |
     v
Future authentication blocked
```

This is one of the major enterprise benefits of centralized identity.

------------------------------------------------------------------------

## 2.10 SAML Strengths

-   Mature enterprise federation ecosystem
-   Strong support for enterprise SSO
-   Rich XML-based assertions
-   Widely supported by enterprise SaaS
-   Mature metadata and certificate-based trust models

## 2.11 SAML Limitations

-   XML complexity
-   More cumbersome for modern API/mobile development
-   Browser-centric deployments are common
-   XML signature/configuration mistakes can be difficult to
    troubleshoot
-   Less natural than OAuth/OIDC for REST APIs and modern application
    architectures

------------------------------------------------------------------------

# 3. OAuth 2.0

## 3.1 What Problem Does OAuth Solve?

OAuth 2.0 primarily solves **delegated authorization**.

The key problem:

> How can an application access a protected resource without requiring
> the user to give the application their password?

Example:

``` text
Alice
 |
 | wants Calendar App to read calendar
 v
Calendar App
 |
 | requests authorization
 v
Authorization Server
 |
 | Access Token
 v
Calendar App
 |
 | Access Token
 v
Calendar API
```

The calendar app never needs Alice's Google password.

------------------------------------------------------------------------

## 3.2 OAuth Roles

OAuth defines four major roles.

### Resource Owner

Usually the user.

``` text
Alice
```

The resource owner can authorize access to protected resources.

### Client

The application requesting access.

``` text
Calendar Application
```

### Authorization Server

Issues tokens after the authorization process.

``` text
Authorization Server
```

### Resource Server

Hosts protected resources.

``` text
Calendar API
```

Architecture:

``` text
                   +----------------------+
                   | Authorization Server |
                   |                      |
                   | Authentication       |
                   | Authorization        |
                   | Token Endpoint       |
                   +----------+-----------+
                              |
                              | Access Token
                              v
+--------------+       +--------------+
| Resource     |       | Resource     |
| Owner        |       | Server       |
| Alice        |       | Calendar API |
+------+-------+       +------+-------+
       |                      ^
       |                      |
       v                      |
     Client ------------------+
   Calendar App
```

------------------------------------------------------------------------

## 3.3 OAuth Is Not Primarily Authentication

This distinction is fundamental.

OAuth asks:

> Can this client access this protected resource?

It does not, by itself, standardize:

> Who is the human user?

OIDC adds standardized authentication semantics on top of OAuth.

------------------------------------------------------------------------

## 3.4 Authorization Code Flow

The Authorization Code flow is central to modern OAuth deployments.

### Step-by-step

``` text
1. User opens Client
          |
          v
2. Client redirects to Authorization Server
          |
          v
3. Authorization Server authenticates user
          |
          v
4. User grants consent
          |
          v
5. Authorization Server redirects back with code
          |
          v
6. Client exchanges code for tokens
          |
          v
7. Client calls Resource Server with access token
```

Detailed:

``` text
 User                 Client              Auth Server             API
  |                     |                      |                   |
  |--- open app ------->|                      |                   |
  |                     |--- authorize ------->|                   |
  |                     |                      |                   |
  |<--------------------|---- login ---------->|                   |
  |                     |                      |                   |
  |-------------------->|---- credentials ---->|                   |
  |                     |                      |                   |
  |<--------------------|--- consent ----------|                   |
  |                     |                      |                   |
  |                     |<--- authorization ---|                   |
  |                     |      code            |                   |
  |                     |                      |                   |
  |                     |--- code + verifier ->|                   |
  |                     |<--- access token ----|                   |
  |                     |                      |                   |
  |                     |--- access token ------------------------>|
  |                     |<--- protected resource -----------------|
```

------------------------------------------------------------------------

## 3.5 Authorization Code

The authorization code is a short-lived credential representing the
result of the authorization request.

Conceptually:

``` text
Authorization Server
       |
       | code = abc123
       v
Client
       |
       | exchange code
       v
Token Endpoint
       |
       v
Access Token
```

The authorization code should not be treated as an access token.

------------------------------------------------------------------------

## 3.6 PKCE

**PKCE = Proof Key for Code Exchange.**

PKCE protects the authorization code flow against code interception.

### Step 1: Generate verifier

The client creates a high-entropy random value:

``` text
code_verifier
```

### Step 2: Create challenge

For the standard S256 method:

``` text
code_challenge =
    BASE64URL(
        SHA256(code_verifier)
    )
```

### Step 3: Send challenge

``` text
Client
  |
  | authorization request
  | code_challenge = X
  v
Authorization Server
```

### Step 4: Receive code

``` text
Authorization Server
  |
  | authorization code
  v
Client
```

### Step 5: Redeem code

``` text
Client
  |
  | code + code_verifier
  v
Token Endpoint
```

The server verifies that the supplied verifier corresponds to the
original challenge.

``` text
                 Authorization Server
                         |
       code_challenge = SHA256(verifier)
                         |
                         v
                    Authorization
                         |
                         v
                       Code
                         |
                         v
Client ---------------- Token Endpoint
       code + verifier
                         |
                         v
                    Verify match
                         |
                         v
                     Tokens
```

### Why this matters

Suppose an attacker intercepts the authorization code:

``` text
Victim gets code = ABC
Attacker steals code = ABC
```

The attacker still does not have:

``` text
code_verifier
```

Therefore the attacker should not be able to redeem the code
successfully.

------------------------------------------------------------------------

## 3.7 OAuth Client Credentials Grant

Used for machine-to-machine scenarios.

There is no end-user consent flow in the normal client-credentials
pattern.

Example:

``` text
Payment Service
       |
       | client authentication
       v
Authorization Server
       |
       | access token
       v
Payment Service
       |
       | Bearer access token
       v
Fraud API
```

Typical use cases:

-   Microservice-to-microservice calls
-   Backend integrations
-   Daemons
-   Scheduled jobs
-   Service accounts

Mental model:

``` text
User involved?        No
Delegated user access? No
Application identity?  Yes
```

------------------------------------------------------------------------

## 3.8 Access Tokens

An access token is a credential used to access protected resources.

Example:

``` http
GET /calendar/events
Authorization: Bearer ACCESS_TOKEN
```

An access token may encode or reference information such as:

``` text
issuer
subject/client
audience
scope
expiration
```

However, **not every access token is a JWT**.

Access tokens can be opaque strings.

``` text
Opaque:
8f2a...random-looking-value...

JWT:
header.payload.signature
```

The resource server must validate the token according to the
authorization server's token model.

------------------------------------------------------------------------

## 3.9 Refresh Tokens

A refresh token allows a client to obtain a new access token without
requiring the user to repeat the entire authorization process, when the
authorization server issues refresh tokens.

``` text
Client
 |
 | refresh token
 v
Authorization Server
 |
 | new access token
 v
Client
 |
 | access token
 v
API
```

Important:

``` text
Refresh Token → Authorization Server
Access Token  → Resource Server
```

A refresh token is generally not sent to the protected API.

------------------------------------------------------------------------

## 3.10 OAuth Scopes

Scopes express requested/authorized permissions.

Examples:

``` text
calendar.read
calendar.write
profile
email
payments.read
```

Example:

``` text
scope = calendar.read calendar.write
```

The authorization server may grant a scope set equal to or narrower than
what was requested.

``` text
Client requests:
calendar.read calendar.write

Authorization Server grants:
calendar.read
```

The resource server then enforces the resulting permissions.

------------------------------------------------------------------------

## 3.11 OAuth Token Lifecycle

``` text
              Authorization
                    |
                    v
             Authorization Code
                    |
                    v
              Access Token
                    |
              +-----+------+
              |            |
           API use       expires
                           |
                           v
                     Refresh Token
                           |
                           v
                    New Access Token
```

------------------------------------------------------------------------

# 4. OIDC

## 4.1 Why OIDC Exists

OAuth provides authorization but does not standardize a complete user
authentication protocol.

OIDC fills this gap.

**OIDC = OpenID Connect.**

OIDC is an identity layer built on top of OAuth 2.0. It defines
standardized authentication semantics and identity claims. The OpenID
Foundation describes OIDC Core as authentication built on OAuth 2.0 with
claims used to communicate information about the End-User.
citeturn0search0

Mental model:

``` text
OAuth 2.0
   |
   | authorization foundation
   v
OpenID Connect
   |
   | authentication + identity
   v
User login
```

------------------------------------------------------------------------

## 4.2 OIDC Roles

Common OIDC terminology:

``` text
End-User
   |
   v
Relying Party (RP)
   |
   | trusts
   v
OpenID Provider (OP)
```

### End-User

The person being authenticated.

### Relying Party (RP)

The application relying on the identity result.

### OpenID Provider (OP)

The identity provider that authenticates the user and provides OIDC
responses.

The OP also provides OAuth authorization-server functionality.

------------------------------------------------------------------------

## 4.3 OIDC Authorization Code + PKCE

Modern web/mobile authentication often uses:

``` text
User
 |
 v
OIDC Client / RP
 |
 | authorization request
 | client_id
 | redirect_uri
 | scope=openid ...
 | state
 | nonce
 | code_challenge
 v
OpenID Provider
 |
 | authenticate + MFA
 v
Authorization Code
 |
 v
OIDC Client
 |
 | code + code_verifier
 v
Token Endpoint
 |
 +----> ID Token
 |
 +----> Access Token
 |
 +----> Refresh Token (if issued)
 v
OIDC Client
 |
 v
Authenticated application
```

------------------------------------------------------------------------

## 4.4 The `openid` Scope

A major OIDC clue is:

``` text
scope=openid
```

The `openid` scope signals an OpenID Connect authentication request.

Additional scopes can request claims or API permissions according to the
provider's implementation.

Example:

``` text
scope=openid profile email calendar.read
```

Conceptually:

``` text
openid
  ↓
OIDC authentication

calendar.read
  ↓
API authorization
```

------------------------------------------------------------------------

## 4.5 ID Token

The ID token is the central OIDC identity artifact.

Purpose:

> Communicate authentication/identity information to the OIDC client.

Common format:

``` text
JWT
```

Conceptual example:

``` json
{
  "iss": "https://idp.example.com",
  "sub": "user-123",
  "aud": "client-456",
  "exp": 1780000000,
  "iat": 1779996400,
  "nonce": "random-value"
}
```

Important claims:

``` text
iss   → issuer
sub   → subject
aud   → intended audience
exp   → expiration
iat   → issued-at time
nonce → request correlation/replay defense
```

------------------------------------------------------------------------

## 4.6 ID Token vs Access Token

This is one of the most important distinctions in IAM.

``` text
                    OIDC Provider
                         |
             +-----------+-----------+
             |                       |
             v                       v
         ID Token               Access Token
             |                       |
             v                       v
        OIDC Client                API
             |                       |
      "Who authenticated?"     "What can be accessed?"
```

### ID Token

Audience:

``` text
OIDC Client / RP
```

Purpose:

``` text
Authentication / identity
```

### Access Token

Audience:

``` text
Resource Server / API
```

Purpose:

``` text
Authorization
```

Do not automatically send an ID token to an API.

------------------------------------------------------------------------

## 4.7 Claims

A **claim** is a statement about an entity.

Examples:

``` text
sub = 123456
email = alice@example.com
name = Alice
department = Engineering
```

Claims can appear in different identity artifacts.

``` text
SAML
  → assertions / attributes

OIDC
  → ID token claims
  → UserInfo claims

OAuth access tokens
  → may contain authorization-related claims
```

------------------------------------------------------------------------

## 4.8 State

`state` protects the authorization response flow by allowing the client
to associate the response with the authorization request it initiated.

Conceptually:

``` text
Client
 |
 | generate state = ABC123
 v
Authorization Server
 |
 | redirect back with state = ABC123
 v
Client
 |
 | compare with expected value
 v
Accept / Reject
```

If the returned value does not match the expected value, the client
should reject the response.

State is especially important for preventing request/response mix-up and
CSRF-style attacks in browser authorization flows.

------------------------------------------------------------------------

## 4.9 Nonce

OIDC uses `nonce` to bind an ID token to the authentication request.

``` text
Client
 |
 | nonce = XYZ789
 v
OIDC Provider
 |
 | authentication
 v
ID Token
 |
 | nonce = XYZ789
 v
Client
 |
 | validate nonce
 v
Accept / Reject
```

The client should validate the nonce when required by the OIDC flow.

------------------------------------------------------------------------

## 4.10 OIDC Discovery

OIDC providers can publish metadata describing important endpoints and
capabilities.

Conceptually:

``` text
/.well-known/openid-configuration
             |
             v
+-------------------------------+
| issuer                        |
| authorization_endpoint        |
| token_endpoint                |
| userinfo_endpoint             |
| jwks_uri                      |
| supported scopes              |
| supported response types      |
+-------------------------------+
```

This allows clients to discover provider configuration rather than
hard-coding every endpoint.

------------------------------------------------------------------------

## 4.11 JWKS and Signing Keys

OIDC ID tokens are commonly signed.

The client needs the provider's public signing keys to verify
signatures.

Typical architecture:

``` text
OIDC Provider
     |
     | publishes JWKS
     v
JWKS Endpoint
     |
     | public keys
     v
OIDC Client
     |
     | verify ID token signature
     v
Trusted identity result
```

Key rotation is an important operational consideration.

------------------------------------------------------------------------

# 5. Tokens

## 5.1 Token vs Assertion vs Session

These concepts are related but not identical.

``` text
Token
  |
  +--> Credential used by a protocol

Assertion
  |
  +--> Statement made by one trusted party about identity/security state

Session
  |
  +--> Ongoing authenticated state maintained by an application
```

Examples:

``` text
SAML Assertion → identity statement
OIDC ID Token  → identity credential
OAuth Access Token → API authorization credential
Cookie Session → application login state
```

------------------------------------------------------------------------

## 5.2 ID Token

Purpose:

``` text
Tell the OIDC client about authentication and identity.
```

Common claims:

``` text
iss
sub
aud
exp
iat
nonce
```

The RP should validate the ID token according to OIDC requirements.

------------------------------------------------------------------------

## 5.3 Access Token

Purpose:

``` text
Authorize access to a protected resource.
```

Example:

``` text
Client
 |
 | Authorization: Bearer <token>
 v
Resource Server
```

Access tokens may be:

-   Opaque
-   JWTs
-   Other token formats depending on the authorization system

Therefore:

> **Access token ≠ JWT by definition.**

------------------------------------------------------------------------

## 5.4 Refresh Token

Purpose:

``` text
Obtain new access tokens.
```

Typical relationship:

``` text
Refresh Token
      |
      v
Authorization Server
      |
      v
Access Token
      |
      v
Resource Server
```

Refresh tokens require stronger protection because they can have a
longer useful lifetime.

------------------------------------------------------------------------

## 5.5 JWT

**JWT = JSON Web Token.**

JWT is a compact claims format.

A signed JWT commonly looks like:

``` text
HEADER.PAYLOAD.SIGNATURE
```

Conceptually:

``` text
+------------+-------------+-------------+
| Header     | Payload     | Signature   |
+------------+-------------+-------------+
| alg        | iss         | cryptographic|
| typ        | sub         | signature    |
| kid        | aud         |              |
|            | exp         |              |
+------------+-------------+-------------+
```

### Important

Base64url encoding is not encryption.

If a JWT is only signed:

``` text
Anyone possessing it
      |
      v
Can decode payload
```

The signature protects integrity/authenticity, not confidentiality.

------------------------------------------------------------------------

## 5.6 JWT Signature

Simplified model:

``` text
Header + "." + Payload
            |
            | signing key
            v
        Signature
```

Verification:

``` text
Header + "." + Payload
            |
            | trusted public key
            v
      Verify Signature
```

If the payload has been modified:

``` text
Original:
role=developer

Attacker changes:
role=admin

Signature verification
        |
        v
     FAIL
```

------------------------------------------------------------------------

## 5.7 Issuer (`iss`)

`iss` identifies who issued the token.

Example:

``` text
iss = https://idp.example.com
```

A client/API should trust only expected issuers.

------------------------------------------------------------------------

## 5.8 Subject (`sub`)

`sub` identifies the principal represented by the token.

Example:

``` text
sub = 2487192
```

Important:

``` text
Issuer A:
sub=123

Issuer B:
sub=123
```

These do not automatically represent the same identity.

Identity uniqueness is generally scoped to the issuer/security domain.

------------------------------------------------------------------------

## 5.9 Audience (`aud`)

`aud` indicates the intended recipient/audience.

Example:

``` text
aud = https://api.example.com
```

Audience validation is a critical security boundary.

``` text
Token intended for API-A
          |
          v
       API-B
          |
          v
aud != API-B
          |
          v
        REJECT
```

------------------------------------------------------------------------

## 5.10 Expiration (`exp`)

`exp` indicates when a token expires.

``` text
Issued:      10:00
Expires:     10:10
```

After expiration:

``` text
API
 |
 | token.exp < current_time
 v
Reject
```

Clock synchronization is therefore important in distributed identity
systems.

------------------------------------------------------------------------

## 5.11 Issued At (`iat`)

`iat` identifies when the token was issued.

Example:

``` text
iat = 10:00
```

It can help with validation and token-lifetime reasoning.

------------------------------------------------------------------------

## 5.12 Scopes

Scopes express permissions requested/granted by OAuth.

Example:

``` text
scope = payments.read
```

Think:

``` text
Scope → What operation is authorized?
```

Do not confuse:

``` text
sub   → Who?
scope → What access?
aud   → For whom?
iss   → Issued by whom?
exp   → Until when?
```

------------------------------------------------------------------------

## 5.13 Token Validation Mental Model

When receiving a security token:

``` text
             Token received
                    |
                    v
             Parse token
                    |
                    v
          Verify cryptographic
             integrity
                    |
                    v
          Is issuer trusted?
                    |
                    v
          Is audience correct?
                    |
                    v
          Is token unexpired?
                    |
                    v
          Are required scopes/
          permissions present?
                    |
                    v
             Accept request
```

The exact validation rules depend on token type and protocol.

------------------------------------------------------------------------

# 6. Sessions

## 6.1 What Is a Session?

A session represents ongoing authenticated state between a user/client
and an application.

Example:

``` text
Alice logs in
     |
     v
Application validates identity
     |
     v
Application creates session
     |
     v
Browser receives cookie
     |
     v
Alice makes subsequent requests
```

------------------------------------------------------------------------

## 6.2 Cookie-Based Session

Traditional web application:

``` text
Browser
   |
   | username/password
   v
Application
   |
   | create session
   v
Session Store
   |
   | session_id
   v
Browser
```

Browser:

``` http
Cookie: session_id=abc123
```

Later:

``` text
Browser
   |
   | Cookie: session_id=abc123
   v
Application
   |
   | lookup session
   v
Session Store
```

The browser cookie is usually an opaque identifier.

------------------------------------------------------------------------

## 6.3 Secure Session Cookies

For authentication cookies, common security attributes include:

``` text
Secure
HttpOnly
SameSite
```

Conceptually:

``` text
Secure
  → send over HTTPS

HttpOnly
  → JavaScript cannot directly read the cookie

SameSite
  → controls cross-site cookie sending behavior
```

The exact SameSite setting should match the application's legitimate
cross-site authentication requirements.

------------------------------------------------------------------------

## 6.4 Token-Based API Architecture

A typical API architecture:

``` text
Client
  |
  | Authorization: Bearer ACCESS_TOKEN
  v
API
  |
  | validate token
  v
Authorize request
```

For a JWT access token, the API may validate:

``` text
Signature
Issuer
Audience
Expiration
Scopes
Other claims
```

For an opaque token, the API may use introspection or another validation
mechanism.

------------------------------------------------------------------------

## 6.5 Session vs Token

  Session                        Token
  ------------------------------ --------------------------------------------
  Application login state        Credential used across protocol boundaries
  Often server-side state        May contain claims
  Usually referenced by cookie   Often sent as Authorization header
  Easy central revocation        Stateless JWT revocation is more complex
  Common for browser apps        Common for APIs/distributed systems

But this is not an either/or choice.

A modern architecture can use both:

``` text
OIDC
 |
 | authenticate user
 v
Application
 |
 | validate identity
 v
Create local session
 |
 v
Secure Cookie
```

And separately:

``` text
Application backend
 |
 | OAuth access token
 v
Downstream API
```

------------------------------------------------------------------------

## 6.6 BFF Pattern

A useful modern web architecture is the **Backend-for-Frontend (BFF)**.

``` text
Browser
   |
   | Secure session cookie
   v
BFF
   |
   | Access token
   v
API
```

The browser does not need to directly manage every API access token.

The BFF can:

-   Manage the browser session
-   Handle OIDC
-   Store tokens server-side
-   Call APIs
-   Enforce application-specific controls

This can reduce exposure of tokens to browser JavaScript.

------------------------------------------------------------------------

## 6.7 Logout

Logout can occur at multiple layers.

``` text
              Logout
                 |
       +---------+---------+
       |         |         |
       v         v         v
 Local App    IdP Session  Tokens
 Session
```

A complete logout strategy may involve:

``` text
1. Delete local session
2. Clear browser cookie
3. Optionally initiate IdP logout
4. Revoke refresh token where supported
5. Expire server-side sessions
```

An already-issued access token may remain usable until expiration unless
the architecture uses active revocation/introspection or another
mechanism.

OIDC defines standardized logout-related specifications, including
RP-initiated, front-channel, and back-channel logout.
citeturn0search0

------------------------------------------------------------------------

# 7. Federation Architecture

## 7.1 Enterprise Federation

Consider:

``` text
                         ACME CORPORATE
                               |
                     +---------+---------+
                     | Corporate Identity|
                     | Provider / IdP   |
                     +---------+---------+
                               |
              +----------------+----------------+
              |                |                |
             SAML             OIDC             OIDC
              |                |                |
              v                v                v
         SaaS App A       Internal App       Developer Portal
              |                |                |
              v                v                v
        Local Session    Local Session    Local Session
```

The corporate identity platform is the central authentication authority.

------------------------------------------------------------------------

## 7.2 End-to-End OIDC Enterprise Flow

``` text
Alice
 |
 | Open Internal App
 v
Internal Application
 |
 | Authorization Request
 | state
 | nonce
 | PKCE
 v
Corporate OIDC Provider
 |
 | Authenticate + MFA
 v
Authorization Code
 |
 v
Internal Application
 |
 | Code + PKCE verifier
 v
Token Endpoint
 |
 +--> ID Token
 +--> Access Token
 |
 v
Application validates identity
 |
 v
Create local session
 |
 v
Alice accesses application
```

------------------------------------------------------------------------

## 7.3 Authentication and Authorization Separation

A strong enterprise design separates:

``` text
Corporate IdP
      |
      | Authentication
      | Identity
      | Groups / Claims
      v
Application
      |
      | Application authorization
      | RBAC / ABAC / policy
      v
Permissions
```

Example:

``` text
IdP Group:
Engineering

Application mapping:
Engineering
   |
   +--> reports.read
   +--> deployments.read

IdP Group:
Finance

Application mapping:
Finance
   |
   +--> payments.read
```

The IdP authenticates the person.

The application remains responsible for deciding what that identity may
do inside the application unless authorization is deliberately delegated
to another policy system.

------------------------------------------------------------------------

## 7.4 Workforce Federation

Typical enterprise:

``` text
Employee
   |
   v
Corporate Directory
   |
   v
Identity Provider
   |
   +---- SAML ----> SaaS
   |
   +---- OIDC ----> Internal App
   |
   +---- OAuth ---> APIs
```

This is a realistic IAM architecture because organizations often use
multiple protocols simultaneously.

------------------------------------------------------------------------

## 7.5 Identity Lifecycle

Authentication protocols do not replace identity lifecycle management.

Think:

``` text
HR System
   |
   v
Identity Lifecycle
   |
   +--> Create account
   +--> Update attributes
   +--> Disable account
   +--> Remove access
   |
   v
Corporate IdP
   |
   v
Applications
```

Provisioning/deprovisioning can use systems and standards such as SCIM
in addition to authentication protocols.

Important distinction:

``` text
SAML / OIDC
    → Authentication / federation

OAuth
    → Authorization

SCIM
    → Provisioning / lifecycle
```

------------------------------------------------------------------------

## 7.6 Federation Trust

Federation depends on trust configuration.

``` text
            TRUST
              |
      +-------+-------+
      |               |
      v               v
    IdP               SP
      |               |
      +-------+-------+
              |
              v
        Trust Material
              |
      +-------+-------+
      |               |
 Certificates     Metadata /
 / Keys            Endpoints
```

The exact trust mechanism differs by protocol.

------------------------------------------------------------------------

## 7.7 Multi-Cloud Enterprise Example

``` text
                         Corporate IdP
                              |
             +----------------+----------------+
             |                |                |
             v                v                v
             AWS             Azure             GCP
             |                |                |
        Workforce IAM    Enterprise IAM    Workforce IAM
             |                |                |
             +----------------+----------------+
                              |
                              v
                        Applications
```

The identity architecture is centralized even when workloads are
distributed.

This is a key enterprise IAM principle:

> **Centralize identity governance where practical; distribute workload
> authorization according to resource boundaries.**

------------------------------------------------------------------------

# 8. SAML vs OAuth 2.0 vs OIDC

## 8.1 First Principle

Do not think:

``` text
SAML vs OAuth vs OIDC
```

as if they are three interchangeable login protocols.

Instead:

``` text
SAML
  → Federation / Enterprise SSO

OAuth 2.0
  → Delegated Authorization

OIDC
  → Authentication / Identity
     built on OAuth 2.0
```

The OpenID Foundation explicitly describes OIDC as authentication built
on OAuth 2.0. citeturn0search0

------------------------------------------------------------------------

## 8.2 Comparison by Question

  -----------------------------------------------------------------------
  Question          SAML              OAuth 2.0         OIDC
  ----------------- ----------------- ----------------- -----------------
  Who               Yes               Not its primary   Yes
  authenticated?                      purpose           

  What can client   Not its primary   Yes               Yes, through
  access?           purpose                             OAuth

  Enterprise SSO?   Excellent         Not by itself     Excellent

  API               Not primary       Excellent         Uses OAuth
  authorization?                                        

  Identity token?   Assertion         No standard ID    ID token
                                      token             

  Main artifact     SAML Assertion    Access Token      ID Token + Access
                                                        Token

  Data              XML               HTTP/JSON         JSON/JWT commonly
  representation                      commonly          

  Browser redirect  Common            Common            Common
  flows                                                 

  Mobile apps       Less natural      Yes               Excellent

  REST APIs         Less natural      Excellent         Excellent with
                                                        OAuth

  Enterprise SaaS   Very common       Common            Increasingly
                                                        common

  Federation        Yes               Not by itself     Yes, through OIDC
                                                        trust
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 8.3 SAML vs OIDC

Both can provide enterprise SSO.

### SAML

``` text
IdP
 |
 | XML SAML Assertion
 v
SP
 |
 v
Session
```

### OIDC

``` text
OP
 |
 | ID Token
 v
RP
 |
 v
Session
```

The architectural idea is similar:

``` text
Central Identity Provider
          |
          v
Application trusts identity result
          |
          v
Local session
```

The protocol mechanics and artifact formats differ.

------------------------------------------------------------------------

## 8.4 OAuth vs OIDC

``` text
OAuth 2.0
    |
    | Authorization
    v
Access Token
    |
    v
API

OIDC
    |
    | Authentication
    v
ID Token
    |
    v
Client
```

The simplest memory trick:

``` text
OAuth  → "Can I access it?"
OIDC   → "Who logged in?"
```

------------------------------------------------------------------------

## 8.5 Scenario-Based Selection

### Scenario A

> Employees need SSO into an old enterprise SaaS platform.

Use:

``` text
SAML
```

### Scenario B

> A mobile application needs user login.

Use:

``` text
OIDC
+
Authorization Code
+
PKCE
```

### Scenario C

> A service needs to call another service's API.

Use:

``` text
OAuth 2.0
Client Credentials
```

### Scenario D

> An application needs a user's consent to read their calendar.

Use:

``` text
OAuth 2.0
Authorization Code
+
PKCE where appropriate
```

### Scenario E

> An internal application needs enterprise user authentication and API
> access.

Use:

``` text
OIDC
+
OAuth 2.0
```

------------------------------------------------------------------------

## 8.6 Detailed Comparison Table

  ---------------------------------------------------------------------------
  Area              SAML                  OAuth 2.0         OIDC
  ----------------- --------------------- ----------------- -----------------
  Core problem      Federated identity /  Delegated         Authentication /
                    SSO                   authorization     identity

  Typical principal User                  User or client    User

  Typical consumer  SP                    Resource          RP
                                          server/client     

  Main issuer role  IdP                   Authorization     OpenID Provider
                                          Server            

  Main credential   Assertion             Access token      ID token + access
                                                            token

  Typical format    XML                   Token format      JWT commonly for
                                          varies            ID token

  API-first design  Weak fit              Strong fit        Strong fit when
                                                            combined with
                                                            OAuth

  Browser SSO       Strong                Can support       Strong
                                          authorization     
                                          redirects         

  Mobile            Possible but less     Strong            Strong
  authentication    natural                                 

  Enterprise legacy Strong                Moderate          Strong

  Delegated user    Not primary           Strong            Strong via OAuth
  permissions                                               

  Authentication    Strong                Not standardized  Strong
  semantics                                                 

  Token audience    Assertion conditions  Access token      ID token
                    / audience            audience          audience + access
                                                            token audience

  PKCE              No                    Yes               Yes through OAuth

  `state`           Different             Yes in            Yes
                    mechanisms/profiles   authorization     
                                          flows             

  `nonce`           Not OIDC concept      Not OAuth core    Yes
                                          concept           

  XML               Yes                   No                No

  JWT               Not core              Common            Common
  ---------------------------------------------------------------------------

------------------------------------------------------------------------

# 9. Security Considerations

## 9.1 Threat Model First

Identity systems should be designed against threats such as:

``` text
Attacker
   |
   +--> Steal token
   +--> Intercept code
   +--> Forge token
   +--> Replay assertion
   +--> Trick browser
   +--> Abuse excessive scope
   +--> Send token to wrong API
   +--> Exploit redirect URI
```

Security controls should map to these threats.

------------------------------------------------------------------------

## 9.2 Token Theft

Bearer token model:

``` text
Token = bearer credential

Whoever possesses it
       |
       v
May be able to use it
```

Mitigations:

-   HTTPS/TLS
-   Short access-token lifetime
-   Secure token storage
-   Least privilege
-   Refresh-token protection
-   Refresh-token rotation where supported
-   Sender-constrained tokens where appropriate
-   Monitoring
-   Revocation/introspection where appropriate

------------------------------------------------------------------------

## 9.3 Replay Attack

A replay attack uses a previously valid credential or message again.

``` text
Legitimate message
      |
      v
Attacker captures it
      |
      v
Attacker sends same message again
      |
      v
Server accidentally accepts replay
```

Defenses can include:

``` text
Short validity windows
Nonces
State
One-time authorization codes
Assertion IDs / replay detection
PKCE
TLS
Token rotation
```

The exact defense depends on the protocol and threat.

------------------------------------------------------------------------

## 9.4 CSRF

CSRF can cause a browser to make an unwanted request in the victim's
security context.

For OAuth/OIDC browser flows:

``` text
Client
 |
 | generate unpredictable state
 v
Authorization Server
 |
 | return state
 v
Client
 |
 | verify state
 v
Continue
```

The client should bind the authorization response to the request it
initiated.

------------------------------------------------------------------------

## 9.5 Authorization Code Interception

Threat:

``` text
Authorization Server
       |
       | code
       v
Browser / Client
       |
       +------> attacker steals code
```

PKCE:

``` text
Original request:
code_challenge = H(verifier)

Token request:
code + verifier

Server:
H(verifier) == original challenge?
        |
       YES
        |
      Tokens
```

This prevents an attacker who only has the code from redeeming it.

------------------------------------------------------------------------

## 9.6 Redirect URI Security

The authorization server must not blindly redirect authorization
responses to arbitrary destinations.

Conceptually:

``` text
Registered:
https://app.example.com/callback

Attacker tries:
https://evil.example/callback
```

The authorization server should enforce registered redirect URI policy.

Poor redirect URI validation can lead to code/token leakage.

------------------------------------------------------------------------

## 9.7 Issuer Validation

Expected:

``` text
iss = https://trusted-idp.example
```

Unexpected:

``` text
iss = https://attacker.example
```

Reject.

The application must establish which issuer(s) are trusted.

------------------------------------------------------------------------

## 9.8 Audience Validation

Example:

``` text
Access Token:
aud = payment-api
```

Request arrives at:

``` text
reporting-api
```

If the token is not intended for the reporting API:

``` text
Reject
```

This prevents tokens from being treated as universal credentials across
unrelated resource servers.

------------------------------------------------------------------------

## 9.9 Signature Validation

For signed JWTs:

``` text
Token
 |
 v
Read key identifier (`kid`)
 |
 v
Find trusted public key
 |
 v
Verify signature
 |
 +--> FAIL → Reject
 |
 +--> PASS → Continue validation
```

Signature validation is only one part of token validation.

------------------------------------------------------------------------

## 9.10 Algorithm and Key Handling

A secure implementation should not blindly trust attacker-controlled
token header values.

Important considerations include:

-   Allowed algorithms
-   Trusted issuer keys
-   Key rotation
-   `kid` handling
-   Algorithm confusion defenses
-   JWKS retrieval and caching
-   Key lifecycle

------------------------------------------------------------------------

## 9.11 Least Privilege

Bad:

``` text
scope = *
```

Better:

``` text
scope = calendar.read
```

Even better when applicable:

``` text
calendar.read
calendar.events.read
```

Principle:

> Give the client only the permissions it actually needs.

------------------------------------------------------------------------

## 9.12 Refresh Token Protection

Refresh tokens can have a long security lifetime.

Protect them carefully.

Potential controls:

``` text
Secure storage
TLS
Rotation
Reuse detection
Revocation
Expiration
Device binding / sender constraint where appropriate
```

A stolen refresh token can be more damaging than a short-lived access
token.

------------------------------------------------------------------------

## 9.13 SAML-Specific Security

Important areas include:

``` text
XML signature validation
Issuer validation
Audience validation
Destination validation
Time conditions
Replay detection
Trusted metadata/certificates
```

A particularly important rule:

> Never accept a SAML assertion simply because its XML parses correctly.

------------------------------------------------------------------------

## 9.14 OIDC-Specific Security

Validate relevant ID token properties, including:

``` text
Signature
Issuer
Audience
Expiration
Issued-at constraints where applicable
Nonce
Other protocol-specific requirements
```

Also use secure redirect URI handling and PKCE for applicable
authorization-code clients.

------------------------------------------------------------------------

## 9.15 Security Validation Flow

A generic mental model:

``` text
              Credential received
                       |
                       v
              Is it structurally valid?
                       |
                       v
              Is cryptography valid?
                       |
                       v
              Is issuer trusted?
                       |
                       v
              Is audience correct?
                       |
                       v
              Is it within validity period?
                       |
                       v
              Is replay prevented?
                       |
                       v
              Are permissions sufficient?
                       |
                       v
                  ACCEPT
```

------------------------------------------------------------------------

# 10. Real-World Scenarios

## 10.1 Scenario 1 --- Salesforce Enterprise SSO

### Requirement

Employees use corporate credentials to access Salesforce.

Architecture:

``` text
Employee
   |
   v
Salesforce
   |
   | SAML AuthnRequest
   v
Corporate IdP
   |
   | Authenticate + MFA
   v
SAML Assertion
   |
   v
Salesforce
   |
   | Validate assertion
   v
Salesforce session
```

Protocol:

``` text
SAML
```

------------------------------------------------------------------------

## 10.2 Scenario 2 --- Mobile Application Login

### Requirement

A mobile application needs user authentication.

Architecture:

``` text
Mobile App
    |
    | Authorization Code + PKCE
    v
OIDC Provider
    |
    | Login + MFA
    v
Authorization Code
    |
    v
Mobile App
    |
    | code + verifier
    v
Token Endpoint
    |
    +--> ID Token
    +--> Access Token
```

Protocol stack:

``` text
OIDC
  +
OAuth 2.0
  +
PKCE
```

------------------------------------------------------------------------

## 10.3 Scenario 3 --- Calendar Application

### Requirement

A calendar application wants to read a user's calendar.

``` text
Alice
  |
  v
Calendar App
  |
  | request calendar.read
  v
Authorization Server
  |
  | authentication + consent
  v
Authorization Code
  |
  v
Calendar App
  |
  | exchange code
  v
Access Token
  |
  v
Calendar API
```

Protocol:

``` text
OAuth 2.0
```

If the application also needs to authenticate Alice, it may use:

``` text
OIDC + OAuth 2.0
```

------------------------------------------------------------------------

## 10.4 Scenario 4 --- Microservice-to-Microservice

### Requirement

Payment Service calls Fraud Service.

``` text
Payment Service
       |
       | Client Credentials
       v
Authorization Server
       |
       | access token
       v
Payment Service
       |
       | Bearer token
       v
Fraud API
```

Protocol:

``` text
OAuth 2.0
Client Credentials
```

No human login is required.

------------------------------------------------------------------------

## 10.5 Scenario 5 --- Internal Web Application

### Requirement

Employees should log into an internal application with corporate
identity.

``` text
Browser
   |
   v
Internal App
   |
   | OIDC Authorization Code + PKCE
   v
Corporate IdP
   |
   | authenticate + MFA
   v
Authorization Code
   |
   v
Internal App
   |
   | tokens
   v
Validate ID Token
   |
   v
Create local session
```

Protocol:

``` text
OIDC
```

------------------------------------------------------------------------

## 10.6 Scenario 6 --- Old Enterprise SaaS

### Requirement

A SaaS product supports only SAML.

Architecture:

``` text
Corporate IdP
      |
      | SAML
      v
SaaS SP
      |
      v
Local Session
```

Even if the company uses OIDC internally, it can still use SAML for that
SaaS application.

This is why enterprise IAM engineers need to understand both.

------------------------------------------------------------------------

## 10.7 Scenario 7 --- Hybrid Enterprise

Real companies may have all three:

``` text
                       Corporate IdP
                            |
           +----------------+----------------+
           |                |                |
           v                v                v
        SAML             OIDC             OAuth
           |                |                |
           v                v                v
       Legacy SaaS     Modern Apps        APIs
```

This is normal.

Protocol choice depends on:

-   Application capability
-   Security requirements
-   Architecture
-   User experience
-   API needs
-   Existing federation standards
-   Vendor support

------------------------------------------------------------------------

# 11. Common Misconceptions

## Misconception 1: OAuth is a login protocol

**Correction:**

OAuth primarily defines delegated authorization.

For standardized user authentication:

``` text
OIDC
```

------------------------------------------------------------------------

## Misconception 2: OIDC replaces OAuth

Incorrect.

OIDC builds on OAuth.

``` text
OIDC
  |
  v
OAuth 2.0
```

------------------------------------------------------------------------

## Misconception 3: OAuth and OIDC are the same

Not exactly.

``` text
OAuth → Authorization
OIDC  → Authentication + Identity
```

OIDC uses OAuth mechanisms.

------------------------------------------------------------------------

## Misconception 4: JWT is an authentication protocol

Incorrect.

``` text
JWT = token format
```

Protocols/frameworks:

``` text
SAML
OAuth 2.0
OIDC
```

------------------------------------------------------------------------

## Misconception 5: Every access token is a JWT

Incorrect.

Access tokens can be opaque.

``` text
Access Token
 |
 +--> JWT
 |
 +--> Opaque token
 |
 +--> Other implementation-specific format
```

------------------------------------------------------------------------

## Misconception 6: Every JWT is an access token

Incorrect.

JWT is a format.

A JWT can be used for different purposes depending on the protocol and
profile.

OIDC ID tokens are commonly JWTs.

------------------------------------------------------------------------

## Misconception 7: An ID token should be sent to every API

Incorrect.

The ID token is intended for the OIDC client.

The access token is intended for the resource server.

``` text
ID Token
   → Client

Access Token
   → API
```

------------------------------------------------------------------------

## Misconception 8: A valid signature means a token is valid for my API

Incorrect.

You also need relevant checks such as:

``` text
Issuer
Audience
Expiration
Scopes
Protocol-specific constraints
```

------------------------------------------------------------------------

## Misconception 9: Authentication determines all permissions

Not necessarily.

``` text
Authentication
      ↓
Identity
      ↓
Application Authorization
      ↓
Permissions
```

------------------------------------------------------------------------

## Misconception 10: SAML assertion equals application session

Usually no.

Typical:

``` text
SAML Assertion
      ↓
SP validates
      ↓
SP creates local session
      ↓
Browser cookie
```

------------------------------------------------------------------------

## Misconception 11: Federation means synchronization

Not necessarily.

Federation primarily establishes trust for identity/authentication.

Provisioning is a separate concern.

``` text
Federation
 → Authentication / trust

Provisioning
 → Create/update/delete accounts
```

SCIM is commonly used for provisioning.

------------------------------------------------------------------------

## Misconception 12: SSO means one session everywhere

Not necessarily.

Each application may maintain its own local session.

``` text
Corporate IdP session
       |
       +--> App A session
       +--> App B session
       +--> App C session
```

The user experiences SSO even though multiple application sessions
exist.

------------------------------------------------------------------------

# 12. Interview / Architecture Questions

## 12.1 Explain SAML in One Minute

Strong answer:

> SAML is an XML-based federation and SSO standard commonly used in
> enterprise environments. An Identity Provider authenticates a user and
> issues a signed SAML assertion to a Service Provider. The Service
> Provider validates the assertion, maps the identity and attributes,
> and normally creates its own application session.

------------------------------------------------------------------------

## 12.2 Explain OAuth 2.0 in One Minute

> OAuth 2.0 is an authorization framework that allows a client to obtain
> limited access to protected resources without requiring the resource
> owner's password. It defines roles such as resource owner, client,
> authorization server, and resource server, and commonly uses access
> tokens to represent delegated authorization.

------------------------------------------------------------------------

## 12.3 Explain OIDC in One Minute

> OpenID Connect adds an authentication and identity layer on top of
> OAuth 2.0. It allows a client to authenticate a user and receive
> standardized identity information, most notably through an ID token.
> Modern deployments commonly use Authorization Code with PKCE.

------------------------------------------------------------------------

## 12.4 Access Token vs ID Token

``` text
ID Token
 |
 | Audience: OIDC Client
 | Purpose: Authentication / identity
 v
Client

Access Token
 |
 | Audience: Resource Server
 | Purpose: API authorization
 v
API
```

------------------------------------------------------------------------

## 12.5 Why PKCE?

> PKCE binds the authorization code to a verifier known by the client.
> If an attacker intercepts the authorization code, the attacker does
> not have the verifier required to redeem it.

------------------------------------------------------------------------

## 12.6 What Is Federation?

> Federation is a trust relationship between separate identity/security
> domains in which one domain can rely on identity information
> established by another domain.

------------------------------------------------------------------------

## 12.7 SAML vs OIDC

A strong answer:

> Both can be used for federated authentication and SSO. SAML is an
> XML-based enterprise federation standard with signed assertions and is
> widely deployed in enterprise SaaS. OIDC is an identity layer built on
> OAuth 2.0 and is generally more natural for modern web, mobile, and
> API-oriented architectures.

------------------------------------------------------------------------

## 12.8 Why Is OAuth Not Enough for Login?

Because OAuth tells the client how to obtain authorization to access
resources, but OAuth alone does not standardize the identity information
needed to securely establish "this is the user who authenticated."

OIDC adds:

``` text
ID Token
Claims
Nonce
Authentication semantics
Discovery
```

------------------------------------------------------------------------

## 12.9 Why Validate Audience?

> To ensure that a credential issued for one resource is not incorrectly
> accepted by another resource.

Example:

``` text
Token aud = payment-api

reporting-api receives it

aud mismatch
     ↓
Reject
```

------------------------------------------------------------------------

## 12.10 Why Validate Issuer?

> To ensure that the credential came from an identity/authorization
> authority the application trusts.

------------------------------------------------------------------------

## 12.11 Why Short-Lived Access Tokens?

> To reduce the useful lifetime of a stolen bearer credential.

------------------------------------------------------------------------

## 12.12 Can OIDC Use Cookie Sessions?

Yes.

Very common architecture:

``` text
OIDC Authentication
        |
        v
Application
        |
        | validate identity
        v
Local Session
        |
        v
Secure Cookie
        |
        v
Browser
```

------------------------------------------------------------------------

## 12.13 What Happens When a User Logs Out?

Possible layers:

``` text
Local application session
        |
        v
IdP session
        |
        v
Refresh tokens
        |
        v
Access tokens
```

A complete logout design must define which layers are terminated.

------------------------------------------------------------------------

## 12.14 Design Question: Enterprise SaaS

### Question

> Design SSO for 500,000 employees across 100 SaaS applications.

A strong high-level design:

``` text
                    Corporate Identity
                           |
                    +------+------+
                    |             |
                  MFA        Conditional Access
                    |
                    v
             Corporate IdP
                    |
       +------------+------------+
       |            |            |
      SAML         OIDC         SAML
       |            |            |
       v            v            v
     SaaS A       SaaS B       SaaS C
```

Consider:

-   Central authentication
-   MFA
-   Conditional access
-   Federation metadata
-   Certificate/key rotation
-   Application onboarding
-   Attribute/claim mapping
-   Session lifetime
-   Logout
-   Monitoring
-   Deprovisioning
-   Break-glass accounts
-   Vendor support
-   Incident response

------------------------------------------------------------------------

## 12.15 Design Question: Modern Application

### Requirement

A browser application needs user login and API access.

Strong architecture:

``` text
Browser
   |
   | OIDC Authorization Code + PKCE
   v
Identity Provider
   |
   | ID Token + Access Token
   v
Application / BFF
   |
   | Secure application session
   v
Browser

Application / BFF
   |
   | OAuth Access Token
   v
Backend API
```

------------------------------------------------------------------------

# 13. Quick Reference Cheat Sheet

## 13.1 Identity Fundamentals

``` text
Authentication
→ Who are you?

Authorization
→ What can you do?

SSO
→ Authenticate once, access multiple applications.

Federation
→ Trust identity across security domains.
```

------------------------------------------------------------------------

## 13.2 Protocols

``` text
SAML
→ Enterprise federation / SSO
→ XML
→ SAML Assertions

OAuth 2.0
→ Delegated authorization
→ API access
→ Access Tokens

OIDC
→ Authentication + identity
→ Built on OAuth 2.0
→ ID Tokens
```

------------------------------------------------------------------------

## 13.3 Tokens

``` text
ID Token
→ OIDC client
→ Identity/authentication

Access Token
→ Resource server/API
→ Authorization

Refresh Token
→ Authorization server
→ Obtain new access token

JWT
→ Token/claims format
```

------------------------------------------------------------------------

## 13.4 Token Claims

``` text
iss
→ Who issued it?

sub
→ Who is represented?

aud
→ Who is it intended for?

exp
→ When does it expire?

iat
→ When was it issued?

scope
→ What access is granted?
```

------------------------------------------------------------------------

## 13.5 OAuth/OIDC Flow

``` text
User
 |
 v
Client
 |
 | Authorization Request
 | state
 | nonce (OIDC)
 | PKCE challenge
 v
Authorization Server / OIDC Provider
 |
 | Authenticate + MFA
 v
Authorization Code
 |
 v
Client
 |
 | code + verifier
 v
Token Endpoint
 |
 +----> ID Token (OIDC)
 |
 +----> Access Token
 |
 +----> Refresh Token (optional)
 v
Client
 |
 v
API
```

------------------------------------------------------------------------

## 13.6 SAML Flow

``` text
User
 |
 v
SP
 |
 | AuthnRequest
 v
IdP
 |
 | Authenticate + MFA
 v
IdP
 |
 | Signed SAML Response
 v
SP
 |
 | Validate assertion
 v
Local Session
```

------------------------------------------------------------------------

# Final Mental Model

If you remember only one page from this document, remember this:

``` text
                         IDENTITY & ACCESS
                                |
          +---------------------+---------------------+
          |                     |                     |
          v                     v                     v
   AUTHENTICATION         AUTHORIZATION          FEDERATION
          |                     |                     |
          v                     v                     v
     "WHO ARE YOU?"      "WHAT CAN YOU DO?"    "WHO TRUSTS WHOM?"
          |                     |                     |
          v                     v                     v
        OIDC                  OAuth 2.0              SAML
          |                     |                     |
          v                     v                     v
      ID Token             Access Token          Assertion
          |                     |                     |
          v                     v                     v
       Client                  API                    SP


OIDC:
IdP / OP
   |
   | ID Token
   v
Client / RP
   |
   v
Application Session


OAuth:
Authorization Server
   |
   | Access Token
   v
Client
   |
   | Access Token
   v
Resource Server / API


SAML:
Identity Provider
   |
   | Signed SAML Assertion
   v
Service Provider
   |
   v
Application Session
```

------------------------------------------------------------------------

# The 30-Second Recall

``` text
SAML
= Enterprise SSO / Federation
= XML Assertions

OAuth 2.0
= Delegated Authorization
= API Access
= Access Tokens

OIDC
= Authentication + Identity
= Built on OAuth 2.0
= ID Tokens

ID Token
= For the OIDC client
= "Who authenticated?"

Access Token
= For the API
= "What can be accessed?"

Refresh Token
= For the authorization server
= "Give me a new access token"

JWT
= Token/claims format
= Not a protocol

Session
= Application's ongoing authenticated state

Federation
= Trust between security/identity domains

PKCE
= Protects authorization code redemption

state
= Binds authorization response to the initiating request

nonce
= Binds OIDC ID token to authentication request

iss
= Who issued it?

sub
= Who is it about?

aud
= Who is it for?

exp
= When does it expire?

scope
= What access is granted?
```

------------------------------------------------------------------------

# One Final Architecture Rule

When analyzing an IAM architecture, ask these questions in order:

``` text
1. WHO is the user/service?
        |
        v
2. HOW is identity authenticated?
        |
        v
3. WHICH system is authoritative?
        |
        v
4. HOW is trust established?
        |
        v
5. WHAT artifact crosses the trust boundary?
        |
        +--> SAML Assertion?
        +--> OIDC ID Token?
        +--> OAuth Access Token?
        |
        v
6. WHO is the artifact intended for?
        |
        v
7. WHAT permissions does it grant?
        |
        v
8. HOW long is it valid?
        |
        v
9. HOW is replay/theft prevented?
        |
        v
10. HOW is the application session created?
        |
        v
11. HOW does logout/revocation work?
```

This mental model is more valuable than memorizing protocol terminology
because it lets you reason about unfamiliar IAM architectures.

------------------------------------------------------------------------

# Reference Standards / Further Reading

-   OpenID Connect specifications: https://openid.net/developers/specs/
-   OpenID Connect Working Group specifications:
    https://openid.net/wg/connect/specifications/
-   OAuth specifications and RFC index: https://oauth.net/specs/
-   OAuth 2.0 Authorization Framework: RFC 6749
-   OAuth 2.0 Bearer Token Usage: RFC 6750
-   Proof Key for Code Exchange (PKCE): RFC 7636
-   OAuth 2.0 Token Introspection: RFC 7662
-   JSON Web Token (JWT): RFC 7519

> Standards evolve. For implementation work, always verify the current
> specification and security best-current-practice guidance rather than
> relying solely on study notes.
