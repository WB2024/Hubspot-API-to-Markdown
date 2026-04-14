#!/usr/bin/env python3
"""
HubSpot API Documentation Scraper TUI
Scrapes developers.hubspot.com documentation and stores it as Markdown files.
"""

import argparse
import re
import sys
import time
import json
import requests
import html2text
import questionary

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

from bs4 import BeautifulSoup
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text
from rich import box

# ─── Constants ────────────────────────────────────────────────────────────────

SITEMAP_URLS = [
    "https://developers.hubspot.com/docs/sitemap.xml",  # Main docs sitemap (API reference, guides)
    "https://developers.hubspot.com/sitemap.xml",       # General sitemap (changelog, blog - filtered to /docs only)
]

BASE_URL = "https://developers.hubspot.com"
STATE_FILE = ".hubspot_docs_state.json"
CONFIG_FILE = Path.home() / ".hubspot-docs-scraper.json"
REQUEST_DELAY = 0.5  # seconds between requests (be polite)
REQUEST_TIMEOUT = 45  # longer timeout for slow pages
MAX_RETRIES = 5       # more retries for flaky connections
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; HubSpotDocsScraper/1.0; "
        "+https://github.com/hubspot-docs-scraper)"
    )
}

console = Console()

# Session cache for sitemap (avoid re-fetching during a single run)
_sitemap_cache: list[dict] | None = None


# ─── State Management ─────────────────────────────────────────────────────────

def load_state(output_dir: Path) -> dict:
    """Load the local state file tracking downloaded pages and their lastmod dates."""
    state_path = output_dir / STATE_FILE
    if state_path.exists():
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_state(output_dir: Path, state: dict) -> None:
    """Persist state to disk."""
    state_path = output_dir / STATE_FILE
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


# ─── Config Management ────────────────────────────────────────────────────────

def load_config() -> dict:
    """Load user configuration from home directory."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_config(config: dict) -> None:
    """Save user configuration to home directory."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except IOError as e:
        console.print(f"[yellow]  Warning: Could not save config: {e}[/yellow]")


def get_output_dir_from_config() -> Path | None:
    """Get saved output directory from config, if it exists."""
    config = load_config()
    if "output_dir" in config:
        path = Path(config["output_dir"]).expanduser().resolve()
        if path.exists():
            return path
    return None


def save_output_dir_to_config(output_dir: Path) -> None:
    """Save output directory to config for future sessions."""
    config = load_config()
    config["output_dir"] = str(output_dir)
    config["last_used"] = datetime.now(timezone.utc).isoformat()
    save_config(config)


# ─── Sitemap Fetching ─────────────────────────────────────────────────────────

def fetch_sitemap_entries(sitemap_url: str) -> list[dict]:
    """
    Fetch and parse a sitemap XML, returning a list of dicts:
    [{"url": ..., "lastmod": ...}, ...]
    Handles sitemap index files recursively.
    """
    entries = []
    try:
        resp = requests.get(sitemap_url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        console.print(f"[red]  ✗ Could not fetch sitemap: {sitemap_url}\n    {e}[/red]")
        return entries

    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as e:
        console.print(f"[red]  ✗ Could not parse sitemap XML: {e}[/red]")
        return entries

    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    # Sitemap index — recurse into child sitemaps
    for sitemap in root.findall("sm:sitemap", ns):
        loc_el = sitemap.find("sm:loc", ns)
        if loc_el is not None and loc_el.text:
            child_entries = fetch_sitemap_entries(loc_el.text.strip())
            entries.extend(child_entries)

    # Regular sitemap
    for url_el in root.findall("sm:url", ns):
        loc_el = url_el.find("sm:loc", ns)
        lastmod_el = url_el.find("sm:lastmod", ns)
        if loc_el is not None and loc_el.text:
            entries.append({
                "url": loc_el.text.strip(),
                "lastmod": lastmod_el.text.strip() if lastmod_el is not None else None,
            })

    return entries


def discover_all_pages(version_filter: str | None = None, use_cache: bool = True) -> list[dict]:
    """
    Fetch all sitemap entries and filter to docs pages only.
    
    Args:
        version_filter: Optional API version to filter (e.g., 'latest', '2026-09-beta')
        use_cache: Whether to use cached sitemap from this session
    """
    global _sitemap_cache
    
    if use_cache and _sitemap_cache is not None:
        all_entries = _sitemap_cache
    else:
        all_entries = []
        with console.status("[bold cyan]Fetching sitemaps…[/bold cyan]"):
            for sitemap_url in SITEMAP_URLS:
                entries = fetch_sitemap_entries(sitemap_url)
                all_entries.extend(entries)
        _sitemap_cache = all_entries

    # Filter to developers.hubspot.com/docs pages only
    docs_entries = [
        e for e in all_entries
        if BASE_URL in e["url"] and "/docs" in e["url"]
    ]
    
    # Apply version filter if specified
    if version_filter:
        docs_entries = [
            e for e in docs_entries
            if f"/api-reference/{version_filter}/" in e["url"]
            or "/guides/" in e["url"]  # Always include guides
            or "/api-reference/" not in e["url"]  # Include non-API-reference pages
        ]

    # Deduplicate
    seen = set()
    unique = []
    for e in docs_entries:
        if e["url"] not in seen:
            seen.add(e["url"])
            unique.append(e)

    return unique


def clear_sitemap_cache() -> None:
    """Clear the sitemap cache to force a fresh fetch."""
    global _sitemap_cache
    _sitemap_cache = None


# ─── URL → File Path Mapping ──────────────────────────────────────────────────

def url_to_filepath(url: str, output_dir: Path) -> Path:
    """
    Convert a docs URL to a logical local file path.

    Example:
      https://developers.hubspot.com/docs/api/crm/contacts
      → <output_dir>/api/crm/contacts.md

      https://developers.hubspot.com/docs/cms/building-blocks/templates
      → <output_dir>/cms/building-blocks/templates.md
    """
    # Strip the base and /docs prefix
    path = url.replace(BASE_URL, "").lstrip("/")
    if path.startswith("docs/"):
        path = path[len("docs/"):]
    elif path == "docs":
        path = "index"

    # Clean up any query strings or fragments
    path = path.split("?")[0].split("#")[0].rstrip("/")

    if not path:
        path = "index"

    return output_dir / Path(path).with_suffix(".md")


# ─── Page Scraping ────────────────────────────────────────────────────────────

def scrape_page_to_markdown(url: str, retries: int = MAX_RETRIES) -> Optional[str]:
    """
    Download a HubSpot docs page and convert it to clean Markdown,
    preserving all code blocks.
    
    Args:
        url: The page URL to scrape
        retries: Number of retry attempts for failed requests
    """
    last_error = None
    for attempt in range(retries):
        try:
            # Use longer timeout for retries
            timeout = REQUEST_TIMEOUT + (attempt * 15)
            resp = requests.get(url, headers=HEADERS, timeout=timeout)
            resp.raise_for_status()
            break
        except requests.exceptions.Timeout as e:
            last_error = e
            if attempt < retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4, 8, 16s
                time.sleep(wait_time)
                continue
        except requests.RequestException as e:
            last_error = e
            if attempt < retries - 1:
                time.sleep(1 * (attempt + 1))
                continue
    else:
        console.print(f"[red]    ✗ Request failed for {url} after {retries} attempts: {last_error}[/red]")
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    # ── Try to extract the main documentation content ──
    # HubSpot docs use several possible container selectors; try them in order.
    # The new Mintlify-based docs use Tailwind classes; find the content area.
    content = (
        soup.find("main")
        or soup.find("article")
        or soup.find(id="hs_cos_wrapper_content")
        or soup.find(class_="developer-docs__content")
        or soup.find(class_="docs-content")
        or soup.find(class_="content")
    )
    
    # For Mintlify/Tailwind-based HubSpot docs: find the largest px-5 div (main content area)
    if content is None:
        px5_divs = soup.find_all("div", class_="px-5")
        if px5_divs:
            content = max(px5_divs, key=lambda d: len(d.get_text()))
    
    # Fallback to body
    if content is None:
        content = soup.body

    if content is None:
        return None

    # ── Remove navigation, headers, footers, sidebars ──
    for tag in content.find_all(
        ["nav", "footer", "header", "aside", "script", "style", "noscript", "svg", "iframe"]
    ):
        tag.decompose()
    
    # ── Remove interactive UI elements that don't make sense in static markdown ──
    # Remove buttons and interactive elements
    for tag in content.find_all(["button", "input", "select", "form"]):
        tag.decompose()
    
    # Remove elements with interactive/UI text
    interactive_texts = [
        "Show child attributes", "Hide child attributes",
        "Try it", "Copy", "Copied",
        "Yes", "No",  # Feedback buttons
        "Was this page helpful?",
        "Navigate to header",
    ]
    for text in interactive_texts:
        for tag in content.find_all(string=re.compile(re.escape(text), re.IGNORECASE)):
            parent = tag.parent
            if parent and parent.name in ["button", "span", "div", "a"]:
                # Check if it's a small UI element (not main content)
                if len(parent.get_text()) < 50:
                    parent.decompose()
    
    # Remove duplicate API panels - keep only the main content, not the sticky sidebar
    # The API docs show the same curl/response in two places
    sticky_panels = content.find_all("div", class_=lambda c: c and "sticky" in str(c))
    for panel in sticky_panels:
        # Only remove if it looks like a duplicate code panel
        if panel.find("pre") and len(panel.get_text()) < 5000:
            panel.decompose()
    
    # Keywords that indicate non-content elements
    # Match only if keyword is the class name or appears at the start (e.g., "nav-item")
    # Avoid matching Tailwind utility classes like "pt-[calc(9rem+var(--banner-height,0px))]"
    def is_nav_class(class_list):
        if not class_list:
            return False
        keywords = ["sidebar", "nav", "menu", "breadcrumb", "footer",
                    "header", "toc", "cookie", "banner", "feedback"]
        for cls in class_list:
            cls_lower = cls.lower()
            for kw in keywords:
                # Match: exact keyword, keyword at start, or keyword after common prefixes
                if cls_lower == kw or cls_lower.startswith(kw + "-") or cls_lower.startswith(kw + "_"):
                    return True
                # Also match if keyword appears after a hyphen (e.g., "site-nav", "page-header")
                if f"-{kw}" in cls_lower and not cls_lower.startswith("pt-") and not cls_lower.startswith("var("):
                    return True
        return False
    
    for tag in content.find_all(class_=is_nav_class):
        tag.decompose()

    # ── Pre-process code blocks so html2text preserves them ──
    # Wrap <pre><code> blocks with fenced markers html2text will honour.
    for pre in content.find_all("pre"):
        code_el = pre.find("code")
        lang = ""
        if code_el:
            # Try to detect language from class (e.g., class="language-python")
            for cls in (code_el.get("class") or []):
                if cls.startswith("language-"):
                    lang = cls[len("language-"):]
                    break
            code_text = code_el.get_text()
        else:
            code_text = pre.get_text()
        
        # Auto-detect language if not found
        if not lang:
            code_stripped = code_text.strip()
            if code_stripped.startswith("curl ") or code_stripped.startswith("curl\n"):
                lang = "bash"
            elif code_stripped.startswith("{") or code_stripped.startswith("["):
                lang = "json"
            elif "import " in code_stripped[:100] or "from " in code_stripped[:100]:
                lang = "python"
            elif "const " in code_stripped[:100] or "function " in code_stripped[:100]:
                lang = "javascript"

        fence = f"\n```{lang}\n{code_text.strip()}\n```\n"
        new_tag = soup.new_tag("div")
        new_tag.string = fence
        pre.replace_with(new_tag)

    # ── Convert to Markdown ──
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = True  # Ignore images (usually icons)
    converter.body_width = 0          # don't wrap lines
    converter.protect_links = True
    converter.wrap_links = False
    converter.mark_code = True
    converter.ignore_emphasis = False

    raw_md = converter.handle(str(content))
    
    # ── Post-process markdown cleanup ──
    raw_md = clean_markdown(raw_md)

    # ── Add page header ──
    title_el = soup.find("title")
    title = title_el.get_text().strip() if title_el else url
    # Clean up common HubSpot title suffix
    title = title.replace(" | HubSpot Developer Docs", "").strip()
    title = title.replace(" - HubSpot docs", "").strip()

    header = (
        f"# {title}\n\n"
        f"> **Source:** [{url}]({url})  \n"
        f"> **Scraped:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        f"---\n\n"
    )

    return header + raw_md


def clean_markdown(md: str) -> str:
    """Clean up and format the markdown output."""
    
    # Remove zero-width spaces and other invisible unicode
    md = md.replace("\u200b", "")  # Zero-width space
    md = md.replace("\u200c", "")  # Zero-width non-joiner
    md = md.replace("\u200d", "")  # Zero-width joiner
    md = md.replace("\ufeff", "")  # BOM
    md = md.replace("\u00a0", " ")  # Non-breaking space -> regular space
    
    # Remove "Show child attributes" and similar UI text that might have slipped through
    ui_patterns = [
        r"Show child attributes\s*",
        r"Hide child attributes\s*",
        r"Navigate to header\s*",
        r"Was this page helpful\?\s*",
        r"Last modified on [A-Za-z]+ \d+, \d+\s*",
        r"⌘[A-Z]\s*",  # Keyboard shortcuts like ⌘I
    ]
    for pattern in ui_patterns:
        md = re.sub(pattern, "", md, flags=re.IGNORECASE)
    
    # Fix code blocks that got mangled
    # Remove backslashes before dashes in code blocks (curl \--url -> curl --url)
    def fix_code_block(match):
        code = match.group(0)
        code = code.replace("\\--", "--")
        code = code.replace("\\ --", " --")
        return code
    
    md = re.sub(r"```[\s\S]*?```", fix_code_block, md)
    
    # Remove duplicate blank lines (more than 2 newlines -> 2)
    md = re.sub(r"\n{4,}", "\n\n\n", md)
    
    # Remove lines that are just whitespace
    md = re.sub(r"\n[ \t]+\n", "\n\n", md)
    
    # Clean up bullet points
    md = re.sub(r"^\s*\*\s+\*\s+", "  * ", md, flags=re.MULTILINE)
    
    # Remove orphaned list markers
    md = re.sub(r"^\s*\*\s*$", "", md, flags=re.MULTILINE)
    
    # Fix headers that might have extra spaces
    md = re.sub(r"^(#{1,6})\s{2,}", r"\1 ", md, flags=re.MULTILINE)
    
    # Remove "Option 1", "Option 2" type selectors (UI tabs)
    md = re.sub(r"^\s*\*\s*Option \d+\s*$", "", md, flags=re.MULTILINE)
    
    # Clean up HubSpot-specific UI remnants
    md = re.sub(r"oauth2private_appsoauth2private_apps", "OAuth 2.0 / Private Apps", md)
    md = re.sub(r"YesNo\s*$", "", md, flags=re.MULTILINE)
    
    # Remove lines that are just emojis or icons
    md = re.sub(r"^[^\w\n]*$", "", md, flags=re.MULTILINE)
    
    # Final cleanup of excessive newlines
    md = re.sub(r"\n{3,}", "\n\n", md)
    
    return md.strip()


# ─── Download Logic ──────────────────────────────────────────────────────────

def download_page(entry: dict, output_dir: Path, state: dict) -> bool:
    """Download a single page and save it. Returns True on success."""
    url = entry["url"]
    filepath = url_to_filepath(url, output_dir)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    markdown = scrape_page_to_markdown(url)
    if markdown is None:
        return False

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown)
    except IOError as e:
        console.print(f"[red]    ✗ Could not write {filepath}: {e}[/red]")
        return False

    state[url] = {
        "lastmod": entry.get("lastmod"),
        "file": str(filepath.relative_to(output_dir)),
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
    }
    return True


# ─── TUI Actions ──────────────────────────────────────────────────────────────

def prompt_output_dir(use_saved: bool = True) -> Path:
    """
    Prompt user for the markdown output directory.
    
    Args:
        use_saved: If True, offer to use the previously saved directory
    """
    # Check for saved directory
    saved_dir = get_output_dir_from_config()
    
    if use_saved and saved_dir:
        use_saved_choice = questionary.confirm(
            f"📁  Use saved directory? ({saved_dir})",
            default=True,
        ).ask()
        if use_saved_choice is None:
            console.print("[yellow]Cancelled.[/yellow]")
            sys.exit(0)
        if use_saved_choice:
            return saved_dir
    
    default = str(saved_dir) if saved_dir else str(Path.home() / "hubspot-docs")
    answer = questionary.text(
        "📁  Where should Markdown files be stored?",
        default=default,
        validate=lambda v: True if v.strip() else "Please enter a path.",
    ).ask()
    if answer is None:
        console.print("[yellow]Cancelled.[/yellow]")
        sys.exit(0)
    
    output_dir = Path(answer.strip()).expanduser().resolve()
    
    # Save for future sessions
    save_output_dir_to_config(output_dir)
    
    return output_dir


def action_download_missing(output_dir: Path) -> None:
    """Find and download all missing documentation pages."""
    console.rule("[bold cyan]Download Missing Pages[/bold cyan]")

    pages = discover_all_pages()
    if not pages:
        console.print("[yellow]  No pages found in sitemap.[/yellow]")
        return

    state = load_state(output_dir)

    missing = [
        p for p in pages
        if not url_to_filepath(p["url"], output_dir).exists()
    ]

    if not missing:
        console.print(
            f"[green]  ✓ All {len(pages)} pages already downloaded.[/green]"
        )
        return

    console.print(
        f"  Found [bold]{len(pages)}[/bold] total pages, "
        f"[bold yellow]{len(missing)}[/bold yellow] missing."
    )

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Downloading…", total=len(missing))
        ok = 0
        fail = 0
        for entry in missing:
            short = entry["url"].replace(BASE_URL, "")
            progress.update(task, description=f"[cyan]{short[:60]}[/cyan]")
            if download_page(entry, output_dir, state):
                ok += 1
            else:
                fail += 1
            save_state(output_dir, state)
            progress.advance(task)
            time.sleep(REQUEST_DELAY)

    console.print(
        f"\n  [green]✓ Downloaded:[/green] {ok}   "
        f"[red]✗ Failed:[/red] {fail}"
    )


def action_check_updates(output_dir: Path) -> None:
    """Check the sitemap for pages with newer lastmod dates than local copies."""
    console.rule("[bold cyan]Check for Updated Pages[/bold cyan]")

    pages = discover_all_pages()
    if not pages:
        console.print("[yellow]  No pages found in sitemap.[/yellow]")
        return

    state = load_state(output_dir)
    updates = []

    for entry in pages:
        url = entry["url"]
        sitemap_lastmod = entry.get("lastmod")
        if not sitemap_lastmod:
            continue
        if url in state:
            local_lastmod = state[url].get("lastmod")
            if local_lastmod and sitemap_lastmod > local_lastmod:
                updates.append(entry)
        # If not in state but file exists, also flag as needing update
        elif url_to_filepath(url, output_dir).exists():
            updates.append(entry)

    if not updates:
        console.print("[green]  ✓ All local docs are up to date.[/green]")
        return

    # Show the user what needs updating
    table = Table(
        title=f"{len(updates)} Page(s) Have Updates",
        box=box.ROUNDED,
        show_lines=False,
    )
    table.add_column("Page", style="cyan", no_wrap=False, max_width=60)
    table.add_column("Sitemap Date", style="yellow", no_wrap=True)
    table.add_column("Local Date", style="dim", no_wrap=True)

    for entry in updates[:40]:  # show max 40 in table
        url = entry["url"]
        sitemap_lastmod = entry.get("lastmod", "—")
        local_lastmod = state.get(url, {}).get("lastmod", "—")
        short_url = url.replace(BASE_URL + "/docs/", "")
        table.add_row(short_url, sitemap_lastmod, local_lastmod)

    if len(updates) > 40:
        table.caption = f"… and {len(updates) - 40} more"

    console.print(table)

    proceed = questionary.confirm(
        f"  Download all {len(updates)} updated page(s)?",
        default=True,
    ).ask()

    if not proceed:
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Updating…", total=len(updates))
        ok = 0
        fail = 0
        for entry in updates:
            short = entry["url"].replace(BASE_URL, "")
            progress.update(task, description=f"[cyan]{short[:60]}[/cyan]")
            if download_page(entry, output_dir, state):
                ok += 1
            else:
                fail += 1
            save_state(output_dir, state)
            progress.advance(task)
            time.sleep(REQUEST_DELAY)

    console.print(
        f"\n  [green]✓ Updated:[/green] {ok}   "
        f"[red]✗ Failed:[/red] {fail}"
    )


def action_download_specific(output_dir: Path) -> None:
    """Let user pick a specific section or URL to download."""
    console.rule("[bold cyan]Download Specific Pages[/bold cyan]")

    pages = discover_all_pages()
    if not pages:
        console.print("[yellow]  No pages found in sitemap.[/yellow]")
        return

    # Group pages by top-level section
    sections: dict[str, list[dict]] = {}
    for entry in pages:
        path = entry["url"].replace(BASE_URL + "/docs/", "").lstrip("/")
        top = path.split("/")[0] if "/" in path else path
        sections.setdefault(top, []).append(entry)

    section_choices = sorted(sections.keys())
    section_choices = ["[ALL PAGES]", "[ENTER CUSTOM URL]"] + section_choices

    choice = questionary.select(
        "  Select a section to download:",
        choices=section_choices,
    ).ask()

    if choice is None:
        return

    if choice == "[ALL PAGES]":
        targets = pages
    elif choice == "[ENTER CUSTOM URL]":
        url = questionary.text(
            "  Enter the full URL to download:",
            validate=lambda v: True if v.startswith("http") else "Enter a valid URL.",
        ).ask()
        if not url:
            return
        # Match against known pages or create a synthetic entry
        matched = [p for p in pages if p["url"].rstrip("/") == url.rstrip("/")]
        targets = matched if matched else [{"url": url, "lastmod": None}]
    else:
        targets = sections[choice]

    state = load_state(output_dir)

    # Only download missing ones (or ask)
    missing = [t for t in targets if not url_to_filepath(t["url"], output_dir).exists()]
    existing = [t for t in targets if url_to_filepath(t["url"], output_dir).exists()]

    console.print(
        f"\n  Section [bold]{choice}[/bold]: "
        f"[bold]{len(targets)}[/bold] pages, "
        f"[green]{len(existing)} already downloaded[/green], "
        f"[yellow]{len(missing)} missing[/yellow]."
    )

    if not missing:
        console.print("[green]  ✓ Nothing to download.[/green]")
        return

    proceed = questionary.confirm(
        f"  Download {len(missing)} missing page(s)?",
        default=True,
    ).ask()
    if not proceed:
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Downloading…", total=len(missing))
        ok = 0
        fail = 0
        for entry in missing:
            short = entry["url"].replace(BASE_URL, "")
            progress.update(task, description=f"[cyan]{short[:60]}[/cyan]")
            if download_page(entry, output_dir, state):
                ok += 1
            else:
                fail += 1
            save_state(output_dir, state)
            progress.advance(task)
            time.sleep(REQUEST_DELAY)

    console.print(
        f"\n  [green]✓ Downloaded:[/green] {ok}   "
        f"[red]✗ Failed:[/red] {fail}"
    )


def action_show_status(output_dir: Path) -> None:
    """Show a summary of what's downloaded vs available."""
    console.rule("[bold cyan]Local Documentation Status[/bold cyan]")

    pages = discover_all_pages()
    state = load_state(output_dir)

    downloaded = sum(
        1 for p in pages if url_to_filepath(p["url"], output_dir).exists()
    )
    missing = len(pages) - downloaded

    # Disk usage
    total_size = sum(
        f.stat().st_size
        for f in output_dir.rglob("*.md")
        if f.is_file()
    ) if output_dir.exists() else 0

    table = Table(box=box.SIMPLE_HEAVY, show_header=False)
    table.add_column("Key", style="bold")
    table.add_column("Value", style="cyan")
    table.add_row("Output directory", str(output_dir))
    table.add_row("Total pages in sitemap", str(len(pages)))
    table.add_row("Downloaded", f"[green]{downloaded}[/green]")
    table.add_row("Missing", f"[yellow]{missing}[/yellow]")
    table.add_row(
        "Disk usage",
        f"{total_size / 1024:.1f} KB" if total_size < 1_048_576
        else f"{total_size / 1_048_576:.1f} MB"
    )
    console.print(table)


def action_change_directory() -> Path:
    """Prompt the user to change the output directory."""
    return prompt_output_dir(use_saved=False)


def action_clear_config() -> None:
    """Clear the saved configuration."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
        console.print("[green]  ✓ Configuration cleared.[/green]")
    else:
        console.print("[yellow]  No configuration file found.[/yellow]")


def action_refresh_sitemap() -> None:
    """Force refresh the sitemap cache."""
    clear_sitemap_cache()
    console.print("[green]  ✓ Sitemap cache cleared. Will re-fetch on next action.[/green]")


# ─── Main Menu ────────────────────────────────────────────────────────────────

MENU_CHOICES = [
    questionary.Choice("📥  Download missing pages",       "missing"),
    questionary.Choice("🔄  Check for & download updates", "updates"),
    questionary.Choice("🎯  Download specific section",    "specific"),
    questionary.Choice("📊  Show status",                  "status"),
    questionary.Separator(),
    questionary.Choice("📁  Change output directory",      "change_dir"),
    questionary.Choice("🔃  Refresh sitemap cache",        "refresh"),
    questionary.Choice("🗑️   Clear saved settings",         "clear_config"),
    questionary.Separator(),
    questionary.Choice("🚪  Quit",                         "quit"),
]


def print_banner() -> None:
    console.print(
        Panel.fit(
            Text.assemble(
                ("  HubSpot Docs Scraper  ", "bold white on dark_orange"),
            ),
            subtitle="[dim]developers.hubspot.com → Markdown[/dim]",
            border_style="orange1",
        )
    )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Scrape HubSpot API documentation to Markdown files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                        # Interactive TUI mode
  python main.py --download             # Download all missing pages (non-interactive)
  python main.py --status               # Show download status
  python main.py --output ~/my-docs     # Use specific output directory
  python main.py --download --output .  # Download to current directory
        """
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        metavar="DIR",
        help="Output directory for Markdown files (saves as default for future runs)"
    )
    parser.add_argument(
        "-d", "--download",
        action="store_true",
        help="Download all missing pages (non-interactive mode)"
    )
    parser.add_argument(
        "-u", "--update",
        action="store_true",
        help="Check for and download updated pages (non-interactive mode)"
    )
    parser.add_argument(
        "-s", "--status",
        action="store_true",
        help="Show download status and exit"
    )
    parser.add_argument(
        "--clear-config",
        action="store_true",
        help="Clear saved configuration and exit"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    
    # Handle --clear-config
    if args.clear_config:
        action_clear_config()
        return
    
    print_banner()
    console.print()
    
    # Determine output directory
    if args.output:
        output_dir = Path(args.output).expanduser().resolve()
        save_output_dir_to_config(output_dir)
    elif args.download or args.update or args.status:
        # Non-interactive mode: use saved dir or fail
        output_dir = get_output_dir_from_config()
        if not output_dir:
            console.print("[red]Error: No saved output directory. Run interactively first or use --output.[/red]")
            sys.exit(1)
    else:
        output_dir = prompt_output_dir()
    
    output_dir.mkdir(parents=True, exist_ok=True)
    console.print(
        f"  Using output directory: [bold cyan]{output_dir}[/bold cyan]\n"
    )
    
    # Non-interactive modes
    if args.status:
        action_show_status(output_dir)
        return
    
    if args.download:
        action_download_missing(output_dir)
        return
    
    if args.update:
        action_check_updates(output_dir)
        return

    # Interactive TUI mode
    while True:
        choice = questionary.select(
            "  What would you like to do?",
            choices=MENU_CHOICES,
        ).ask()

        if choice is None or choice == "quit":
            console.print("\n[dim]Goodbye! 👋[/dim]\n")
            break
        elif choice == "missing":
            action_download_missing(output_dir)
        elif choice == "updates":
            action_check_updates(output_dir)
        elif choice == "specific":
            action_download_specific(output_dir)
        elif choice == "status":
            action_show_status(output_dir)
        elif choice == "change_dir":
            output_dir = action_change_directory()
            output_dir.mkdir(parents=True, exist_ok=True)
            console.print(
                f"  Switched to: [bold cyan]{output_dir}[/bold cyan]\n"
            )
        elif choice == "refresh":
            action_refresh_sitemap()
        elif choice == "clear_config":
            action_clear_config()

        console.print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[dim]Interrupted. Goodbye! 👋[/dim]\n")
        sys.exit(0)