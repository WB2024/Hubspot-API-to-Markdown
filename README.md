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
| 🔍 **Auto-discovery** | Finds all docs via HubSpot's sitemap — no manual URL lists |
| 📥 **Smart downloads** | Only fetches missing pages; skip what you already have |
| 🔄 **Update detection** | Checks `lastmod` dates to find changed documentation |
| 📁 **Logical structure** | Mirrors the docs URL hierarchy (`/api/crm/contacts` → `api/crm/contacts.md`) |
| 💻 **Code preservation** | All code blocks, syntax highlighting hints, and examples kept intact |
| ⏱️ **Rate limiting** | Polite 400ms delay between requests to avoid hammering servers |
| 💾 **State tracking** | Remembers what's downloaded via local JSON state file |

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

### Usage

```
┌───────────────────────────────────────┐
│     HubSpot Docs Scraper              │
│   developers.hubspot.com → Markdown   │
└───────────────────────────────────────┘

? Where should Markdown files be stored? ~/hubspot-docs

? What would you like to do?
  📥  Download missing pages
  🔄  Check for & download updates
  🎯  Download specific section
  📊  Show status
  📁  Change output directory
  ──────────────────
  🚪  Quit
```

**Menu options:**

- **Download missing pages** — Fetch all docs you don't have yet
- **Check for updates** — Compare sitemap dates, download newer versions
- **Download specific section** — Pick a section (e.g., `api/crm`) or enter a custom URL
- **Show status** — See download progress and disk usage

## Output Structure

```
~/hubspot-docs/
├── .hubspot_docs_state.json      # Tracks downloaded pages
├── api/
│   ├── crm/
│   │   ├── contacts.md
│   │   ├── companies.md
│   │   └── deals.md
│   └── marketing/
│       └── emails.md
├── guides/
│   └── api/
│       └── overview.md
└── api-reference/
    └── latest/
        └── crm/
            └── objects/
                └── contacts/
                    └── get-contact.md
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

Edit constants at the top of `main.py`:

```python
REQUEST_DELAY = 0.4   # Seconds between requests (be polite)
REQUEST_TIMEOUT = 20  # Request timeout in seconds
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
- HubSpot may have changed their sitemap URL

**Pages downloading but content is empty**
- Some pages may require JavaScript; this tool handles server-rendered content only
- Open an issue with the specific URL

**Rate limited / 429 errors**
- Increase `REQUEST_DELAY` in `main.py`

## Contributing

Contributions welcome! Please open an issue first to discuss what you'd like to change.

## License

[MIT](LICENSE) — Use freely, attribution appreciated.

## Disclaimer

This tool is for personal/educational use. Respect HubSpot's Terms of Service and robots.txt. The downloaded content remains © HubSpot, Inc.