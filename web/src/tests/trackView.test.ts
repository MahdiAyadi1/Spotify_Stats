import { describe, expect, it } from "vitest";
import type { TopTrack } from "../api";
import { filterTracks, sortTracks } from "../lib/trackView";

const trackFixtures: TopTrack[] = [
  { rank: 1, track: "Alpha", artist: "Artist A", plays: 5, ms_played: 120_000, skips: 0, skip_rate: 0, first_played: "2024-01-01" },
  { rank: 2, track: "Bravo", artist: "Artist B", plays: 10, ms_played: 100_000, skips: 0, skip_rate: 0, first_played: "2024-01-02" },
  { rank: 3, track: "Charlie", artist: "Artist A", plays: 10, ms_played: 150_000, skips: 0, skip_rate: 0, first_played: "2024-01-03" },
  { rank: 4, track: "Delta", artist: "Artist C", plays: 2, ms_played: 220_000, skips: 0, skip_rate: 0, first_played: "2024-01-04" },
];

describe("sortTracks", () => {
  it("sorts by plays first, then listening time, then name", () => {
    expect(sortTracks(trackFixtures, "plays").map((track) => track.track)).toEqual([
      "Charlie",
      "Bravo",
      "Alpha",
      "Delta",
    ]);
  });

  it("sorts by listening time first, then plays, then name", () => {
    expect(sortTracks(trackFixtures, "listening_time").map((track) => track.track)).toEqual([
      "Delta",
      "Charlie",
      "Alpha",
      "Bravo",
    ]);
  });
});

describe("filterTracks", () => {
  it("filters by track or artist and keeps the global rank from the full list", () => {
    const tracks = sortTracks(trackFixtures, "plays");

    expect(filterTracks(tracks, "artist a").map((track) => ({ track: track.track, globalRank: track.globalRank }))).toEqual([
      { track: "Charlie", globalRank: 1 },
      { track: "Alpha", globalRank: 3 },
    ]);

    expect(filterTracks(tracks, "br").map((track) => track.globalRank)).toEqual([2]);
  });
});
