import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchStats } from "../api";

const exportZip = new File(["zip"], "export.zip");

function stubFetch(response: Response) {
  const fetchMock = vi.fn().mockResolvedValue(response);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("fetchStats", () => {
  it("posts the ZIP to /api/stats and returns the statistics", async () => {
    const stats = {
      summary: { total_plays: 1, total_ms_played: 200_000, distinct_tracks: 1 },
      top_tracks: [{ rank: 1, track: "Let Down", artist: "Radiohead", plays: 1, ms_played: 200_000 }],
    };
    const fetchMock = stubFetch(Response.json(stats));

    expect(await fetchStats(exportZip)).toEqual(stats);
    expect(fetchMock).toHaveBeenCalledWith("/api/stats", { method: "POST", body: exportZip });
  });

  it("throws the error message sent by the API", async () => {
    stubFetch(Response.json({ error: "The upload is not a ZIP file." }, { status: 400 }));

    await expect(fetchStats(exportZip)).rejects.toThrow("The upload is not a ZIP file.");
  });

  it("throws a generic message when the error body is not JSON", async () => {
    stubFetch(new Response("<html>Bad gateway</html>", { status: 502 }));

    await expect(fetchStats(exportZip)).rejects.toThrow("The request failed with status 502.");
  });
});
