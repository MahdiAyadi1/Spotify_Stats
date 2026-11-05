"""Rules shared across the package."""

# A play needs at least this much listening. Shorter entries are skips.
MIN_PLAY_MS = 30_000

# Matched against the file name only: the export may put the files in a folder.
# Matches Streaming_History_Audio_2022.json and, for a year split over several
# files, Streaming_History_Audio_2023_1.json, Streaming_History_Audio_2023_2.json.
# Does not match Streaming_History_Video_*.json or the PDF in the export.
HISTORY_FILE_PATTERN = "Streaming_History_Audio_*.json"

# Limits on the unzipped history files, to protect the function's memory.
# Measured on the bytes actually read, not on the sizes declared in the ZIP.
MAX_HISTORY_FILE_BYTES = 100 * 1024 * 1024
MAX_TOTAL_HISTORY_BYTES = 500 * 1024 * 1024
