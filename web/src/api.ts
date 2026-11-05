// Mirrors the JSON contract of POST /api/stats described in AGENTS.md.
// Keys stay in snake_case, exactly as the API returns them.

export interface StatsSummary {
  total_plays: number;
  total_ms_played: number;
  distinct_tracks: number;
}

export interface TopTrack {
  rank: number;
  track: string;
  artist: string;
  plays: number;
  ms_played: number;
}

export interface MostSkippedTrack {
  rank: number;
  track: string;
  artist: string;
  skips: number;
}

export interface StatsResponse {
  summary: StatsSummary;
  top_tracks: TopTrack[];
  most_skipped?: MostSkippedTrack[];
}

export async function fetchStats(exportZip: File): Promise<StatsResponse> {
  const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
  const statsUrl = new URL("/api/stats", apiBaseUrl || window.location.origin).toString();

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
