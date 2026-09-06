# Identity Screening System

Decision-support prototype for authorized human review of identity and travel documents. It reports bounded indicators and never makes legal, criminal, or definitive authenticity determinations.

## Local development

Start the API:

```powershell
Push-Location backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload
Pop-Location
```

Start the frontend in another terminal:

```powershell
Push-Location frontend
npm install
npm run dev
Pop-Location
```

For a custom API address, copy `frontend/.env.example` to `frontend/.env.local` and change `NEXT_PUBLIC_API_BASE_URL`.

Open `http://localhost:3000`, upload a synthetic JPEG/PNG/PDF fixture, and review the explainable demonstration result.

### OCR prerequisite

The Python adapter uses Tesseract OCR. On Windows, install the Tesseract executable and ensure `tesseract.exe` is on `PATH`, for example:

```powershell
winget install UB-Mannheim.TesseractOCR
```

Without that executable, image preprocessing and metadata analysis still run, while OCR is returned as `unavailable` rather than inventing fields. The backend Dockerfile installs Tesseract automatically.

### Face comparison assistance

The optional `Presented Person Image` is validated as a temporary PNG/JPEG input. The backend uses OpenCV's bundled Haar cascade to detect zero, one, or multiple faces. When exactly one face is detected in each image, it returns a normalized grayscale correlation signal for authorized human review. This signal never confirms identity, changes risk, or creates a government/security decision. Face images are processed in memory, embeddings are not generated or returned, and face verification remains assistive with human review required.

Direct API usage:

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/face/compare -F "document=@document.png" -F "presented_person=@person.png"
```

## Docker

```powershell
docker compose up --build
```

The API is at `http://localhost:8000` and the frontend is at `http://localhost:3000`.

The baseline OCR, tampering, and face adapters are deliberately labeled unavailable or demonstration mode. No government database connection is present.

### Secure audit and integrity

Each screening creates a server-generated case ID, hashes the original uploaded bytes with SHA-256, records lifecycle module events, and exposes the result through `GET /api/v1/cases/{case_id}`. Use `POST /api/v1/integrity/verify` with an image or PDF and an optional `expected_hash` to compare file integrity. A mismatch means the supplied bytes differ; it does not establish fraud and requires human review.

The SQLAlchemy models and Alembic migration contain the PostgreSQL persistence fields. Until PostgreSQL is configured and connected, the running demonstration repository is explicitly in-memory and does not persist raw documents, biometric data, or OCR content. No blockchain network or transaction is claimed.

### Authentication

Authentication uses short-lived JWT bearer tokens and Argon2 password hashes. Set these environment variables before starting the backend:

```powershell
$env:SCREENING_JWT_SECRET_KEY = "generate-a-long-random-secret"
$env:SCREENING_DEMO_OFFICER_PASSWORD = "use-a-local-demo-password"
$env:SCREENING_DEMO_ADMIN_PASSWORD = "use-a-different-local-demo-password"
$env:SCREENING_REFERENCE_PROFILE_LOCK_SECRET = "set-a-second-admin-protection-secret"
```

The environment-created accounts `demo.officer` and `demo.admin` are demonstration accounts only. The login endpoint is `POST /api/v1/auth/login`; protected screening, face, integrity, document, and case endpoints require its bearer token. Logout is client-side session clearing, and no government authentication is claimed.

### Reference profile security

The project now includes a protected administrative reference profile workflow. Only `ADMIN` users can create or mutate locked reference profiles. Replacing or deleting a locked profile requires the backend-secret check from `SCREENING_REFERENCE_PROFILE_LOCK_SECRET`, and this value is never exposed in the frontend or committed to source control.

Example admin flow:

```powershell
POST /api/v1/reference-profiles
{
  "document_type": "passport",
  "profile_name": "passport-demo-profile",
  "document_hash": "sha256:...",
  "profile_summary": {"aspect_ratio": 1.4, "layout_consistency": 95},
  "characteristics": {"major_regions": 6},
  "authorization_code": "set-a-second-admin-protection-secret"
}
```

The API returns the profile with `status: "LOCKED"` and `is_locked: true`. Replacement or unlock operations require the same secret and admin authorization.

### Case management

Successful screenings create a `PROCESSING` case, record module lifecycle events, then complete as `COMPLETED`. Failed file validation creates a failed case and returns its case ID in the `X-Case-ID` response header. Use `GET /api/v1/cases?page=1&page_size=20` with optional `search`, `risk_level`, `document_type`, and `status` filters, then open `GET /api/v1/cases/{case_id}` for the stored structured result and audit trail. History responses contain hashes and screening evidence only; raw document files and biometric data are not returned.

### PDF reports

Open a case from Screening History and choose `Export PDF`. The authenticated endpoint `GET /api/v1/cases/{case_id}/report` generates an in-memory ReportLab PDF from the stored case evidence and records a `REPORT_GENERATED` audit event. Reports contain case metadata, integrity hash, module summaries, risk reasons, and audit events, but omit raw OCR text, passwords, tokens, filesystem paths, credentials, and biometric embeddings.

The frontend uses a lightweight CSS command-center treatment: deep-space gradients, a star/grid field, glass panels, cyan security accents, orbital entry marker, scan-line intake, hover depth, and reduced-motion support. No WebGL or heavy 3D dependency is used.