# Password Reset Setup

The login screen now supports **Forgot password?** and the backend exposes:

- `POST /api/forgot-password`
- `POST /api/reset-password`

Reset tokens are cryptographically random, stored only as SHA-256 hashes, expire after the configured timeout, and are single-use. Older unused reset tokens are invalidated when a new reset is requested or a password is changed.

## Local development

Set:

```env
APP_BASE_URL=http://127.0.0.1:5000
RESET_TOKEN_MINUTES=30
RESET_SHOW_DEBUG_LINK=true
```

Without SMTP settings, the development UI displays the generated reset link so the flow can be tested locally.

## Deployment

Set `APP_BASE_URL` to the public HTTPS application URL and configure SMTP:

```env
MAIL_HOST=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=...
MAIL_PASSWORD=...
MAIL_FROM=...
MAIL_USE_TLS=true
RESET_SHOW_DEBUG_LINK=false
```

Do not enable `RESET_SHOW_DEBUG_LINK` in production.

## Database

The application already calls `db.create_all()` during startup, so the new `password_reset_tokens` table is created automatically for this prototype. For a production deployment with migrations, add the equivalent migration before rollout.
