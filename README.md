<img src="https://storage.googleapis.com/lanyard/static/lanyardtemplogo.png" alt="Lanyard Logo" width="300"/>

# 🏷️ Expose your Discord presence and activities to a RESTful API and WebSocket

Lanyard is a service that makes it super easy to export your live Discord presence to an API endpoint (`lanyard.prp.bio/v1/users/:your_id`) and to a WebSocket for you to use wherever you want.

This is a Python/Flask rewrite of the original Elixir version with full feature parity:
- REST API for presence data (W.I.P)
- Real-time WebSocket gateway (W.I.P)
- Key-Value store for custom data (W.I.P)
- Discord bot commands (W.I.P)
- Prometheus metrics (W.I.P)

## Quick Start

### Prerequisites
- Python 3.8+
- Redis server
- Discord bot token (create one at https://discord.com/developers/applications)

### Installation

```bash
git clone https://github.com/lecanact/lanyard-flask.git
cd lanyard-flask
pip install -r requirements.txt
```

### Environment Setup

Create a `.env` file:

```env
BOT_TOKEN=your_discord_bot_token_here
USER_TOKEN=your_discord_user_token_here
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
HTTP_PORT=4001
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
BOT_IDEMPOTENCY_ENV_KEY=your_bot_idempotency_env_key_here
```

### Running Locally

```bash
python run.py
```

The API will be available at `http://localhost:4001`

## Docker Setup

### Build the image
```bash
docker build -t lanyard-flask:latest .
```

### Run with Docker Compose

```bash
docker-compose up
```

This starts both the Redis instance and Lanyard API server.

## API Documentation

### Get User Presence
`GET https://lanyard.prp.bio/v1/users/:user_id`

Example response:
```json
{
  "success": true,
  "data": {
    "discord_user": {
      "username": "YourUsername",
      "id": "123456789",
      "avatar": "avatar_hash",
      "discriminator": "0001"
    },
    "discord_status": "online",
    "active_on_discord_web": true,
    "active_on_discord_desktop": false,
    "active_on_discord_mobile": false,
    "listening_to_spotify": true,
    "spotify": {
      "track_id": "3kdlVcMVsSkbsUy8eQcBjI",
      "song": "Let Go",
      "artist": "Ark Patrol",
      "album": "Let Go",
      "album_art_url": "https://i.scdn.co/image/...",
      "timestamps": {
        "start": 1615529820677,
        "end": 1615530068733
      }
    },
    "activities": [],
    "kv": {
      "location": "Los Angeles, CA"
    }
  }
}
```

### Get Current User Presence
`GET https://lanyard.prp.bio/v1/users/@me`

Requires `Authorization` header with API key.

### Set KV Pair
`PUT https://lanyard.prp.bio/v1/users/:user_id/kv/:key`

Body: raw string value

### Set Multiple KV Pairs
`PATCH https://lanyard.prp.bio/v1/users/:user_id/kv`

Body: JSON object with key-value pairs

### Delete KV Pair
`DELETE https://lanyard.prp.bio/v1/users/:user_id/kv/:key`

## KV Store

The KV store allows storing custom key-value data linked to your Discord account.

### Limits
- Keys: alphanumeric only, max 255 characters
- Values: max 30,000 characters
- Max pairs per user: 512

### Getting an API Key

DM the Spook bot with `.apikey` to receive your API key.

### Discord Bot Commands
- `.apikey` - Get/generate API key (DM only)
- `.set <key> <value>` - Set a KV pair
- `.get <key>` - Get a KV value
- `.del <key>` - Delete a KV pair

## WebSocket

Connect to `wss://lanyard.prp.bio/socket` for real-time presence updates.

### Opcodes

| Opcode | Name       | Description |
|--------|-----------|-------------|
| 0      | Event     | Receive events (INIT_STATE, PRESENCE_UPDATE) |
| 1      | Hello     | Server sends heartbeat interval |
| 2      | Initialize | Client sends to subscribe to users |
| 3      | Heartbeat | Client sends periodically to maintain connection |

### Initialize (Opcode 2)

Subscribe to specific users:
```json
{
  "op": 2,
  "d": {
    "subscribe_to_ids": ["123456789", "987654321"]
  }
}
```

Or subscribe to all monitored users:
```json
{
  "op": 2,
  "d": {
    "subscribe_to_all": true
  }
}
```

### Events

**INIT_STATE** - Initial state of subscribed users
```json
{
  "op": 0,
  "seq": 1,
  "t": "INIT_STATE",
  "d": {
    "123456789": { /* presence data */ }
  }
}
```

**PRESENCE_UPDATE** - User presence changed
```json
{
  "op": 0,
  "seq": 2,
  "t": "PRESENCE_UPDATE",
  "d": { /* presence data with user_id */ }
}
```

## Metrics

Prometheus metrics are available at `GET /metrics`

## Project Structure

```
lanyard-flask/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── bot.py
│   ├── utils.py
│   └── api/
│       ├── __init__.py
│       ├── v1/
│       │   └── __init__.py
│       ├── metrics.py
│
├── services/
│   ├── redis_client.py
│   ├── presence.py
│   ├── kv_store.py
│   ├── metrics.py
│   └── socketio_handler.py
├── run.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Configuration

Environment variables:
- `BOT_TOKEN` - Discord bot token (required)
- `USER_TOKEN` - Discord user token (required)
- `PYTHONDONTWRITEBYTECODE` - Stops writing bytes (default: 1)
- `PYTHONUNBUFFERED` - Remove buffering (default: 1)
- `REDIS_HOST` - Redis server host (default: localhost)
- `REDIS_PORT` - Redis server port (default: 6379)
- `REDIS_DB` - Redis database number (default: 0)
- `REDIS_PASSWORD` - Redis password (optional)
- `HTTP_PORT` - HTTP server port (default: 4001)
- `FLASK_ENV` - Environment (development/production, default: development)
- `BOT_IDEMPOTENCY_ENV_KEY` - Idempotency check (optional)

## Features

✅ REST API for Discord presence (W.I.P)
✅ Real-time WebSocket gateway (W.I.P)
✅ Key-value store with custom data (W.I.P)
✅ Discord bot commands (W.I.P)
✅ Prometheus metrics (W.I.P)
✅ Multi-instance sync via Redis pub/sub (W.I.P)
✅ Full API key authentication (W.I.P)

## Credits

Credits to @Phineas for creating the original Lanyard.
