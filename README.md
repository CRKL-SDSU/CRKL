# CRKL
CS 514 Final Project

## Frontend API console

The `frontend/` directory contains a small Next.js app for testing the REST API
described in `specs/openapi/openapi.yaml`. It supports list and detail requests
for missions, agencies, spacecraft, and launches and displays JSON responses.

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL` in `.env.local` to the API server's `/api/v1`
base URL (for example, `http://localhost:8000/api/v1`). The frontend expects
the API to allow browser requests from the Next.js development origin.

The user-facing catalog is available at `http://localhost:3000/explore`. It
searches the selected resource collection returned by the API and displays
matching records as result cards. The API console remains available at `/`.
