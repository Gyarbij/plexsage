# PlexSage

A self-hosted web application that generates Plex music playlists using LLMs with library awareness. PlexSage uses a filter-first approach to ensure 100% of suggested tracks are playable from your library.

## Features

- **Prompt-Based Playlists**: Describe what you want ("melancholy 90s alternative for a rainy day") and get a curated playlist
- **Seed Track Discovery**: Start from a song you like and explore similar music across selectable dimensions (mood, era, instrumentation, etc.)
- **Library-First Guarantee**: Every track in generated playlists exists in your Plex library
- **Smart Filtering**: Refine by genre, decade, minimum rating, and more before generation
- **Cost Transparency**: See actual token usage and costs for each request
- **Context-Aware Limits**: Automatically adjusts track limits based on your LLM's context window
- **Multi-Provider Support**: Works with Anthropic Claude, OpenAI GPT, or Google Gemini

## Quick Start

### Prerequisites

- Docker and Docker Compose
- A Plex server with a music library
- [Plex authentication token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/)
- API key from Anthropic, OpenAI, or Google

### Setup

1. Clone the repository:
```bash
git clone https://github.com/ecwilsonaz/plexsage.git
cd plexsage
```

2. Create your environment file:
```bash
cp .env.example .env
```

3. Edit `.env` with your credentials:
```bash
PLEX_URL=http://your-plex-server:32400
PLEX_TOKEN=your-plex-token

# Choose ONE provider:
ANTHROPIC_API_KEY=sk-ant-your-key-here
# OPENAI_API_KEY=sk-your-key-here
# GEMINI_API_KEY=your-gemini-key-here
```

4. Start the application:
```bash
docker-compose up -d
```

5. Open http://localhost:8765

## LLM Providers

PlexSage auto-detects your provider based on which API key is set. You can also explicitly set `LLM_PROVIDER` in your `.env`.

| Provider | Models | Max Tracks | Cost | Notes |
|----------|--------|------------|------|-------|
| **Gemini** | gemini-2.5-flash | ~18,000 | Lowest | Great for large libraries |
| **Anthropic** | claude-sonnet-4-5, claude-haiku-4-5 | ~3,500 | Medium | Nuanced recommendations |
| **OpenAI** | gpt-4.1, gpt-4.1-mini | ~2,300 | Medium | Solid all-around choice |

### Two-Model Strategy

PlexSage uses two models by default:
- **Analysis model** (smarter): Understands your prompt, suggests filters, analyzes seed tracks
- **Generation model** (cheaper): Selects tracks from the filtered list

This balances quality and cost. Set `smart_generation: true` in config to use the analysis model for everything (higher quality, ~3-5x cost).

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `PLEX_URL` | Your Plex server URL |
| `PLEX_TOKEN` | Plex authentication token |
| `PLEX_MUSIC_LIBRARY` | Music library name (default: "Music") |
| `LLM_PROVIDER` | anthropic, openai, or gemini (auto-detected if not set) |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `GEMINI_API_KEY` | Google Gemini API key |

### Optional: config.yaml

For additional customization, create a `config.yaml`:

```yaml
plex:
  music_library: "Music"

llm:
  provider: "gemini"
  model_analysis: "gemini-2.5-flash"
  model_generation: "gemini-2.5-flash"
  smart_generation: false

defaults:
  track_count: 25
```

## How It Works

PlexSage uses a **filter-first architecture** to handle large libraries:

1. **Analyze**: LLM interprets your prompt and suggests genre/decade filters
2. **Filter**: Library is narrowed to matching tracks (e.g., "90s Alternative" → 2,000 tracks)
3. **Sample**: If still too large, randomly samples tracks to fit context limits
4. **Generate**: Filtered track list sent to LLM for curation
5. **Match**: LLM selections are fuzzy-matched back to your library
6. **Save**: Playlist is created in Plex

This ensures every track exists in your library while keeping costs manageable for 50,000+ track libraries.

## Development

### Local Setup

```bash
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

# Set environment variables (or use .env file)
export PLEX_URL=http://your-plex-server:32400
export PLEX_TOKEN=your-plex-token
export GEMINI_API_KEY=your-key

uvicorn backend.main:app --reload --port 8765
```

### Running Tests

```bash
pytest tests/ -v
```

## API

Interactive API documentation available at `/docs` when running.

Key endpoints:
- `GET /api/health` - Health check
- `GET /api/config` - Current configuration
- `GET /api/library/stats` - Library statistics
- `POST /api/analyze/prompt` - Analyze natural language prompt
- `POST /api/generate` - Generate playlist
- `POST /api/playlist` - Save playlist to Plex

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, python-plexapi, rapidfuzz
- **Frontend**: Vanilla HTML/CSS/JS (no build step)
- **LLM SDKs**: anthropic, openai, google-generativeai
- **Deployment**: Docker

## License

MIT
