# CRKL Frontend

This directory contains the Next.js frontend for exploring the CRKL REST API.

## Prerequisites

- Node.js and npm
- A running CRKL API server

## Run locally

From the repository root:

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

The development server runs at [http://localhost:3000](http://localhost:3000).
Open `/` for the API console or `/explore` for the user-facing catalog.
On `/explore`, click a result to open its detail overlay. Related missions,
agencies, spacecraft, and launches are clickable, and the overlay provides
Back and Forward navigation through the records you visit.

### Configure the API URL

Set `NEXT_PUBLIC_API_BASE_URL` in `.env.local` to the API server's `/api/v1`
base URL. The default points to an API running locally on port 8000:

```dotenv
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

The API must allow browser requests from the Next.js development origin
(`http://localhost:3000`).

## Other commands

```bash
npm run build      # Create a production build
npm run start      # Serve the production build
npm run typecheck  # Run the TypeScript checker
npm test           # Run the frontend test suite once
npm run test:watch # Run tests in watch mode
```

## Tests

Frontend tests use Vitest and Testing Library. They render components and mock
API requests, so the backend and MySQL do not need to be running.

From this directory:

```bash
npm install
npm run typecheck
npm test
```

GitHub Actions runs the type check and test suite automatically for pushes and
pull requests.
