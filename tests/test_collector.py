import asyncio
import unittest
from unittest.mock import patch

from collector import _parse_feed, collect_articles
from config import FeedSource


class CollectorTests(unittest.TestCase):
    def test_parse_rss_skips_entries_without_a_link(self) -> None:
        content = b"""\
        <rss version="2.0"><channel>
          <item><title>First article</title><link>https://example.com/1</link></item>
          <item><title>Missing URL</title></item>
        </channel></rss>
        """

        articles = _parse_feed(content, FeedSource("Example", "AI", "https://feed"))

        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["title"], "First article")
        self.assertEqual(articles[0]["category"], "AI")

    def test_parse_atom_reads_namespaced_alternate_link(self) -> None:
        content = b"""\
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <title>Atom article</title>
            <link rel="self" href="https://example.com/feed"/>
            <link rel="alternate" href="https://example.com/article"/>
          </entry>
        </feed>
        """

        articles = _parse_feed(content, FeedSource("Example", "AI", "https://feed"))

        self.assertEqual(articles[0]["url"], "https://example.com/article")

    def test_collection_keeps_successes_when_a_feed_fails(self) -> None:
        sources = (
            FeedSource("Working", "AI", "https://example.com/ok"),
            FeedSource("Broken", "AI", "https://example.com/fail"),
        )
        article = {
            "title": "Headline",
            "category": "AI",
            "source": "Working",
            "url": "https://example.com/article",
        }

        def fetch(source: FeedSource) -> list[dict[str, str]]:
            if source.name == "Broken":
                raise OSError("feed unavailable")
            return [article]

        with patch("collector._fetch_source", side_effect=fetch):
            result = asyncio.run(collect_articles(sources))

        self.assertEqual(result.articles, [article])
        self.assertEqual(result.failures, ["Broken"])


if __name__ == "__main__":
    unittest.main()
