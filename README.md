# 2026 Lead Conversion Board — Vercel Version

This is the Streamlit-free Vercel version of the Lead Conversion Board.

## What changed

- Removed Streamlit completely.
- Existing Google Sheets remains the shared source of truth.
- Dashboard calculations, statuses, filters, lead forms, edit/delete, follow-up handling, bulk upload validation, and analytics charts are preserved.
- Browser UI replaces Streamlit widgets.
- Vercel serves `index.html` and runs `api/index.py` as the Python serverless API.
- No `.streamlit/secrets.toml` is included.

## Deploy

1. Upload this project to GitHub.
2. Import the repository into Vercel.
3. In **Vercel → Project → Settings → Environment Variables**, add:

### Recommended single JSON variable

`GOOGLE_SERVICE_ACCOUNT_JSON`

Value: the complete Google service-account JSON object as one JSON string.

Also add:

`GOOGLE_SHEET_NAME=Lead tracker`

`GOOGLE_WORKSHEET_NAME=Sheet 2026`

4. Make sure the Google service account email has access to the Google Sheet as an editor.
5. Deploy.

## Alternative environment variables

Instead of `GOOGLE_SERVICE_ACCOUNT_JSON`, the API also accepts:

- `GOOGLE_TYPE`
- `GOOGLE_PROJECT_ID`
- `GOOGLE_PRIVATE_KEY_ID`
- `GOOGLE_PRIVATE_KEY`
- `GOOGLE_CLIENT_EMAIL`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_AUTH_URI`
- `GOOGLE_TOKEN_URI`
- `GOOGLE_AUTH_PROVIDER_X509_CERT_URL`
- `GOOGLE_CLIENT_X509_CERT_URL`
- `GOOGLE_UNIVERSE_DOMAIN`

Never commit the service-account private key to GitHub.

## Local test

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

The frontend is static. The API is intended to run through Vercel's Python runtime.

## Important

Do not include the old `.streamlit` folder, `secrets.toml`, or `streamlit` dependency in the Vercel deployment.
