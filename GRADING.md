# Grading guide

This guide runs CRKL-Space with Docker, loads the real data, and walks
through what to try. It takes about 10 minutes, most of it the first build.

## 1. Requirements

- [Docker Desktop](https://www.docker.com/products/docker-desktop/), running
- Git
- Port 3000 free

You don't need MySQL, Python, or Node.js.

## 2. Start

```bash
git clone https://github.com/CRKL-SDSU/CRKL.git
cd CRKL
cp .env.example .env
```

Open `.env` and replace both placeholder passwords with any passwords of your
own (no single quotes). Then start the services:

```bash
docker compose up --build
```

Wait until the log shows the frontend is ready. The first build takes a few
minutes. Leave this terminal open.

The database starts **empty**: the tables exist, but there are no records
until you load data in the next step.

## 3. Load the data

In a second terminal, in the same `CRKL` folder:

```bash
docker compose run --rm load-real-data
```

This loads real missions, agencies, spacecraft, and launches from the
[Launch Library 2](https://thespacedevs.com/llapi) snapshot files in
`backend/data/snapshot/`. It doesn't call the API, and it finishes in under a
minute. It prints `Real data loaded.` when done.

Optional, for comparison: the fictional sample data used by our tests.

| To… | Run |
| --- | --- |
| Add the real data (keeps what is already there) | `docker compose run --rm load-real-data` |
| Replace all data with the real data | `docker compose run --rm load-real-data --replace` |
| Replace all data with the sample data | `docker compose run --rm load-dummy-data --replace` |

`--replace` deletes every mission, agency, spacecraft, launch, and tag first.
Records from the sample data show **Source: Dummy**; real records show
**Source: Launch Library 2**.

## 4. Try it

Open <http://localhost:3000/explore>.

1. **Search launches.** Select **Launches** and search for `"Apollo 11"` (with
   the quotes). Each result card shows the launch date, status, launch
   provider, image, and source.
2. **Open a record.** Click **Saturn V | Apollo 11**. The detail panel shows
   the full image with its credit and license, the launch window, and the
   related mission **Apollo 11**. Click the mission to move to it, and use
   **Back** and **Forward** to move between records.
3. **Related records.** Select **Launches** and search for `lunar`. With
   **Include related records** checked, launches also match through their
   missions, so launches whose mission description mentions "lunar" appear.
   Uncheck it and search again: only the few launches with "lunar" in their own
   fields remain.
4. **Search syntax.** Try `apollo -soyuz`, `apollo OR gemini`, and
   `"south pole"`. See [Search syntax and tags](README.md#search-syntax-and-tags).
5. **Tags.** Open a mission and add a tag, such as `moon`. Then search for
   `tag:moon` in Missions, and in Launches, which match through their missions.
6. **AI prompt.** In a detail panel, click the small copy icon at the bottom
   right. It copies a prompt for an AI assistant with the record's details and
   links to its Launch Library 2 data.

The API console at <http://localhost:3000/> shows the raw JSON for list and
detail requests.

## 5. About the real data

- Relationships are loaded as Launch Library 2 records them. Most real agencies
  and spacecraft have few or no related missions; see **Relationships** under
  [Data source and license](README.md#data-source-and-license).
- Missions from Launch Library 2 have no status of their own, so their status
  shows "—".

## 6. Stop and reset

| To… | Run |
| --- | --- |
| Stop (data is kept) | <kbd>Ctrl</kbd>+<kbd>C</kbd>, then `docker compose down` |
| Start again | `docker compose up` |
| Start over with an empty database | `docker compose down -v`, then `docker compose up` |

## 7. Tests

The test suites need no running services. See [Tests](README.md#tests) in the
README; GitHub Actions also runs them on every push.
