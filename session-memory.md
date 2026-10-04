# CRKL Session Memory

## Runtime

- MySQL uses the compatible Homebrew `mysql@8.0` service on `127.0.0.1:3306`.
- The FastAPI backend runs from `backend/code` with `python3 main.py` on port `8000`.
- The Next.js frontend runs from `frontend` with `npm run dev` on port `3000`.
- `CRKL_MYSQL_PASSWORD` is loaded through `direnv` from the repository `.envrc`.
- The backend health endpoint is `GET /api/v1/health`.

## Search behavior

- Resource list endpoints accept `related=true|false`; the default is `true`.
- Related search expands searches across linked missions, agencies, spacecraft, and launches.
- The frontend `/explore` page exposes an “Include related records” checkbox enabled by default.
- The checkbox sends the `related` query parameter and supports exact-table-only searches when disabled.

## Detail navigation

- Search result cards on `/explore` open an overlay detail view using the resource detail endpoints.
- Detail overlays display scalar fields and related record collections returned by the backend.
- Related missions, agencies, spacecraft, and launches are clickable and open another detail in the same overlay.
- The overlay tracks visited records with Back and Forward controls; opening a new record after going back truncates forward history.
- The overlay can be closed with the close button, outside click, or `Escape`.

## Tests and CI

- Backend tests are in `backend/tests/test_api.py`, mock database access, and cover list search, related detail responses, and missing-record `404` responses.
- Backend CI dependencies are in `backend/requirements-ci.txt`.
- Frontend tests are in `frontend/app/explore/page.test.tsx` and cover related search, detail overlay navigation, Back/Forward history, and Escape-to-close behavior.
- Frontend test configuration is in `frontend/vitest.config.ts` and `frontend/vitest.setup.ts`.
- Frontend commands are `npm run typecheck`, `npm test`, and `npm run test:watch`.
- GitHub Actions runs both backend and frontend checks from `.github/workflows/tests.yml` on pushes and pull requests.
- Tests do not require running MySQL, the backend server, or the frontend server.

## Documentation

- Root setup and test instructions are in `README.md`.
- Backend setup, configuration, runtime, and test instructions are in `backend/README.md`.
- Frontend setup, runtime, and test instructions are in `frontend/README.md`.
