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
type PageKey =
  | "overview"
  | "tracks"
  | "artists"
  | "albums"
  | "skipped"
  | "yearly"
  | "discovery"
  | "sessions"
  | "habits";

const NAV_ITEMS: Array<{ key: PageKey; label: string }> = [
  { key: "overview", label: "Overview" },
  { key: "tracks", label: "Top tracks" },
  { key: "artists", label: "Top artists" },
  { key: "albums", label: "Top albums" },
  { key: "skipped", label: "Most skipped" },
  { key: "yearly", label: "Yearly tracks" },
  { key: "discovery", label: "Discovery" },
  { key: "sessions", label: "Sessions" },
  { key: "habits", label: "Habits" },
];

const PAGE_SIZE = 50;

function PaginatedList<T>({ items, renderItem }: { items: T[]; renderItem: (item: T, index: number) => React.ReactNode }) {
  const [pageIndex, setPageIndex] = useState(0);

  useEffect(() => {
    setPageIndex(0);
  }, [items]);

  const pageCount = Math.max(1, Math.ceil(items.length / PAGE_SIZE));
  const startIndex = pageIndex * PAGE_SIZE;
  const visibleItems = items.slice(startIndex, startIndex + PAGE_SIZE);

  return (
    <>
      {visibleItems.map(renderItem)}
      <div className="pager">
        <button type="button" disabled={pageIndex === 0} onClick={() => setPageIndex((page) => page - 1)}>
          Previous
        </button>
        <span>
          Page {pageIndex + 1} of {pageCount}
        </span>
        <button type="button" disabled={pageIndex >= pageCount - 1} onClick={() => setPageIndex((page) => page + 1)}>
          Next
        </button>
      </div>
    </>
  );
}

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
  const [selectedPage, setSelectedPage] = useState<PageKey>("overview");
  const [metric, setMetric] = useState<TrackMetric>("plays");
  const [searchQuery, setSearchQuery] = useState("");
  const [themeMode, setThemeMode] = useState<ThemeMode>("system");
  const [yearlyPage, setYearlyPage] = useState(0);
  const [discoveryPage, setDiscoveryPage] = useState(0);

  useEffect(() => {
    const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const resolvedTheme = themeMode === "system" ? (systemPrefersDark ? "dark" : "light") : themeMode;
    document.documentElement.dataset.theme = resolvedTheme;
    document.documentElement.style.colorScheme = resolvedTheme;
  }, [themeMode]);

  useEffect(() => {
    setYearlyPage(0);
    setDiscoveryPage(0);
  }, [stats]);

  const rankedTracks = useMemo(() => sortTracks(stats.top_tracks, metric), [stats.top_tracks, metric]);
  const podiumTracks = useMemo(() => rankedTracks.slice(0, 3), [rankedTracks]);
  const filteredTracks = useMemo(() => filterTracks(rankedTracks, searchQuery), [rankedTracks, searchQuery]);

  const summaryTiles = [
    { label: "Plays", value: formatCount(stats.summary.total_plays) },
    { label: "Listening time", value: formatListeningTime(stats.summary.total_ms_played) },
    { label: "Skips", value: formatCount(stats.summary.total_skips) },
    { label: "Distinct tracks", value: formatCount(stats.summary.distinct_tracks) },
    { label: "Distinct artists", value: formatCount(stats.summary.distinct_artists) },
  ];

  const renderPage = () => {
    if (selectedPage === "overview") {
      return (
        <>
          <section className="summary" aria-label="Statistics summary">
            {summaryTiles.map((tile) => (
              <div key={tile.label} className="summary-tile">
                <span className="summary-label">{tile.label}</span>
                <strong>{tile.value}</strong>
              </div>
            ))}
          </section>

          {rankedTracks.length > 0 && (
            <section className="podium" aria-label="Top three tracks">
              {podiumTracks.map((track, index) => (
                <article key={`${track.globalRank}-${track.track}`} className={`podium-card podium-${index + 1}`}>
                  <span className="podium-rank">#{track.globalRank}</span>
                  <strong>{track.track}</strong>
                  <span>{track.artist}</span>
                  <span>
                    {metric === "plays" ? `${formatCount(track.plays)} plays` : formatListeningTime(track.ms_played)}
                  </span>
                </article>
              ))}
            </section>
          )}

          <div className="panel-stack">
            {stats.top_artists.length > 0 && (
              <section className="panel" aria-label="Top artists">
                <h2>Top artists</h2>
                <ol className="ranked-list">
                  <PaginatedList
                    items={stats.top_artists}
                    renderItem={(artist) => (
                      <li key={`${artist.rank}-${artist.artist}`}>
                        <span className="rank">#{artist.rank}</span>
                        <span className="name">{artist.artist}</span>
                        <span>{formatCount(artist.plays)} plays</span>
                        <span className="muted">{formatListeningTime(artist.ms_played)}</span>
                      </li>
                    )}
                  />
                </ol>
              </section>
            )}

            {stats.top_albums.length > 0 && (
              <section className="panel" aria-label="Top albums">
                <h2>Top albums</h2>
                <ol className="ranked-list">
                  <PaginatedList
                    items={stats.top_albums}
                    renderItem={(album) => (
                      <li key={`${album.rank}-${album.album}-${album.artist}`}>
                        <span className="rank">#{album.rank}</span>
                        <span className="name">{album.album}</span>
                        <span>{formatCount(album.plays)} plays</span>
                        <span className="muted">{album.artist}</span>
                      </li>
                    )}
                  />
                </ol>
              </section>
            )}
          </div>
        </>
      );
    }

    if (selectedPage === "tracks") {
      return (
        <>
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

          {rankedTracks.length > 0 && (
            <>
              <section className="podium" aria-label="Top three tracks">
                {podiumTracks.map((track, index) => (
                  <article key={`${track.globalRank}-${track.track}`} className={`podium-card podium-${index + 1}`}>
                    <span className="podium-rank">#{track.globalRank}</span>
                    <strong>{track.track}</strong>
                    <span>{track.artist}</span>
                    <span>
                      {metric === "plays" ? `${formatCount(track.plays)} plays` : formatListeningTime(track.ms_played)}
                    </span>
                  </article>
                ))}
              </section>

              <h2>{metric === "plays" ? "Top tracks" : "Longest listened"}</h2>
              <TrackList tracks={filteredTracks} />
            </>
          )}
        </>
      );
    }

    if (selectedPage === "artists") {
      return (
        <section className="panel" aria-label="Top artists">
          <h2>Top artists</h2>
          <ol className="ranked-list">
            <PaginatedList
              items={stats.top_artists}
              renderItem={(artist) => (
                <li key={`${artist.rank}-${artist.artist}`}>
                  <span className="rank">#{artist.rank}</span>
                  <span className="name">{artist.artist}</span>
                  <span>{formatCount(artist.plays)} plays</span>
                  <span className="muted">{formatListeningTime(artist.ms_played)}</span>
                </li>
              )}
            />
          </ol>
        </section>
      );
    }

    if (selectedPage === "albums") {
      return (
        <section className="panel" aria-label="Top albums">
          <h2>Top albums</h2>
          <ol className="ranked-list">
            <PaginatedList
              items={stats.top_albums}
              renderItem={(album) => (
                <li key={`${album.rank}-${album.album}-${album.artist}`}>
                  <span className="rank">#{album.rank}</span>
                  <span className="name">{album.album}</span>
                  <span>{formatCount(album.plays)} plays</span>
                  <span className="muted">{album.artist}</span>
                </li>
              )}
            />
          </ol>
        </section>
      );
    }

    if (selectedPage === "skipped") {
      return (
        <section className="most-skipped" aria-label="Most skipped tracks">
          <h2>Most skipped</h2>
          <ol>
            <PaginatedList
              items={stats.most_skipped}
              renderItem={(track) => (
                <li key={`${track.track}-${track.artist}`}>
                  <span className="most-skipped-rank">#{track.rank}</span>
                  <span className="most-skipped-track">{track.track}</span>
                  <span className="most-skipped-artist">{track.artist}</span>
                  <span className="most-skipped-count">{formatCount(track.skips)} skips</span>
                </li>
              )}
            />
          </ol>
        </section>
      );
    }

    if (selectedPage === "yearly") {
      const yearlyPageCount = Math.max(1, Math.ceil(stats.yearly_top_tracks.length / PAGE_SIZE));
      const visibleYearlyTracks = stats.yearly_top_tracks.slice(yearlyPage * PAGE_SIZE, (yearlyPage + 1) * PAGE_SIZE);

      return (
        <section className="panel" aria-label="Yearly top tracks">
          <h2>Yearly top tracks</h2>
          <table className="mini-table">
            <thead>
              <tr>
                <th>Year</th>
                <th>Track</th>
                <th>Plays</th>
              </tr>
            </thead>
            <tbody>
              {visibleYearlyTracks.map((entry) => (
                <tr key={`${entry.year}-${entry.track}`}>
                  <td>{entry.year}</td>
                  <td>{entry.track}</td>
                  <td className="number">{formatCount(entry.plays)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="pager">
            <button type="button" disabled={yearlyPage === 0} onClick={() => setYearlyPage((page) => page - 1)}>
              Previous
            </button>
            <span>
              Page {yearlyPage + 1} of {yearlyPageCount}
            </span>
            <button type="button" disabled={yearlyPage >= yearlyPageCount - 1} onClick={() => setYearlyPage((page) => page + 1)}>
              Next
            </button>
          </div>
        </section>
      );
    }

    if (selectedPage === "discovery") {
      const discoveryPageCount = Math.max(1, Math.ceil(stats.discovery.length / PAGE_SIZE));
      const visibleDiscovery = stats.discovery.slice(discoveryPage * PAGE_SIZE, (discoveryPage + 1) * PAGE_SIZE);

      return (
        <section className="panel" aria-label="Month-by-month discovery">
          <h2>Discovery</h2>
          <table className="mini-table">
            <thead>
              <tr>
                <th>Month</th>
                <th>New tracks</th>
                <th>New artists</th>
              </tr>
            </thead>
            <tbody>
              {visibleDiscovery.map((entry) => (
                <tr key={entry.month}>
                  <td>{entry.month}</td>
                  <td className="number">{formatCount(entry.new_tracks)}</td>
                  <td className="number">{formatCount(entry.new_artists)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="pager">
            <button type="button" disabled={discoveryPage === 0} onClick={() => setDiscoveryPage((page) => page - 1)}>
              Previous
            </button>
            <span>
              Page {discoveryPage + 1} of {discoveryPageCount}
            </span>
            <button type="button" disabled={discoveryPage >= discoveryPageCount - 1} onClick={() => setDiscoveryPage((page) => page + 1)}>
              Next
            </button>
          </div>
        </section>
      );
    }

    if (selectedPage === "sessions") {
      return (
        <section className="panel" aria-label="Listening sessions">
          <h2>Listening sessions</h2>
          <p className="summary-line">
            {formatCount(stats.sessions.count)} sessions · average {formatListeningTime(stats.sessions.average_ms)}
          </p>
          {stats.sessions.longest && (
            <p className="summary-line">
              Longest: {stats.sessions.longest.plays} plays · {formatListeningTime(stats.sessions.longest.duration_ms)}
            </p>
          )}
        </section>
      );
    }

    return (
      <section className="panel" aria-label="Listening habits">
        <h2>Listening habits</h2>
        <div className="panel-stack">
          <div>
            <h3>Platforms</h3>
            <ul className="ranked-list compact-list">
              <PaginatedList
                items={stats.habits.platforms}
                renderItem={(platform) => (
                  <li key={platform.platform}>
                    <span className="name">{platform.platform}</span>
                    <span>{formatCount(platform.plays)} plays</span>
                  </li>
                )}
              />
            </ul>
          </div>
          <div>
            <h3>Reason start</h3>
            <ul className="ranked-list compact-list">
              <PaginatedList
                items={stats.habits.reason_start}
                renderItem={(reason) => (
                  <li key={reason.reason}>
                    <span className="name">{reason.reason}</span>
                    <span>{formatCount(reason.plays)} plays</span>
                  </li>
                )}
              />
            </ul>
          </div>
        </div>
      </section>
    );
  };

  return (
    <div className="dashboard">
      <aside className="sidebar" aria-label="Statistics sections">
        <nav>
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              type="button"
              className={selectedPage === item.key ? "side-link active" : "side-link"}
              onClick={() => setSelectedPage(item.key)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>

      <div className="content-panel">{renderPage()}</div>
    </div>
  );
}
