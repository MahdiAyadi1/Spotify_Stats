# Spotify Stats

Upload your Spotify Extended streaming history export and explore your listening habits through a dashboard built around the data itself.

> **Status:** completed for the current scope and deployed. The project is built around a Python Azure Function API and a React + TypeScript front end, deployed to GitHub Pages and Azure Functions.

## What it does

- Reads a Spotify ZIP export and extracts the audio history JSON files.
- Treats any listening session under 30 seconds as a skip, and 30 seconds or more as a play.
- Ranks tracks by plays or listening time, and supports searches across the full result set.
- Shows richer listening insights beyond the top tracks, including artists, albums, yearly winners, discovery, sessions and platform habits.
- Includes a dark/light theme and a sidebar-based browsing experience with paginated views for long result sets.

## Current features

- Top tracks with global ranking, search and a podium view
- Top artists
- Top albums
- Most skipped tracks
- Yearly top tracks
- Discovery by month
- Listening sessions summary
- Listening habits, including platform breakdowns
- Summary statistics for plays, skips, listening time and distinct counts

## Get your data from Spotify

1. Go to your Spotify account's **Privacy settings** and request your data.
2. Select **Extended streaming history**.
3. Spotify prepares the export and sends it by email. This can take several days.
4. Download the ZIP and upload it as-is to the app; there is no need to unzip it.

## Privacy

Your history is processed in memory to compute the statistics and is **not stored or logged**. Nothing is kept after the response is returned.

## How it works

```
Browser (React + TypeScript)          GitHub Pages / Azure Functions
  upload the ZIP                 ──►    POST /api/stats   (Python Azure Function)
  render the dashboard           ◄──      unzip, aggregate, return JSON
```

- **Front end:** React + TypeScript, built to static files with Vite and deployed to GitHub Pages.
- **API:** a Python Azure Function that reads the `Streaming_History_Audio_*.json` files from the ZIP and returns aggregated statistics.
- **Hosting:** GitHub Pages for the UI and Azure Functions for the API backend.

## Tech stack

- React
- TypeScript
- Python 3.11
- Azure Functions
- Azure Static Web Apps
- Dev container setup for development

## Development

The project is developed in a dev container, so no local Node or Python install is required. Open the repository in the container and install the dependencies it expects.

```bash
# API (Python)
cd api
cp local.settings.json.example local.settings.json
func start            # http://localhost:7071
pytest                # unit tests
ruff check .          # lint

# Front end (React)
cd web
fnm env --use-on-cd --shell powershell | Out-String | Invoke-Expression
npm run dev           # http://localhost:5173, proxies /api to the function
npm run typecheck
npm test
```

## Status

- [x] Upload ZIP and validate export structure
- [x] Python aggregation for top tracks, artists, albums and skip analysis
- [x] React dashboard with upload, summary tiles, podium, search and theme support
- [x] Sidebar pages for each section and pagination for long lists
- [x] Most skipped, yearly, discovery, session and habits views
- [x] Deployment to GitHub Pages for the front end and Azure Functions for the API
- [x] Live deployment validation for the current application scope

## Project notes

See [AGENTS.md](AGENTS.md) for architecture decisions, constraints and coding conventions. The backend and frontend are intentionally kept loosely coupled by the API contract in the Python service and the TypeScript types in the web app.
