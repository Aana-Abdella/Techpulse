import unittest

from src.services.article_service import (
    filter_by_category,
    filter_new_articles,
    validate_article,
)


class ArticleServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.articles = [
            {
                "title": "AI breakthrough",
                "category": "AI",
                "source": "Example",
                "url": "https://example.com/ai",
            },
            {
                "title": "Linux update",
                "category": "Linux",
                "source": "Example",
                "url": "https://example.com/linux",
            },
        ]

    def test_validate_article_rejects_missing_or_blank_fields(self) -> None:
        self.assertTrue(validate_article(self.articles[0]))
        self.assertFalse(validate_article({"title": "Missing fields"}))
        self.assertFalse(
            validate_article(
                {
                    **self.articles[0],
                    "source": " ",
                }
            )
        )

    def test_filter_by_category_ignores_case_and_skips_invalid_articles(self) -> None:
        matches = filter_by_category(
            [*self.articles, None, {"category": "AI"}], "aI"
        )

        self.assertEqual([article["title"] for article in matches], ["AI breakthrough"])

    def test_filter_new_articles_updates_seen_urls(self) -> None:
        seen_urls = {self.articles[0]["url"]}

        new_articles = filter_new_articles(
            [self.articles[0], self.articles[1]], seen_urls
        )

        self.assertEqual([article["title"] for article in new_articles], ["Linux update"])
        self.assertIn(self.articles[1]["url"], seen_urls)


if __name__ == "__main__":
    unittest.main()
