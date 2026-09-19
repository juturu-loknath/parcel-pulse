# ParcelPulse

**Smart Parcel Tracking & Notifications** — a mobile-first, bilingual (English + Telugu) parcel tracker for APSRTC Logistics.

## Why it exists

Booking receipts often arrive as photos. ParcelPulse turns that repetitive manual lookup into a small, understandable flow: upload a receipt or enter the LR number, confirm the phone number, and see the latest official APSRTC result.

## What is implemented

- FastAPI APSRTC provider adapter with timeouts, bounded retries, response validation, and normalized tracking events.
- React + TypeScript mobile experience: manual tracking, receipt upload, a confirmation-friendly form, result timeline, language preference, saved parcels, and in-app notification history.
- Local OCR using Tesseract when installed. It is intentionally advisory: users must confirm extracted data.
- SQLite persistence scoped to a randomly generated device identifier, with duplicate prevention and deletion.
- Automated polling remains disabled by default. Manual refresh is available.

## Architecture

```text
React / Vite → FastAPI API → TrackingProvider → APSRTCProvider → APSRTC API
                    ├── OCR service (Pillow + optional Tesseract)
                    └── SQLite saved parcels, isolated by device ID
```

No mobile number is placed in a frontend URL. The browser sends it in a POST body to the local backend, which alone contacts APSRTC.

## Local setup (macOS)

Prerequisites: Python 3.11+, Node 20+, and optionally `brew install tesseract` for receipt OCR.

```bash
cd /Users/juturuloknath/team-diag/parcel-pulse
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm install && cp .env.example .env.local && cd ..
uvicorn app.main:app --app-dir backend --reload
```

In a second terminal:

```bash
cd /Users/juturuloknath/team-diag/parcel-pulse/frontend
npm run dev
```

Open the address Vite prints (normally `http://localhost:5173`).

For normal local development and Android Wi-Fi testing, use Vite's development-only proxy. The API origin is intentionally not hardcoded in frontend source. Copy the provided local configuration:

```bash
cp frontend/.env.development.example frontend/.env.local
```

Restart Vite after changing this value. For a separately hosted frontend or production deployment, set `VITE_API_BASE_URL` to the FastAPI HTTPS origin instead.

## Android Wi-Fi testing

For local phone testing, use `frontend/.env.local` with an empty `VITE_API_BASE_URL` and a `DEV_API_PROXY_TARGET` pointing to the loopback FastAPI server. Vite then exposes the frontend to the network and securely proxies its relative `/api` requests on the Mac; FastAPI can remain bound to `127.0.0.1` and does not need permissive network CORS.

Start FastAPI with `--host 127.0.0.1` and Vite normally. Find the Mac's Wi-Fi IPv4 address in macOS **System Settings → Wi‑Fi → Details → TCP/IP**, then open `http://MAC_WIFI_IP:5173` in Android Chrome. The phone and Mac must use the same Wi‑Fi and macOS Firewall must allow incoming connections for the Vite/Node process.

The receipt picker uses `accept="image/*"` and `capture="environment"`, which Android Chrome normally presents as a camera option even over local HTTP because it is a user-initiated file selection. This app does not use `getUserMedia`. However, browser-installable PWA features, service workers, and direct camera APIs require a secure context; use HTTPS for those capabilities. A safe local HTTPS option is [mkcert](https://github.com/FiloSottile/mkcert): create a certificate for the Mac's Wi-Fi IP, configure Vite's `server.https` with it, and install/trust mkcert's local CA on the test phone. Do not use an untrusted certificate warning bypass for routine testing.

## PWA and Android installation

ParcelPulse includes a web manifest, 192px/512px app icons, and a service worker. On an Android browser over HTTPS, open ParcelPulse and choose **Install app** or **Add to Home screen**. The receipt input uses `accept="image/*"` with `capture="environment"`; compatible mobile browsers offer the camera as a photo source, while others present the normal picker.

The service worker caches the app shell only. Tracking API responses, phone numbers, receipt uploads, and status results are never cached by the service worker. A network connection is still required to check a parcel.

## Deployment (Vercel + FastAPI)

Deploy `frontend/` to Vercel with build command `npm run build` and output directory `dist`. Configure `VITE_API_BASE_URL` in Vercel to the HTTPS origin of the separately deployed FastAPI API, then redeploy so Vite embeds that public build-time value.

Deploy `backend/` on a Python host that supports outbound HTTPS requests and persistent environment variables. Set:

- `DATABASE_URL` to a managed PostgreSQL URL, preferably `postgresql+psycopg://...?...sslmode=require`.
- `CORS_ORIGINS` to the exact Vercel frontend origin. Multiple comma-separated origins are supported.
- `APSRTC_TIMEOUT_SECONDS`, `APSRTC_MAX_RETRIES`, and `MAX_UPLOAD_MB` as appropriate.
- `ENABLE_BACKGROUND_MONITORING=false` until APSRTC confirms permitted automated access.

SQLite remains the zero-configuration local default. PostgreSQL URLs from common hosts using `postgres://` or `postgresql://` are normalized to SQLAlchemy's `psycopg` dialect. For production, run schema migrations as part of deployment rather than relying on the lightweight local `create_all` startup path.

### Private accounts and PostgreSQL setup

ParcelPulse uses FastAPI-managed username/password accounts, not Supabase Auth. The production database starts empty; do not point a migration at a legacy SQLite file. Set `DATABASE_URL` to the Supabase PostgreSQL connection string, `ENVIRONMENT=production`, a unique `SESSION_SECRET` of at least 32 random bytes, and `AUTH_COOKIE_SECURE=true`. Run `alembic -c backend/alembic.ini upgrade head` once against the empty cloud database.

Sign-up is off by default. To let the second private user create an account, set `SIGNUP_ENABLED=true` and a random `PRIVATE_SIGNUP_CODE` only in the backend host's secret environment. The code never belongs in Vercel, source control, logs, or the frontend. The backend verifies it in constant time, throttles failed attempts, and serializes signup requests so a maximum of two accounts can exist. Once both accounts are created, set `SIGNUP_ENABLED=false` (or remove both signup variables) and restart the backend. Existing signed-in sessions and accounts remain valid. Passwords must be non-empty and are hashed with Argon2id; the UI gives non-blocking guidance for easily guessed passwords.

For cookie reliability, use HTTPS custom subdomains under the same site, such as `app.example.com` on Vercel and `api.example.com` for FastAPI. Configure `CORS_ORIGINS` with the exact app URL. There is no public password-reset endpoint; an administrator verifies the person out of band, then runs `cd backend && python -m scripts.reset_password` on a trusted machine.

### Push-notification limitations

Browser push requires HTTPS, a service worker, a user gesture, permission from the device, and a backend that stores Web Push subscriptions and sends messages with VAPID keys. This project includes the installable PWA/service-worker foundation and in-app notification history, but does not yet collect subscriptions or send push messages. Android browser behavior differs by browser and device battery policies; notifications are not guaranteed. No recurring APSRTC polling is enabled.

## Testing

```bash
cd /Users/juturuloknath/team-diag/parcel-pulse/backend
pytest
cd ../frontend && npm run build
```

Tests mock APSRTC responses; they do not contact the live tracking service.

## Privacy and limitations

- Receipt images are processed in memory and are not stored.
- Production saved parcels are scoped to authenticated users in PostgreSQL. SQLite remains local-development-only; do not import legacy parcels unless you separately plan and review a migration.
- Browser notifications and background monitoring are not enabled yet. Automated APSRTC polling needs explicit permission from APSRTC before it can be responsibly enabled.
- APSRTC is the only implemented provider. ParcelPulse never invents status information and shows upstream failures separately from the last verified state.

## Screenshots

Add screenshots made with non-personal sample data before publishing. Do not commit receipt images or real tracking data.

## License

This project uses the [MIT License](LICENSE), a permissive license suitable for an open-source portfolio project. Please confirm it matches your preferred licensing approach before publishing.

## Future work

- Optional account-management improvements beyond the two-user private model
- Permissioned background scheduler and Web Push subscription delivery
- More receipt templates and OCR accuracy evaluation
- Additional carrier providers through the existing provider interface
