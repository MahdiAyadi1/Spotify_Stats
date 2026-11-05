import { useEffect, useMemo, useState, type ChangeEvent } from "react";
import { fetchStats, type StatsResponse } from "./api";
import { TrackList } from "./components/TrackList";
import { formatCount, formatListeningTime } from "./format";
import { filterTracks, sortTracks, type TrackMetric } from "./lib/trackView";

type Status =
  | { kind: "idle" }
  | { kind: "loading"; fileName: string }
  | { kind: "error"; message: string }
  | { kind: "done"; stats: StatsResponse };

type ThemeMode = "system" | "light" | "dark";

export default function App() {
  const [status, setStatus] = useState<Status>({ kind: "idle" });

  async function handleExportChosen(event: ChangeEvent<HTMLInputElement>) {
    const exportZip = event.target.files?.[0];
    event.target.value = ""; // lets the same file be chosen again
    if (!exportZip) {
      return;
    }

    setStatus({ kind: "loading", fileName: exportZip.name });
    try {
      setStatus({ kind: "done", stats: await fetchStats(exportZip) });
    } catch (error) {
      setStatus({
        kind: "error",
        message: error instanceof Error ? error.message : "Something went wrong.",
      });
    }
  }

  return (
    <main>
      <h1>Spotify Stats</h1>
      <p>
        Choose the ZIP of your Spotify <em>Extended streaming history</em>. It is sent to the server
        to compute the statistics and is not stored.
      </p>
      <input
        type="file"
        accept=".zip,application/zip"
        onChange={handleExportChosen}
        disabled={status.kind === "loading"}
      />

      {status.kind === "loading" && <p>Analysing {status.fileName}…</p>}
      {status.kind === "error" && <p role="alert">{status.message}</p>}
      {status.kind === "done" && <Results stats={status.stats} />}
    </main>
  );
}

function Results({ stats }: { stats: StatsResponse }) {
  const [metric, setMetric] = useState<TrackMetric>("plays");
  const [searchQuery, setSearchQuery] = useState("");
  const [themeMode, setThemeMode] = useState<ThemeMode>("system");

  useEffect(() => {
    const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const resolvedTheme = themeMode === "system" ? (systemPrefersDark ? "dark" : "light") : themeMode;
    document.documentElement.dataset.theme = resolvedTheme;
    document.documentElement.style.colorScheme = resolvedTheme;
  }, [themeMode]);

  const rankedTracks = useMemo(() => sortTracks(stats.top_tracks, metric), [stats.top_tracks, metric]);
  const podiumTracks = useMemo(() => rankedTracks.slice(0, 3), [rankedTracks]);
  const filteredTracks = useMemo(() => filterTracks(rankedTracks, searchQuery), [rankedTracks, searchQuery]);

  if (stats.top_tracks.length === 0) {
    return <p>No plays found in this export.</p>;
  }

  return (
    <>
      <section className="summary" aria-label="Statistics summary">
        <div className="summary-tile">
          <span className="summary-label">Plays</span>
          <strong>{formatCount(stats.summary.total_plays)}</strong>
        </div>
        <div className="summary-tile">
          <span className="summary-label">Listening time</span>
          <strong>{formatListeningTime(stats.summary.total_ms_played)}</strong>
        </div>
        <div className="summary-tile">
          <span className="summary-label">Distinct tracks</span>
          <strong>{formatCount(stats.summary.distinct_tracks)}</strong>
        </div>
      </section>

      <section className="toolbar" aria-label="Track controls">
        <div className="toggle-group" role="tablist" aria-label="Track ranking metric">
          <button
            type="button"
            className={metric === "plays" ? "active" : ""}
            aria-pressed={metric === "plays"}
            onClick={() => setMetric("plays")}
          >
            Plays
          </button>
          <button
            type="button"
            className={metric === "listening_time" ? "active" : ""}
            aria-pressed={metric === "listening_time"}
            onClick={() => setMetric("listening_time")}
          >
            Listening time
          </button>
        </div>

        <div className="toggle-group" role="tablist" aria-label="Theme selection">
          <button
            type="button"
            className={themeMode === "system" ? "active" : ""}
            aria-pressed={themeMode === "system"}
            onClick={() => setThemeMode("system")}
          >
            System
          </button>
          <button
            type="button"
            className={themeMode === "light" ? "active" : ""}
            aria-pressed={themeMode === "light"}
            onClick={() => setThemeMode("light")}
          >
            Light
          </button>
          <button
            type="button"
            className={themeMode === "dark" ? "active" : ""}
            aria-pressed={themeMode === "dark"}
            onClick={() => setThemeMode("dark")}
          >
            Dark
          </button>
        </div>
      </section>

      <label className="search-box">
        <span>Search tracks</span>
        <input
          type="search"
          placeholder="Search by track or artist"
          value={searchQuery}
          onChange={(event) => setSearchQuery(event.target.value)}
        />
      </label>

      <section className="podium" aria-label="Top three tracks">
        {podiumTracks.map((track, index) => (
          <article key={`${track.globalRank}-${track.track}`} className={`podium-card podium-${index + 1}`}>
            <span className="podium-rank">#{track.globalRank}</span>
            <strong>{track.track}</strong>
            <span>{track.artist}</span>
            <span>{metric === "plays" ? `${formatCount(track.plays)} plays` : formatListeningTime(track.ms_played)}</span>
          </article>
        ))}
      </section>

      <h2>{metric === "plays" ? "Top tracks" : "Longest listened"}</h2>
      <TrackList tracks={filteredTracks} />

      {stats.most_skipped && stats.most_skipped.length > 0 && (
        <section className="most-skipped" aria-label="Most skipped tracks">
          <h2>Most skipped</h2>
          <ol>
            {stats.most_skipped.slice(0, 20).map((track) => (
              <li key={`${track.track}-${track.artist}`}>
                <span className="most-skipped-rank">#{track.rank}</span>
                <span className="most-skipped-track">{track.track}</span>
                <span className="most-skipped-artist">{track.artist}</span>
                <span className="most-skipped-count">{formatCount(track.skips)} skips</span>
              </li>
            ))}
          </ol>
        </section>
      )}
    </>
  );
}
