# Legacy Vite frontend (not used)

The first CRKL frontend prototype: a Vite + React Router app with static
placeholder pages (Home/About, Missions, Launches, Spacecraft). It was
replaced by the Next.js app in `frontend/` and no longer runs (its Vite and
React Router dependencies are not installed).

It was moved here from `frontend/` because Next.js refuses to build or run
while `frontend/src/pages/` sits next to `frontend/app/`
([#23](https://github.com/CRKL-SDSU/CRKL/issues/23)).

The Home page content (mission, team, project links) now lives on the
GitHub Pages site: `docs/index.html`.
