// Mirrors the JSON contract of POST /api/stats described in AGENTS.md.
// Keys stay in snake_case, exactly as the API returns them.

export interface StatsOptions {
  min_play_ms: number;
  min_skips: number;
  timezone: string;
  date_from: string | null;
  date_to: string | null;
  merge_duplicates: boolean;
}

export interface ExportOverview {
  history_files: number;
  track_entries: number;
  first_entry: string | null;
  last_entry: string | null;
}

export interface StatsSummary {
  total_plays: number;
  total_ms_played: number;
  total_skips: number;
  distinct_tracks: number;
  distinct_artists: number;
}

export interface BaseRankedMetric {
  rank: number;
  plays: number;
  ms_played: number;
  skips: number;
  skip_rate: number;
  first_played: string | null;
}

export interface TopTrack extends BaseRankedMetric {
  track: string;
  artist: string;
}

export interface TopArtist extends BaseRankedMetric {
  artist: string;
}

export interface TopAlbum {
  rank: number;
  album: string;
  artist: string;
  plays: number;
  ms_played: number;
}

export interface MostSkippedTrack {
  rank: number;
  track: string;
  artist: string;
  skips: number;
  plays: number;
  skip_rate: number;
}

export interface YearlyTopTrack {
  year: number;
  track: string;
  artist: string;
  plays: number;
  ms_played: number;
}

export interface MonthlyDiscovery {
  month: string;
  new_tracks: number;
  new_artists: number;
}

export interface TimelineMonth {
  month: string;
  plays: number;
  ms_played: number;
}

export interface TimelineYear {
  year: number;
  plays: number;
  ms_played: number;
}

export interface Timeline {
  months: TimelineMonth[];
  years: TimelineYear[];
}

export interface ClockEntry {
  hour: number;
  plays: number;
  ms_played: number;
}

export interface WeekdayEntry {
  weekday: number;
  plays: number;
  ms_played: number;
}

export interface Clock {
  hours: ClockEntry[];
  weekdays: WeekdayEntry[];
}

export interface ObsessionEntry {
  rank: number;
  track: string;
  artist: string;
  period_start: string;
  plays: number;
}

export interface Obsessions {
  days: ObsessionEntry[];
  weeks: ObsessionEntry[];
}

export interface LongestSession {
  started_at: string;
  duration_ms: number;
  plays: number;
}

export interface SessionsSummary {
  count: number;
  average_ms: number;
  longest: LongestSession | null;
}

export interface HabitStat {
  reason: string;
  plays: number;
  skips: number;
}

export interface PlatformUsage {
  platform: string;
  plays: number;
  ms_played: number;
}

export interface ShuffleTotals {
  shuffled_plays: number;
  other_plays: number;
}

export interface OfflineTotals {
  offline_plays: number;
  online_plays: number;
}

export interface ListeningHabits {
  reason_start: HabitStat[];
  reason_end: HabitStat[];
  platforms: PlatformUsage[];
  shuffle: ShuffleTotals;
  offline: OfflineTotals;
}

export interface StatsResponse {
  options: StatsOptions;
  overview: ExportOverview;
  summary: StatsSummary;
  top_tracks: TopTrack[];
  top_artists: TopArtist[];
  top_albums: TopAlbum[];
  most_skipped: MostSkippedTrack[];
  yearly_top_tracks: YearlyTopTrack[];
  discovery: MonthlyDiscovery[];
  timeline: Timeline;
  clock: Clock;
  obsessions: Obsessions;
  sessions: SessionsSummary;
  habits: ListeningHabits;
}

export async function fetchStats(exportZip: File): Promise<StatsResponse> {
  const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").trim();
  const statsUrl = apiBaseUrl ? new URL("/api/stats", apiBaseUrl).toString() : "/api/stats";

  const response = await fetch(statsUrl, { method: "POST", body: exportZip });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }
  return (await response.json()) as StatsResponse;
}

/** The API answers 400 and 413 with {"error": "..."}; anything else gets a generic message. */
async function readErrorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { error?: string };
    if (body.error) {
      return body.error;
    }
  } catch {
    // The body is not JSON, for example an error page from a gateway.
  }
  return `The request failed with status ${response.status}.`;
}
