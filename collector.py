"""Collect articles from configured RSS and Atom feeds."""

import asyncio
import logging
from dataclasses import dataclass
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from config import FEEDS, FeedSource
from src.services.article_service import Article, validate_article

logger = logging.getLogger(__name__)
MAX_FEED_BYTES = 4 * 1024 * 1024


@dataclass
class CollectionResult:
    articles: list[Article]
    failures: list[str]


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _text(element: ElementTree.Element, name: str) -> str:
    for child in element:
        if _local_name(child.tag) == name:
            return "".join(child.itertext()).strip()
    return ""


def _item_url(item: ElementTree.Element) -> str:
    for child in item:
        if _local_name(child.tag) != "link":
            continue
        url = child.attrib.get("href", "").strip()
        if url and child.attrib.get("rel", "alternate") == "alternate":
            return url
        if not url and child.text:
            return child.text.strip()
    return ""


def _parse_feed(content: bytes, source: FeedSource) -> list[Article]:
    root = ElementTree.fromstring(content)
    articles = []

    for item in root.iter():
        if _local_name(item.tag) not in {"item", "entry"}:
            continue

        article: object = {
            "title": _text(item, "title"),
            "category": source.category,
            "source": source.name,
            "url": _item_url(item),
        }
        if validate_article(article):
            articles.append(article)

    return articles


def _fetch_source(source: FeedSource) -> list[Article]:
    request = Request(source.url, headers={"User-Agent": "TechPulse/0.1"})
    with urlopen(request, timeout=15) as response:
        content = response.read(MAX_FEED_BYTES + 1)

    if len(content) > MAX_FEED_BYTES:
        raise ValueError(f"Feed exceeds the {MAX_FEED_BYTES}-byte size limit")

    return _parse_feed(content, source)


async def collect_articles(
    sources: tuple[FeedSource, ...] = FEEDS,
) -> CollectionResult:
    """Fetch configured feeds concurrently, preserving partial successes."""
    results = await asyncio.gather(
        *(asyncio.to_thread(_fetch_source, source) for source in sources),
        return_exceptions=True,
    )

    articles: list[Article] = []
    failures = []
    for source, result in zip(sources, results):
        if isinstance(result, BaseException) and not isinstance(result, Exception):
            raise result
        if isinstance(result, Exception):
            logger.warning("Could not collect feed %s: %s", source.name, result)
            failures.append(source.name)
            continue
        articles.extend(result)

    return CollectionResult(articles=articles, failures=failures)