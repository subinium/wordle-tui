# TUI Wordle

Beautiful terminal-based Wordle game with shared leaderboard, streaks, and GitHub login.

```
╦ ╦╔═╗╦═╗╔╦╗╦  ╔═╗
║║║║ ║╠╦╝ ║║║  ║╣
╚╩╝╚═╝╩╚══╩╝╩═╝╚═╝
```

## Features

- Daily Wordle with 365 unique words per year
- GitHub OAuth login
- Shared leaderboard
- Personal statistics & streaks
- GitHub-style contribution graph
- Beautiful TUI with Wordle colors
- Keyboard with letter state indicators
- Works offline too!

## Installation

### pip (Recommended)

```bash
pip install tui-wordle
```

### curl

```bash
curl -fsSL https://raw.githubusercontent.com/subinium/tui-wordle/main/install.sh | bash
```

### pipx

```bash
pipx install tui-wordle
```

### npm / bun

```bash
npm install -g tui-wordle
# or
bun install -g tui-wordle
```

### From source

```bash
git clone https://github.com/subinium/tui-wordle.git
cd tui-wordle
pip install -e .
```

## Usage

```bash
# Play the game
wordle

# Or use the full name
tui-wordle
```

## Controls

| Key | Action |
|-----|--------|
| A-Z | Type letter |
| Enter | Submit guess |
| Backspace | Delete letter |
| ESC | Quit game |
| F1 | View statistics |
| F2 | View leaderboard |
| ← → | Navigate tabs (in result screen) |

## Configuration

Set the API server URL:

```bash
export WORDLE_API_URL="https://your-server.com"
```

## Self-Hosting

Want to run your own server?

### 1. Set up Neon PostgreSQL

1. Create account at [neon.tech](https://neon.tech)
2. Create a new project
3. Copy the connection string

### 2. Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/xxx)

Or manually:

1. Fork this repository
2. Connect to Railway
3. Add environment variables:

```
DATABASE_URL=postgresql+asyncpg://...
SECRET_KEY=your-secret-key
GITHUB_CLIENT_ID=your-github-oauth-app-client-id
```

### 3. GitHub OAuth Setup

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Create new OAuth App
3. Set "Device Flow" enabled
4. Copy Client ID to `GITHUB_CLIENT_ID`

## Development

```bash
# Clone
git clone https://github.com/subinium/tui-wordle.git
cd tui-wordle

# Create venv
python -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev,server]"

# Run locally
python -m client.app

# Run server
python -m server.main
```

## License

MIT License - see [LICENSE](LICENSE)

## Credits

- Built with [Textual](https://textual.textualize.io/)
- Inspired by [Wordle](https://www.nytimes.com/games/wordle/)
