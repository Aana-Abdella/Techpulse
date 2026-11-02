"""Format article lists for Telegram messages."""

from html import escape
from urllib.parse import urlsplit

from src.services.ai_summary_service import NewsSummary
from src.services.article_service import Article


def _article_title(title: str, url: str) -> str:
    safe_title = escape(" ".join(title.split())[:150])
    try:
        parsed_url = urlsplit(url.strip())
    except ValueError:
        parsed_url = None
    if (
        parsed_url is not None
        and parsed_url.scheme in {"http", "https"}
        and parsed_url.netloc
    ):
        return f'<a href="{escape(url.strip(), quote=True)}">{safe_title}</a>'
    return safe_title


def format_articles(
    articles: list[Article],
    category: str | None = None,
    *,
    page: int = 0,
    page_size: int = 5,
) -> str:
    """Render escaped HTML headlines with safe clickable article titles."""
    heading = f"Latest {category} news" if category else "Latest Tech News"
    start = page * page_size + 1
    end = page * page_size + len(articles)
    lines = [
        f"📰 <b>{escape(heading)}</b>",
        f"<i>Briefing · {start:02d}–{end:02d}</i>",
        "",
    ]
    for index, article in enumerate(articles, start=start):
        title = _article_title(article["title"], article["url"])
        source = escape(" ".join(article["source"].split())[:80])
        category_name = escape(article["category"])
        lines.extend(
            (
                f"<b>{index:02d}</b>  {title}",
                f"      <i>{category_name} · {source}</i>",
                "",
            )
        )
    return "\n".join(lines).strip()


def format_ai_summary(
    summary: NewsSummary,
    articles: list[Article],
    category: str | None = None,
    *,
    page: int = 0,
    page_size: int = 5,
) -> str:
    """Render a Gemini briefing alongside clickable source headlines."""
    heading = f"{category} News Briefing" if category else "AI Tech Briefing"
    lines = [
        f"🧠 <b>{escape(heading)}</b>",
        "<i>AI summary · based on headlines, not full articles</i>",
        "",
        "<b>Executive overview</b>",
        escape(summary.overview[:400]),
        "",
    ]

    for topic in summary.topics:
        lines.extend(
            (
                f"<b>{escape(topic.category)}</b>",
                escape(topic.summary[:250]),
            )
        )
        lines.extend(
            f"• {escape(point[:100])}" for point in topic.key_points[:2]
        )
        lines.append("")

    if summary.takeaways:
        lines.extend(("<b>Key takeaways</b>",))
        lines.extend(
            f"• {escape(takeaway[:100])}" for takeaway in summary.takeaways[:3]
        )
        lines.append("")

    lines.extend(("<b>Headlines</b>",))
    start = page * page_size + 1
    for index, article in enumerate(articles, start=start):
        lines.append(
            f"{index:02d}. {_article_title(article['title'], article['url'])}"
        )
        lines.append(
            f"    <i>{escape(article['category'])} · "
            f"{escape(article['source'][:80])}</i>"
        )

    return "\n".join(lines).strip()