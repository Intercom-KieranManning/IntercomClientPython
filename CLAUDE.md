# Intercom ClientPython

Python device client that streams video from a camera to a remote receiver (browser viewer) using WebRTC, authenticated via OAuth 2.0 Device Authorization Grant.

## Tech Stack

- **Python 3.14+** with **uv** package manager
- **aiortc** — WebRTC peer connection and media streaming
- **OpenCV (cv2)** — Camera capture
- **websockets** — WebSocket signaling client
- **boto3** — AWS SDK (indirectly via backend)
- **requests** — HTTP API calls for OAuth flow

## Project Structure

```
ClientPython/
├── main.py                      # PiClient entry point
├── intercomclient/
│   ├── config.py                # Config dataclass (env vars)
│   ├── device_authorization.py  # OAuth device flow functions
│   ├── token_store.py           # Token persistence (JSON file, 0600 perms)
│   └── camera_video_stream_track.py  # WebRTC video track (OpenCV capture)
├── pyproject.toml               # uv dependencies
└── Dockerfile.dev               # Dev image (bookworm-slim + OpenCV deps)
```

## Architecture

### Authentication (`intercomclient/device_authorization.py` + `intercomclient/token_store.py`)
- **OAuth 2.0 Device Code Grant** (`urn:ietf:params:oauth:grant-type:device_code`)
- `initiate_device_authorization()` — POSTs to `/oauth/device-authorization/` with device type/OS
- `poll_for_token()` — Polls `/oauth/token/` with device code until approved (timeout configurable via `MAX_POLLING_TIME_MINS`, default 5 min)
- `refresh_tokens()` — Refreshes access token using stored refresh token
- `TokenStore` — Stores access/refresh tokens + device_code to JSON file (permissions `0600`) at `~/.config/intercomclient/tokens.json`

### WebRTC Signaling (`main.py` — `PiClient`)
- Connects to WebSocket signaling server at `{WEBSOCKET_API_BASE_URL}/ws/live_stream/{device_code}/`
- Authenticates with Bearer token in `Authorization` header
- **Signaling loop** handles:
  - `offer` (from viewer) — Sets remote SDP, creates `CameraVideoStreamTrack`, generates SDP answer, sends it back
  - `answer` (unused — device is answerer only)
  - `candidate` — Receives ICE candidates from remote peer; `sdpMid`/`sdpMLineIndex` are top-level fields in the message
  - `status` — `peer_connected`/`peer_disconnected` events
  - `icecandidate` events (local) — Sends locally-generated ICE candidates back through signaling server
- Connection lifecycle: shutdown on `failed`/`closed`, retry on errors with 5s backoff

### Video Capture (`intercomclient/camera_video_stream_track.py`)
- `CameraVideoStreamTrack` extends `aiortc.VideoStreamTrack`
- Uses `cv2.VideoCapture` to capture frames from camera source (default device `0`, configurable via `VIDEO_SOURCE`)
- Converts frames to `av.VideoFrame` (BGR24 format) with proper PTS/time_base timestamps
- Retries silently on capture failure

### Configuration (`intercomclient/config.py`)
- All configurable via environment variables:
  - `HTTP_API_BASE_URL` — Backend API URL (default: `http://backend:8000`)
  - `WEBSOCKET_API_BASE_URL` — WebSocket URL (default: `ws://backend:8000`)
  - `VIDEO_SOURCE` — Camera device index (default: `0`)
  - `TOKEN_FILE_PATH` — Token file path (default: `~/.config/intercomclient/tokens.json`)
  - `OAUTH_CLIENT_ID` / `OAUTH_CLIENT_SECRET` — Fallback if `~/.config/intercom-api/oauth.json` not found
  - `MAX_POLLING_TIME_MINS` — Device auth polling timeout (default: `5`)
- Defaults: 320×240 resolution, 5 fps

### Entry Point (`main.py` → `main()`)
- Creates `PiClient`, registers SIGINT/SIGTERM handlers
- Runs client in a loop: ensure valid tokens → connect signaling → stream

## Docker Dev Setup

```bash
# Start (from repo root)
docker compose up -d clientpython

# View logs
docker compose logs -f clientpython

# Rebuild after code changes
docker compose up -d --build clientpython
```

### Device Access
The container mounts `/dev/video0` from the host for camera access:
```yaml
devices:
  - /dev/video0:/dev/video0
```

### Service Dependency
`clientpython` depends on `utility` (healthy) — ensures device registration and token writing complete before the client starts.

### Shared Volumes
- `device_oauth_config` — OAuth credentials from `utility` (`~/.config/intercom-api/oauth.json`)
- `client_tokens` — Token file shared with `utility` (`~/.config/intercomclient/tokens.json`)

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `HTTP_API_BASE_URL` | `http://backend:8000` | Backend API base URL |
| `WEBSOCKET_API_BASE_URL` | `ws://backend:8000` | WebSocket base URL |
| `VIDEO_SOURCE` | `0` | Camera device index |
| `TOKEN_FILE_PATH` | `~/.config/intercomclient/tokens.json` | Token storage path |
| `OAUTH_CLIENT_ID` | from `oauth.json` | OAuth client ID |
| `OAUTH_CLIENT_SECRET` | from `oauth.json` | OAuth client secret |
| `MAX_POLLING_TIME_MINS` | `5` | Device auth polling timeout |

## `.envrc`

**Never modify `.envrc`.** It contains local-only developer environment config and must always reflect the developer's own setup.
