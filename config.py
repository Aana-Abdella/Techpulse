"""Application settings and the RSS sources used by TechPulse."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

APP_NAME = "TechPulse"
APP_VERSION = "0.1.0"

NEWS_CATEGORIES = [
    "Technology",
    "AI",
    "Software",
    "Cybersecurity",
    "Linux",
    "Startups",
]
DATABASE_PATH = BASE_DIR / "data" / "techpulse.db"


@dataclass(frozen=True)
class FeedSource:
    name: str
    category: str
    url: str


FEEDS = (
    FeedSource("The Verge", "Technology", "https://www.theverge.com/rss/index.xml"),
    FeedSource("Wired", "Technology", "https://www.wired.com/feed/rss"),
    FeedSource("Ars Technica", "Technology", "https://feeds.arstechnica.com/arstechnica/index"),
    FeedSource("arXiv AI", "AI", "https://export.arxiv.org/rss/cs.AI"),
    FeedSource("Hacker News", "Software", "https://hnrss.org/frontpage"),
    FeedSource(
        "The Hacker News",
        "Cybersecurity",
        "https://feeds.feedburner.com/TheHackersNews",
    ),
    FeedSource("LWN", "Linux", "https://lwn.net/headlines/rss"),
    FeedSource("TechCrunch", "Startups", "https://techcrunch.com/feed/"),
)


def get_bot_token() -> str | None:
    """Return the Telegram token from the environment, if configured."""
    token = os.getenv("BOT_TOKEN", "").strip()
    return token or None


def get_gemini_api_key() -> str | None:
    """Return the optional Gemini API key from the environment."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    return api_key or None


def get_gemini_model() -> str:
    """Return the configured Gemini model or the default Flash model."""
    return os.getenv("GEMINI_MODEL", "").strip() or "gemini-flash-latest"
