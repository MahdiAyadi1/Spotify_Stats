import { useEffect, useState } from "react";
import { formatCount, formatListeningTime } from "../format";
import type { RankedTrack } from "../lib/trackView";

const PAGE_SIZE = 50;

export function TrackList({ tracks }: { tracks: RankedTrack[] }) {
  const [pageIndex, setPageIndex] = useState(0);

  useEffect(() => {
    setPageIndex(0);
  }, [tracks]);

  const pageCount = Math.max(1, Math.ceil(tracks.length / PAGE_SIZE));
  const startIndex = pageIndex * PAGE_SIZE;
  const visibleTracks = tracks.slice(startIndex, startIndex + PAGE_SIZE);

  return (
    <>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Track</th>
            <th>Artist</th>
            <th className="number">Plays</th>
            <th className="number">Time</th>
          </tr>
        </thead>
        <tbody>
          {visibleTracks.map((track) => (
            <tr key={`${track.globalRank}-${track.track}`}>
              <td>{track.globalRank}</td>
              <td>{track.track}</td>
              <td>{track.artist}</td>
              <td className="number">{formatCount(track.plays)}</td>
              <td className="number">{formatListeningTime(track.ms_played)}</td>
            </tr>
          ))}
        </tbody>
      </table>
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
