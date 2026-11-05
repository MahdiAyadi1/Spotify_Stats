import type { TopTrack } from "../api";

export type TrackMetric = "plays" | "listening_time";

export interface RankedTrack extends TopTrack {
  globalRank: number;
}

export function sortTracks(tracks: TopTrack[], metric: TrackMetric): RankedTrack[] {
  const sortedTracks = [...tracks].sort((left, right) => {
    if (metric === "listening_time") {
      if (right.ms_played !== left.ms_played) {
        return right.ms_played - left.ms_played;
      }
      if (right.plays !== left.plays) {
        return right.plays - left.plays;
      }
    } else {
      if (right.plays !== left.plays) {
        return right.plays - left.plays;
      }
      if (right.ms_played !== left.ms_played) {
        return right.ms_played - left.ms_played;
      }
    }

    return left.track.localeCompare(right.track);
  });

  return sortedTracks.map((track, index) => ({
    ...track,
    globalRank: index + 1,
  }));
}

export function filterTracks(tracks: RankedTrack[], query: string): RankedTrack[] {
  const normalizedQuery = query.trim().toLowerCase();
  if (!normalizedQuery) {
    return tracks;
  }

  return tracks.filter(
    (track) =>
      track.track.toLowerCase().includes(normalizedQuery) ||
      track.artist.toLowerCase().includes(normalizedQuery),
  );
}
