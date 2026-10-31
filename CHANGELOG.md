# Changelog

## 0.1.0

- `/livez` (public, `ok`), `/readyz` (internal or staff, else 404; 503 on a failed check;
  `?verbose` lists components without messages), `HealthMiddleware` first in the chain.
- Checks `database`, `migrations` (`warn` while pending), `redis`.
- `failure_message()`: exception class out, detail to the log.
- System checks `ct_health.E001`, `E002`, `W001`.
