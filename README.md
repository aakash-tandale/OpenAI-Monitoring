# OpenAI-Monitoring

# OpenAI-Monitoring

## Features

- Uses ETag (`If-None-Match`) and `Last-Modified` (`If-Modified-Since`) to avoid unnecessary downloads.
- Falls back to a deterministic SHA-256 hash of the JSON payload when server validators are not present.
- Prints active incidents and non-operational components to the console with timestamps.
- Adaptive polling: shortens interval when changes are observed and keeps polling conservative when stable.

## Files

- `status_watcher.py` — main watcher implementation.

## Requirements

- Python 3.8+
- aiohttp

Install dependencies:

pip install aiohttp

(You can also pin dependencies into a `requirements.txt` if you prefer.)

## Usage

Clone the repository and run the watcher:

git clone https://github.com/aakash-tandale/OpenAI-Monitoring.git
cd OpenAI-Monitoring
python status_watcher.py

The script will run until interrupted (Ctrl+C). Example output:

[2025-11-16 11:41:19] Product: API Upstream
Status: Investigating degraded performance
------------------------------------------------------------

## How it works (short)

1. On each poll, the watcher sends conditional headers:
   - If it has an ETag from the last successful response, it sends `If-None-Match`.
   - Otherwise, if it has a `Last-Modified` value, it sends `If-Modified-Since`.
2. If the server responds `304 Not Modified`, the watcher does nothing and sleeps for the configured interval.
3. If the server returns `200 OK`, the watcher:
   - Records the `ETag` and/or `Last-Modified` headers (if present).
   - Computes a SHA-256 hash of the JSON payload (sorted keys) and compares to the previous hash as a fallback change detector.
   - Prints any active incidents and any components that are not `operational`.
4. The polling interval adapts: it reduces (faster polling) when changes occur and respects a minimum value.

## Configuration

- The polling interval default is set inside `status_watcher.py` as `self.interval = 30` seconds. You can modify that value in the file if desired.
- The watcher uses the fixed status URL: `https://status.openai.com/api/v2/summary.json`. Change `STATUS_URL` in `status_watcher.py` to monitor a different status endpoint that follows a similar schema.
