# SSH-executed modules for vm-bhyve

Every other module in this collection talks to the OPNsense REST API over HTTPS. vm-bhyve has no REST API — it is a shell tool (`vm ...`) plus plain-text config files — and OPNsense ships no plugin exposing one. The `bhyve_*` modules therefore run **on the OPNsense host itself** (normal Ansible SSH connection, `run_command` against the `vm` CLI and its config files) instead of following the collection's API pattern.

## Considered Options

- Write an OPNsense PHP/MVC plugin exposing a bhyve REST API, keeping the house style — rejected as a disproportionate second project in another language and repo.
- A plain role of `command`/`template` tasks — rejected for lacking a real idempotency and check-mode story for stateful VM supervision.
