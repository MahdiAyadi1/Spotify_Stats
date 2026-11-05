# Spotify Stats

Upload your Spotify listening history and get statistics and charts about what you actually listen to.

> **Status:** in development. The first version shows your top tracks; more statistics are planned. Not deployed yet.

## What it does

- Reads the _Extended streaming history_ export that Spotify provides.
- Ranks **every** track you played, by number of plays or by listening time.
- Search any track and see its rank across your whole history.
- Light and dark themes.

A play counts when you listened for at least 30 seconds, like Spotify's own definition. Anything shorter counts as a skip.

Planned: most skipped tracks, top artists, listening over time, and more charts.

## Get your data from Spotify

1. Go to your Spotify account's **Privacy settings** and request your data.
2. Select **Extended streaming history**.
3. Spotify prepares the export and sends it by email. This can take several days.
4. Download the ZIP. You upload it as-is; there is no need to unzip it.

## Privacy

Your history is processed in memory to compute the statistics and is **not stored or logged**. Nothing is kept after the response is returned.

## How it works

```
Browser (React)                         Azure Static Web Apps
  upload the ZIP                 ──►    POST /api/stats   (Python Azure Function)
  render charts from JSON        ◄──      unzip, aggregate, return JSON
```

- **Front end:** React and TypeScript, built to static files.
- **API:** a Python Azure Function that reads the `Streaming_History_Audio_*.json` files from the ZIP one at a time and returns the aggregated statistics.
- **Hosting:** Azure Static Web Apps (Free plan), with the function deployed as its managed API.

## Tech stack

- React, TypeScript
- Python 3.11, Azure Functions
- Azure Static Web Apps
- Dev container for development

## Development

The project is developed in a dev container, so no local Node or Python install is needed. Open the repository in the container; it installs the dependencies on creation.

```bash
# API (Python)
cd api
cp local.settings.json.example local.settings.json
func start            # http://localhost:7071
pytest                # unit tests
ruff check .          # lint

# Front end (React)
cd web
npm run dev           # http://localhost:5173, proxies /api to the function
npm run typecheck
npm test
```

## Roadmap

- [x] Python function that returns top tracks and most skipped from a Spotify export ZIP
- [ ] Test the upload with a real export on a deployed stub (size, duration, memory)
- [x] React front end, part one: upload, summary, ranked list
- [x] React front end, part two: podium, plays / time toggle, search, theme toggle, most skipped
- [ ] Deploy to Azure Static Web Apps
- [ ] Top artists
- [ ] Listening history over time

## Project notes

See [AGENTS.md](AGENTS.md) for architecture decisions, constraints and coding conventions.
