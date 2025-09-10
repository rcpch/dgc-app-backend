# dgc-app-backend-demo

Backend for storing data for the RCPCH Digital Growth Charts app

TODO
  - Entra ID login (just to demonstrate getting an OIDC JWT)
  - Table mapping hashed `sub` to `salt`
  - Derive key from hashed `sub` and `salt`
    - Store iterations alongside salt mapping?
  - Encrypt personal fields on model
  - Store height/weight plaintext?