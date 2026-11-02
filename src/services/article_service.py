"""Validation and in-memory operations for news articles."""

from typing import TypeGuard, TypedDict


class Article(TypedDict):
    title: str
    category: str
    source: str
    url: str


REQUIRED_FIELDS = ("title", "category", "source", "url")


def validate_article(article: object) -> TypeGuard[Article]:
    """Return whether a value contains non-empty strings for every required field."""
    if not isinstance(article, dict):
        return False

    return all(
        isinstance(article.get(field), str) and bool(article[field].strip())
        for field in REQUIRED_FIELDS
    )


def filter_by_category(articles: list[object], category: str) -> list[Article]:
    """Return valid articles matching a category, ignoring letter case."""
    normalized_category = category.strip().casefold()
    return [
        article
        for article in articles
        if validate_article(article)
        and article["category"].strip().casefold() == normalized_category
    ]


def filter_new_articles(
    articles: list[object], seen_urls: set[str] | None = None
) -> list[Article]:
    """Return valid articles with unseen URLs, updating the supplied set."""
    if seen_urls is None:
        seen_urls = set()

    new_articles = []
    for article in articles:
        if not validate_article(article):
            continue

        url = article["url"].strip()
        if url not in seen_urls:
            new_articles.append(article)
            seen_urls.add(url)

    return new_articles
