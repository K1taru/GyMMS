# PayMongo QR Ph deployment

PayMongo support is opt-in. Keep `PAYMONGO_ENABLED=False` until the account is activated, credentials are installed, webhook delivery is verified, and the payment worker is running. The background worker and settlement/reconciliation processing run even while customer QR checkout is disabled.

## Setup on your Docker deployment

1. **Prepare your PayMongo account.** Complete merchant activation and confirm QR Ph is available in the live account's payment methods. Open Developers → API Keys and obtain the test secret key. This integration uses API secret keys on Django; you do not need to paste a public key into templates or JavaScript. Official references: [QR Ph API](https://docs.paymongo.com/docs/payment-acceptance-qr-ph-api) and [launch checklist](https://docs.paymongo.com/docs/payment-acceptance-go-live-checklist).

2. **Edit the private `.env`.** On an existing deployment, keep the working PostgreSQL variables and password; do not copy the example over your runtime file. `.env.example` is only a safe template. The Django names are `DJANGO_SECRET_KEY` and `DJANGO_DEBUG`; a Django key is different from a PayMongo key. Set the following test-mode values locally, using your actual secrets only in `.env`:

   ```dotenv
   PAYMONGO_ENABLED=False
   PAYMONGO_MODE=test
   PAYMONGO_SECRET_KEY_TEST=sk_test_REPLACE_WITH_YOUR_KEY
   PAYMONGO_WEBHOOK_SECRET_TEST=
   ```

   For public deployment set `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS` to your public hostname (without `https://`), `DJANGO_CSRF_TRUSTED_ORIGINS` to its `https://` origin, and `DJANGO_SECURE_SSL_REDIRECT=True`. Keep a strong private Django secret. Keep `.env` permissions restricted (`chmod 600 .env`). If real credentials appeared in a committed/shared `.env.example`, removing them from the latest file does not remove them from Git history: rotate exposed credentials through their owning systems. Changing a database password in `.env` alone does not change the password of an existing PostgreSQL volume.

3. **Prepare PostgreSQL 18 and deploy.** Existing installations must first follow the [Docker cutover guide](docker.md#cutover-from-postgresql-16). Disable new checkouts and resolve every outstanding provider payment/event before switching to the empty database. Keep the old PostgreSQL volume and backups. Fresh installations follow [first setup](setup.md#first-setup). After that preparation, from the project directory:

   ```bash
   docker compose config --quiet
   docker compose build web
   docker compose up -d --wait db
   docker compose run --rm initialize
   docker compose up -d --wait web payment-worker
   docker compose ps
   docker compose exec web python manage.py check_paymongo
   ```

   Initialization applies committed migrations; web collects static assets and starts Gunicorn. The worker waits for successful initialization and HTTP/database readiness. The first configuration check will report the missing webhook secret until you register the endpoint. It does not contact PayMongo or PostgreSQL and never displays credential values. Do not run `docker compose down -v`; that removes the database volume.

4. **Register the test webhook.** In PayMongo Developers → Webhooks, add `https://YOUR_HOST/payments/webhooks/paymongo/test/`. Subscribe to `payment.paid`, `payment.failed`, and `qrph.expired` (if available in the account's event list). The handler also accepts `payment_intent.succeeded` and `payment_intent.awaiting_payment_method`; these can supplement the QR expiry event. Use one endpoint per environment, not one per checkout. Copy this endpoint's webhook signing secret into `PAYMONGO_WEBHOOK_SECRET_TEST`. API and webhook secrets are different. Allow signed POST requests through the tunnel/proxy without login, CAPTCHA, or Cloudflare Access challenges on this exact route. [PayMongo webhook setup](https://docs.paymongo.com/docs/developer-tools-webhook-setup-management)

5. **Reload configuration and check it.** Recreate the web and worker containers after editing `.env`; `docker compose restart` does not reload container environment variables:

   ```bash
   docker compose up -d --force-recreate --no-deps web payment-worker
   docker compose exec web python manage.py check_paymongo --strict
   docker compose logs --tail=100 web payment-worker
   ```

   Keep logs private. When configuration checks pass and the worker is running, set `PAYMONGO_ENABLED=True` in `.env` for the test-mode smoke test, then repeat the recreation command. If production HTTPS validation fails, correct the hostname/origin/proxy configuration before proceeding.

6. **Run the provider smoke test.** Log in as staff, select a fixture member or walk-in and a pricing plan, choose **QR Ph — GCash, GoTyme, Maya**, and submit. The modal must progress from preparing to the TEST simulator link. Never scan a test QR: PayMongo warns that test QR images can process real payments. Use the simulator, verify delivery in PayMongo's webhook dashboard, then verify that the attempt is simulated-complete with no real ledger entry or membership extension. Exercise failure, cancellation, minimize/reopen, navigation, refresh, and multi-tab recovery. The server forwards the intent's `client_key` when PayMongo provides one, but actual secret-key attachment permissions and cancellation behavior must still be validated against your account. If generation or cancellation is rejected, inspect the attempt in admin and confirm the provider contract rather than recording a manual digital success. [PayMongo QR testing warning](https://docs.paymongo.com/docs/payment-acceptance-testing)

7. **Switch to live mode.** First set `PAYMONGO_ENABLED=False` and recreate the containers. Add the live secret key as `PAYMONGO_SECRET_KEY_LIVE`. Register `https://YOUR_HOST/payments/webhooks/paymongo/live/` in live mode and save its separate signing secret as `PAYMONGO_WEBHOOK_SECRET_LIVE`. Set `PAYMONGO_MODE=live`, recreate the containers, then run:

   ```bash
   docker compose exec web python manage.py check_paymongo --strict --production
   ```

   This is an offline check, not proof of provider connectivity or account activation. Keep the old test credentials while test events remain pending. After live checks pass, set `PAYMONGO_ENABLED=True` and recreate again. Perform a controlled real QR payment yourself, verifying the provider receipt, exactly one transaction, and the expected membership result. Confirm scanning with GCash, GoTyme, and Maya before broad staff use. The common QR accepts all supported apps; the ledger reports QR Ph.

8. **Operate and recover.** Monitor the payment worker and webhook deliveries. Owners can inspect attempts/events in Django admin and use the safe recovery actions described below. To stop new QR payments, set `PAYMONGO_ENABLED=False` and recreate web/worker; keep the webhook route and worker online so existing payments still settle.

## Payment flow and safety

- Staff can record cash as a walk-in payment. QR Ph is a separate option.
- Every supported wallet scans the same QR Ph code; the payer chooses their wallet in their app.
- Permit one active QR checkout per staff member. A pending QR is not revenue and must not extend a membership.
- Minimizing only hides the modal. Staff can cancel their own payment process without Owner approval. Once GyMMS saves cancellation, the modal, floating badge and browser recovery pointer are cleared and the staff member can immediately collect another QR or Cash payment, including for the same member. A failed cancellation request retains browser recovery until GyMMS confirms it.
- Local staff cancellation (`staff_cancelled_at`) releases checkout immediately; `is_unresolved` still describes the provider outcome, while `blocks_checkout` describes whether the staff workflow is blocked. Cancelling locally does not guarantee PayMongo has revoked the QR. Tell the customer not to use the old QR. The worker continues cancellation and verification independently, including after a rejection or timeout.
- A verified payment received after local staff cancellation is recorded exactly once as received funds and flagged for refund or credit review, without extending membership or creating a check-in. Replacement payments work normally. Financial review never restores the old popup or blocks checkout; refunds are not automatic.
- Provider webhooks and reconciliation establish settlement. A browser redirect or screenshot is never proof of payment.
- In PayMongo test mode, do not scan test QR images with a real wallet. Use the provider's test URL/simulator flow; the customer UI must hide test QR images.

## Environment

For a new installation, copy `.env.example` to `.env`; preserve and edit the existing private `.env` on an installed system. Keep `DJANGO_DEBUG=True` only for local development. Production must set `DJANGO_DEBUG=False`, a newly generated `DJANGO_SECRET_KEY`, exact `DJANGO_ALLOWED_HOSTS`, and HTTPS `DJANGO_CSRF_TRUSTED_ORIGINS` such as `https://gym.example.com`. Set the domain to the public Cloudflare hostname. The app trusts Cloudflare's `X-Forwarded-Proto` header, enables secure session and CSRF cookies, redirects to HTTPS, and enables HSTS when debug is off. Ensure the Cloudflare tunnel forwards the original scheme and serves the app over HTTPS.

Choose `PAYMONGO_MODE=test` or `live`. Install the corresponding API secret in `PAYMONGO_SECRET_KEY` and webhook signing secret in `PAYMONGO_WEBHOOK_SECRET_TEST` or `PAYMONGO_WEBHOOK_SECRET_LIVE`. Alternatively set `PAYMONGO_SECRET_KEY_TEST` and `PAYMONGO_SECRET_KEY_LIVE`; these take precedence per attempt and allow prior-mode attempts to finish after switching modes. Keep the previous mode's key and signing secret until its attempts/events are reconciled. Do not commit `.env`, paste secrets into logs, or reuse a test credential in live mode. Configure `PAYMONGO_QR_EXPIRY_SECONDS` between 60 and 9000 seconds. `PAYMONGO_RECONCILE_INTERVAL` defaults to 60 seconds; connect/read timeouts default to 5/15 seconds and webhook tolerance to 300 seconds. Provider errors use bounded backoff.

Test-mode receipts mark the attempt simulated-complete without creating ledger revenue or changing memberships. Use the response's validated PayMongo test simulator URL. Provider response fields and QR cancellation support must be confirmed with the activated account before live collection; no sandbox or live API call is made merely by installing this code. If a response lacks a simulator URL, inspect its safe schema in the test environment and confirm the current provider documentation before adding a new field mapping.

## Webhooks

Register each environment's webhook once with PayMongo, using the public HTTPS endpoints:

- Test: `POST /payments/webhooks/paymongo/test/`
- Live: `POST /payments/webhooks/paymongo/live/`

Subscribe to `payment.paid`, `payment.failed`, and `qrph.expired`. Exempt these exact webhook routes from Cloudflare Access, interactive challenges, and CAPTCHA so provider POST requests can reach Django. Keep the routes public over HTTPS and rely on signature verification. Use separate signing secrets for test and live. Confirm delivery and signature validation before enabling customer QR checkout.

## Deployment and recovery

Back up PostgreSQL and verify a restore before deploying payment migrations. Existing installations must complete the [PostgreSQL 18 cutover](docker.md#cutover-from-postgresql-16) before using the refreshed Compose configuration. It creates a separate empty database and retains old storage. Follow the [setup guide's maintenance sequence](setup.md#routine-maintenance) for later releases: stop application services, run initialization, then recreate web and worker. Initialization applies migrations; web collects static assets and exposes HTTP readiness before worker startup. Never run `makemigrations` during deployment; review and commit migration files with the code change.

Future schema changes use normal incremental migrations. Startup never seeds pricing or an Owner; create the Owner with `createsuperuser` and configure pricing explicitly. The optional `seed_pricing` command overwrites matching prices and reactivates plans, and duplicate durations can make it fail. To stop collection, set `PAYMONGO_ENABLED=False` while retaining this release's webhook and worker services. Do not roll the payment endpoints or worker back to a pre-integration image while provider intents remain unresolved. Do not delete or reverse payment records during rollback.

The staff-cancellation upgrade includes migration `0003_staff_cancellation`. It releases existing unpaid unresolved staff cancellation requests, preserving their provider state and queuing reconciliation. Its timestamp uses the last recorded update for these older requests. Build first, then stop both application services while applying the migration and deploy the web/worker together:

```bash
docker compose build web
docker compose stop web payment-worker
docker compose run --rm initialize
docker compose up -d --force-recreate --no-deps web payment-worker
docker compose exec web python manage.py check_paymongo --strict --production
```

Keep the database, test/live credentials, and webhook routes in place. Do not downgrade across this migration after staff have created replacement checkouts: the previous database constraint and code cannot represent the newly released workflows.

Owners with Django admin access (`is_staff=True`) can review attempts and events under `/admin/payments/`, including the staff cancellation timestamp and review flag. Select active attempts and use **Request safe provider cancellation**, or known provider intents and **Retry verification of known provider intents**. For pending webhook failures use **Retry pending webhook verification**. Actions schedule worker processing and never repeat an unknown creation request. Unknown requests without a provider ID remain in the audit trail for tracing through PayMongo; local staff cancellation can still release checkout without asserting provider cancellation. A confirmed paid receipt with `review_required=True` retains the payment but needs manual business resolution (for example, a late receipt after staff cancellation or a deleted member). After resolving it, **Acknowledge paid receipt after manual review** records the Owner and time without extending membership or creating another payment. Financial review is separate from permission to cancel a staff workflow. There is no seeded Owner or default password; create your Owner explicitly with `createsuperuser`. Record only provider/local IDs, timestamps, and outcomes in diagnostics.

WhiteNoise serves collected CSS/JS under Gunicorn with `DJANGO_DEBUG=False`. Existing media uploads continue through Django for this small deployment; a reverse proxy or object storage can replace that route separately. Keep the Gunicorn origin private to the trusted tunnel/proxy so clients cannot forge forwarded HTTPS headers.

For isolated unit tests, run `python manage.py test payments --settings=config.test_settings`; these use in-memory SQLite and clear inherited provider credentials. For full concurrency coverage use `GYMMS_TEST_DB_USER=<test-user> GYMMS_TEST_DB_HOST=<test-host> GYMMS_TEST_DB_PORT=<test-port> python manage.py test payments --settings=config.postgres_test_settings`. Optional `GYMMS_TEST_DB_PASSWORD` and `GYMMS_TEST_DB_NAME` select that dedicated test cluster; Django creates and drops a `test_` database. Never supply production credentials. Tests use fake provider resources and never call PayMongo.
