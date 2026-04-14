# HubSpot API to Markdown

A Python CLI tool that scrapes the official HubSpot Developer documentation and saves it as clean, well-formatted Markdown files — perfect for offline reference, AI/LLM context, or building custom documentation workflows.

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

## Why?

- **Offline access** — Read HubSpot API docs without an internet connection
- **AI/LLM context** — Feed documentation into ChatGPT, Claude, or local LLMs for coding assistance
- **Version control** — Track documentation changes over time with git
- **Custom tooling** — Build search indexes, generate SDKs, or create training data

## Features

| Feature | Description |
|---------|-------------|
| 📋 **Interactive TUI** | Beautiful terminal menu powered by Rich and Questionary |
| �️ **CLI Mode** | Non-interactive mode with `--download`, `--update`, `--status` flags |
| 🔍 **Auto-discovery** | Finds all 2,700+ docs via HubSpot's sitemap — no manual URL lists |
| 📥 **Smart downloads** | Only fetches missing pages; skip what you already have |
| 🔄 **Update detection** | Checks `lastmod` dates to find changed documentation |
| 📁 **Logical structure** | Mirrors the docs URL hierarchy (`/api/crm/contacts` → `api/crm/contacts.md`) |
| 💻 **Code preservation** | All code blocks, syntax highlighting hints, and examples kept intact |
| ⏱️ **Rate limiting** | Polite 400ms delay between requests to avoid hammering servers |
| 🔁 **Auto-retry** | Failed requests automatically retry up to 3 times with backoff |
| 💾 **Persistent config** | Remembers your output directory between sessions |
| 🗂️ **State tracking** | Tracks downloaded pages via local JSON state file |

## Quick Start

### Prerequisites

- Python 3.10 or higher
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/Hubspot-API-to-Markdown.git
cd Hubspot-API-to-Markdown

# Install dependencies
pip install -r requirements.txt

# Run the scraper
python main.py
```

## Usage

### Interactive Mode (TUI)

Simply run without arguments for the interactive menu:

```bash
python main.py
```

```
╭──────────────────────────╮
│   HubSpot Docs Scraper   │
╰─ developers.hubspot.com ─╯

? 📁  Use saved directory? (C:\Users\You\hubspot-docs) Yes
  Using output directory: C:\Users\You\hubspot-docs

? What would you like to do?
  📥  Download missing pages
  🔄  Check for & download updates
  🎯  Download specific section
  📊  Show status
  ──────────────────
  📁  Change output directory
  🔃  Refresh sitemap cache
  🗑️   Clear saved settings
  ──────────────────
  🚪  Quit
```

### Command-Line Mode (Non-Interactive)

Perfect for automation, cron jobs, or CI/CD:

```bash
# Download all missing pages
python main.py --download

# Check for and download updates
python main.py --update

# Show current status
python main.py --status

# Specify output directory (also saves it for future runs)
python main.py --output ~/my-hubspot-docs --download

# Clear saved settings
python main.py --clear-config
```

### CLI Options

| Option | Short | Description |
|--------|-------|-------------|
| `--output DIR` | `-o` | Set output directory (saved for future runs) |
| `--download` | `-d` | Download all missing pages |
| `--update` | `-u` | Download pages with newer `lastmod` dates |
| `--status` | `-s` | Show download statistics |
| `--clear-config` | | Clear saved configuration |
| `--help` | `-h` | Show help message |

## Output Structure

```
~/hubspot-docs/
├── .hubspot_docs_state.json      # Tracks downloaded pages
├── api-reference/
│   └── latest/
│       └── crm/
│           └── objects/
│               └── contacts/
│                   ├── get-contact.md
│                   ├── create-contact.md
│                   └── ...
├── guides/
│   └── api/
│       ├── overview.md
│       └── crm/
│           └── objects/
│               └── contacts.md
└── ...
```

## Example Output

Each Markdown file includes:

```markdown
# Retrieve a contact - HubSpot docs

> **Source:** [https://developers.hubspot.com/docs/api-reference/...](...)
> **Scraped:** 2026-04-14 07:19 UTC

---

## Authorization

Authorization: `string` (header, required)
The access token received from the authorization server...

## Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| objectId | string | ✓ | The contact ID |

## Response

\`\`\`json
{
  "id": "123",
  "properties": { ... }
}
\`\`\`
```

## Configuration

### Persistent Settings

Your settings are saved to `~/.hubspot-docs-scraper.json`:

```json
{
  "output_dir": "C:\\Users\\You\\hubspot-docs",
  "last_used": "2026-04-14T08:30:00+00:00"
}
```

To reset: `python main.py --clear-config`

### Tuning Parameters

Edit constants at the top of `main.py`:

```python
REQUEST_DELAY = 0.4   # Seconds between requests (be polite)
REQUEST_TIMEOUT = 20  # Request timeout in seconds
MAX_RETRIES = 3       # Retry attempts for failed requests
```

## Requirements

- `requests` — HTTP client
- `beautifulsoup4` + `lxml` — HTML parsing
- `html2text` — HTML to Markdown conversion
- `rich` — Beautiful terminal output
- `questionary` — Interactive prompts

## Troubleshooting

**"No pages found in sitemap"**
- Check your internet connection
- Try "Refresh sitemap cache" from the menu
- HubSpot may have changed their sitemap URL

**Pages downloading but content is empty**
- Some pages may require JavaScript; this tool handles server-rendered content only
- Open an issue with the specific URL

**Rate limited / 429 errors**
- Increase `REQUEST_DELAY` in `main.py`
- The scraper has automatic retry with exponential backoff

**"No saved output directory" in CLI mode**
- Run interactively once first, or use `--output` flag

## Contributing

Contributions welcome! Please open an issue first to discuss what you'd like to change.

## License

[MIT](LICENSE) — Use freely, attribution appreciated.

## Disclaimer

This tool is for personal/educational use. Respect HubSpot's Terms of Service and robots.txt. The downloaded content remains © HubSpot, Inc.