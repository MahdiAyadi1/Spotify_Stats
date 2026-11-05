import { useEffect, useState } from "react";
import { formatCount, formatListeningTime } from "../format";
import type { RankedTrack } from "../lib/trackView";

const PAGE_SIZE = 100;

export function TrackList({ tracks }: { tracks: RankedTrack[] }) {
  const [shownCount, setShownCount] = useState(PAGE_SIZE);

  useEffect(() => {
    setShownCount(PAGE_SIZE);
  }, [tracks]);

  const visibleTracks = tracks.slice(0, shownCount);

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
      {shownCount < tracks.length && (
        <button type="button" onClick={() => setShownCount((count) => count + PAGE_SIZE)}>
          Show {PAGE_SIZE} more
        </button>
      )}
    </>
  );
}
