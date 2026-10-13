# PayMongo QR Ph deployment

PayMongo support is opt-in. Keep `PAYMONGO_ENABLED=False` until the account is activated, credentials are installed, webhook delivery is verified, and the payment worker is running. The background worker and settlement/reconciliation processing run even while customer QR checkout is disabled.

## Payment flow and safety

- Staff can record cash as a walk-in payment. QR Ph is a separate option.
- Every supported wallet scans the same QR Ph code; the payer chooses their wallet in their app.
- Permit one unresolved QR payment per staff member. A pending QR is not revenue and must not extend a membership.
- Minimizing only hides the modal. Cancel requests release the checkout only after a provider-confirmed nonpayable state, or before any provider request has begun. An unknown provider request remains unresolved.
- Provider webhooks and reconciliation establish settlement. A browser redirect or screenshot is never proof of payment.
- In PayMongo test mode, do not scan test QR images with a real wallet. Use the provider's test URL/simulator flow; the customer UI must hide test QR images.

## Environment

Copy `.env.example` to `.env`. Keep `DJANGO_DEBUG=True` only for local development. Production must set `DJANGO_DEBUG=False`, a newly generated `DJANGO_SECRET_KEY`, exact `DJANGO_ALLOWED_HOSTS`, and HTTPS `DJANGO_CSRF_TRUSTED_ORIGINS` such as `https://gym.example.com`. Set the domain to the public Cloudflare hostname. The app trusts Cloudflare's `X-Forwarded-Proto` header, enables secure session and CSRF cookies, redirects to HTTPS, and enables HSTS when debug is off. Ensure the Cloudflare tunnel forwards the original scheme and serves the app over HTTPS.

Choose `PAYMONGO_MODE=test` or `live`. Install the corresponding API secret in `PAYMONGO_SECRET_KEY` and webhook signing secret in `PAYMONGO_WEBHOOK_SECRET_TEST` or `PAYMONGO_WEBHOOK_SECRET_LIVE`. Alternatively set `PAYMONGO_SECRET_KEY_TEST` and `PAYMONGO_SECRET_KEY_LIVE`; these take precedence per attempt and allow prior-mode attempts to finish after switching modes. Keep the previous mode's key and signing secret until its attempts/events are reconciled. Do not commit `.env`, paste secrets into logs, or reuse a test credential in live mode. Configure `PAYMONGO_QR_EXPIRY_SECONDS` between 60 and 9000 seconds. `PAYMONGO_RECONCILE_INTERVAL` defaults to 60 seconds; connect/read timeouts default to 5/15 seconds and webhook tolerance to 300 seconds. Provider errors use bounded backoff.

Test-mode receipts mark the attempt simulated-complete without creating ledger revenue or changing memberships. Use the response's validated PayMongo test simulator URL. Provider response fields and QR cancellation support must be confirmed with the activated account before live collection; no sandbox or live API call is made merely by installing this code. If a response lacks a simulator URL, inspect its safe schema in the test environment and confirm the current provider documentation before adding a new field mapping.

## Webhooks

Register each environment's webhook once with PayMongo, using the public HTTPS endpoints:

- Test: `POST /payments/webhooks/paymongo/test/`
- Live: `POST /payments/webhooks/paymongo/live/`

Subscribe to `payment.paid`, `payment.failed`, and `qrph.expired`. Exempt these exact webhook routes from Cloudflare Access, interactive challenges, and CAPTCHA so provider POST requests can reach Django. Keep the routes public over HTTPS and rely on signature verification. Use separate signing secrets for test and live. Confirm delivery and signature validation before enabling customer QR checkout.

## Deployment and recovery

Back up PostgreSQL and verify the backup before deploying payment migrations. `docker compose up -d --build` starts the database, runs the committed migrations and static collection in the web container, and starts the payment worker after web reports migration readiness. Never run `makemigrations` as part of deployment; review and commit migration files with the code change.

The migrations are additive. To stop collection, set `PAYMONGO_ENABLED=False` while retaining this release's webhook and worker services. Do not roll the payment endpoints or worker back to a pre-integration image while provider intents remain unresolved. Do not delete or reverse payment records during rollback.

Owners with Django admin access (`is_staff=True`) can review attempts and events under `/admin/payments/`. Select unresolved attempts and use **Request safe provider cancellation**, or known provider intents and **Retry verification of known provider intents**. For pending webhook failures use **Retry pending webhook verification**. Actions schedule worker processing and never repeat an unknown creation request. Unknown requests without a provider ID require tracing the attempt UUID in the PayMongo dashboard/support before any replacement collection; no local action falsely declares cancellation. A confirmed paid receipt with `review_required=True` retains the payment but needs manual business resolution (for example, a deleted member). After resolving it, **Acknowledge paid receipt after manual review** records the Owner and time without extending membership or creating another payment. Rotate the repository's seeded default Owner password before public deployment. Record only provider/local IDs, timestamps, and outcomes in diagnostics.

WhiteNoise serves collected CSS/JS under Gunicorn with `DJANGO_DEBUG=False`. Existing media uploads continue through Django for this small deployment; a reverse proxy or object storage can replace that route separately. Keep the Gunicorn origin private to the trusted tunnel/proxy so clients cannot forge forwarded HTTPS headers.

For isolated unit tests, run `python manage.py test payments --settings=config.test_settings`; these use in-memory SQLite and clear inherited provider credentials. For full concurrency coverage use `GYMMS_TEST_DB_USER=<test-user> GYMMS_TEST_DB_HOST=<test-host> GYMMS_TEST_DB_PORT=<test-port> python manage.py test payments --settings=config.postgres_test_settings`. Optional `GYMMS_TEST_DB_PASSWORD` and `GYMMS_TEST_DB_NAME` select that dedicated test cluster; Django creates and drops a `test_` database. Never supply production credentials. Tests use fake provider resources and never call PayMongo.
