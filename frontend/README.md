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

### Configure the private backend

The browser calls same-origin `/api/v1` paths. Next.js proxies those requests
server-side to the backend, so the backend URL must not use a `NEXT_PUBLIC_*`
variable:

```dotenv
CRKL_BACKEND_URL=http://127.0.0.1:8000
```

In a private network deployment, use the backend service name instead:

```dotenv
CRKL_BACKEND_URL=http://backend:8000
```

Do not publish the backend port publicly. The frontend server is the only
component that should reach it.

The BFF entrypoint is `app/api/[...path]/route.ts`. It currently forwards
read-only requests for missions, agencies, spacecraft, and launches. The
browser calls `/api/v1/...`; only the Next.js server uses `CRKL_BACKEND_URL`.

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
