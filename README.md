# dgc-app-backend-demo

Backend for storing data for the RCPCH Digital Growth Charts app

## Getting started

Requires Docker already installed and running.

Copy `env-template` to `env` and update the OAuth variables as appropriate.

```bash
s/up
```

The API and demo run on `localhost` directly rather than a specific port. This is because
Google doesn't allow oauth redirects to localhost with a port.

The API runs on `localhost/api`. It is using a self-signed Caddy TLS certificate so you may
need to accept the certificate by visiting it in your browser.

The demo client runs on `localhost/demo`.

## Authentication

Despite being built on top of Django, we don't use Django session management but our own bearer auth JWT.

To "log in" to the API, you pass a valid ID token or refresh token from Microsoft Entra ID or Google (Login with Apple TODO).
The backend then vends an access token JWT. We have to issue our own tokens as Apple does not allow you to verify an access token.

Clients store the access token from the API alongside the refresh token from the third party auth provider.

We deliberately do not support our own authentication but delegate it to third party providers. This is a pragmatic choice
to try and take advantage of the abuse protection those providers already do.

## Data modelling

- Each person who logs in to the app is a `User`.
- Users are members of an `Organisation`, via `UserOrganisation`.
- Each `Child` has measurements and can be in more than one `Organisation` via `UserOrganisation`
  - Although not yet implemented the idea is that there is a single record for a child per linkage identifier (eg NHS number)

Access to an organisation grants you read/write access to all children within it. For parents and carers
they will have their own organisation with just their children and invite in others. We envisage larger
organisations to map to professional settings who want to use the app and not an EPR growth chart integration,
but this will be in the future.

Some child data is encrypted as a defense against the database ever leaking. Identifying data is encrypted with
a key per organisation. The organisation key is not stored in the database directly but is stored encrypted
with a key statically derived (PBKDF2HMAC) from the `sub` claim in the token from the login provider. There is then
an additional child key to encrypt personal information like date of birth. This is itself stored encrypted with 
each the key for each organisation the child is associated with. Encryption is performed using the
[Fernet](https://cryptography.io/en/latest/fernet/) helper from the Python cryptography library.

We don't store `sub` directly but use the SHA-256 hash of it as the user ID. The defense relies on on `sub` being
random and difficult to guess, such that you couldn't rainbow table the list of IDs in the database. For example,
you can't use this project against a provider that vends sequential `sub` IDs.

Users are invited to join an organisation using a link with the following data

- Secure random UUID as the "invite ID"
- Secure randomly generated password (not stored in the database)

Each invite in the database stores the organisation key encrypted with an ephemeral key derived from the share password.
Joining an org involves decrypting the key, checking it works and then writing a new `UserOrganisation` linking model.

| Model              | Field                      | Encryption Key | Notes                                                                                                                                                                              |
|--------------------|----------------------------|----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| User               | id                         | -              | SHA-256 of `sub` from the login provider. Hash cannot be salted since we don't want to store `sub` anywhere in our database                                                        |
| User               | salt/iterations            | -              | Configuration for deriving the user encryption key                                                                                                                                 |
| User               | encrypted_name             | User           | `name` claim from the login provider, encrypted with the user key. Returned from the API when renewing a session with the refresh token, as at that point the ID token has expired |
| User               | encrypted_email            | User           | as above                                                                                                                                                                           |
| Organisation       | encrypted_name             | Organisation   | Name describing the organisation (e.g. Michael's clinic). Encrypted with the organisation key as we have no idea what PII people might put in it                                   |
| UserOrganisation   | is_creator                 | -              | Used to derive a name for the organisation if none set (e.g. organisation is a single one for a parent/carer user)                                                                 |
| UserOrganisation   | encrypted_organisation_key | User           |                                                                                                                                                                                    |
| UserOrganisation   | encrypted_user_name        | Organisation   | `name` claim. Used to display which users are in the organisation                                                                                                                  |
| UserOrganisation   | encrypted_user_email       | Organisation   | `email` claim. Used to display which users are in the organisation                                                                                                                 |
| Child              | id                         | -              | Generic secure random UUID, stored plaintext.                                                                                                                                      |
| Child              | encrypted_name             | Child          | Displayed in the UI so the user can select from multiple children they can see                                                                                                     |
| Child              | encrypted_date_of_birth    | Child          | Required to call the dGC API                                                                                                                                                       |
| ChildOrganisation  | encrypted_child_key        | Organisation   |                                                                                                                                                                                    |
| OrganisationInvite | id                         | -              | Generic secure random UUID, stored plaintext. Part of a pair with the randomly generated password, both required to join an org                                                    |
| OrganisationInvite | salt/iterations            | -              | Configuration for deriving the ephemeral key from the password to decrypt the organisation key                                                                                     |
| OrganisationInvite | encrypted_organisation_key | Share          | Ronseal                                                                                                                                                                            |