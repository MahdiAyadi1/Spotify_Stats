export function formatCount(count: number): string {
  return count.toLocaleString("en-US");
}

/** Listening time as "1,234 h 05 min", or "45 min" under an hour. Seconds are dropped. */
export function formatListeningTime(msPlayed: number): string {
  const totalMinutes = Math.floor(msPlayed / 60_000);
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  if (hours === 0) {
    return `${minutes} min`;
  }
  return `${formatCount(hours)} h ${String(minutes).padStart(2, "0")} min`;
}
