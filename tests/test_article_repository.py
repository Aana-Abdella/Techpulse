import tempfile
import unittest
from pathlib import Path

from src.services.article_repository import ArticleRepository


class ArticleRepositoryTests(unittest.TestCase):
    def test_articles_are_persisted_and_deduplicated_by_url(self) -> None:
        article = {
            "title": "AI breakthrough",
            "category": "AI",
            "source": "Example",
            "url": "https://example.com/ai",
        }
        with tempfile.TemporaryDirectory() as directory:
            repository = ArticleRepository(Path(directory) / "data" / "news.db")
            repository.initialize()

            first_save = repository.save_articles([article, article])
            second_save = repository.save_articles([article])
            saved_articles = repository.get_latest("ai")

        self.assertEqual(first_save, 1)
        self.assertEqual(second_save, 0)
        self.assertEqual(saved_articles, [article])

    def test_invalid_articles_are_not_saved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = ArticleRepository(Path(directory) / "news.db")
            repository.initialize()

            saved_count = repository.save_articles([{"title": "Incomplete"}])

        self.assertEqual(saved_count, 0)

    def test_latest_without_category_returns_a_mix_of_tech_categories(self) -> None:
        articles = [
            {
                "title": f"AI story {index}",
                "category": "AI",
                "source": "AI source",
                "url": f"https://example.com/ai/{index}",
            }
            for index in range(3)
        ]
        articles.extend(
            [
                {
                    "title": "Technology story",
                    "category": "Technology",
                    "source": "Tech source",
                    "url": "https://example.com/technology",
                },
                {
                    "title": "Linux story",
                    "category": "Linux",
                    "source": "Linux source",
                    "url": "https://example.com/linux",
                },
            ]
        )
        with tempfile.TemporaryDirectory() as directory:
            repository = ArticleRepository(Path(directory) / "news.db")
            repository.initialize()
            repository.save_articles(articles)

            latest = repository.get_latest(limit=3)

        self.assertEqual(
            {article["category"] for article in latest},
            {"AI", "Technology", "Linux"},
        )

    def test_channel_is_saved_per_user_and_can_be_replaced(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = ArticleRepository(Path(directory) / "news.db")
            repository.initialize()
            repository.save_channel(10, -1001, "First channel", "first")
            repository.save_channel(20, -1002, "Second channel", None)
            repository.save_channel(10, -1003, "Updated channel", "updated")

            first_user_channel = repository.get_channel(10)
            second_user_channel = repository.get_channel(20)
            missing_channel = repository.get_channel(30)

        self.assertEqual(
            first_user_channel,
            (-1003, "Updated channel", "updated"),
        )
        self.assertEqual(
            second_user_channel,
            (-1002, "Second channel", None),
        )
        self.assertIsNone(missing_channel)

    def test_channel_can_be_removed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = ArticleRepository(Path(directory) / "news.db")
            repository.initialize()
            repository.save_channel(10, -1001, "Example", "example")

            first_remove = repository.remove_channel(10)
            second_remove = repository.remove_channel(10)
            saved_channel = repository.get_channel(10)

        self.assertTrue(first_remove)
        self.assertFalse(second_remove)
        self.assertIsNone(saved_channel)

    def test_ai_summary_cache_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            repository = ArticleRepository(Path(directory) / "news.db")
            repository.initialize()

            missing = repository.get_cached_summary("page-key")
            repository.save_cached_summary("page-key", '{"overview":"cached"}')
            cached = repository.get_cached_summary("page-key")
            repository.save_cached_summary("page-key", '{"overview":"updated"}')
            updated = repository.get_cached_summary("page-key")

        self.assertIsNone(missing)
        self.assertEqual(cached, '{"overview":"cached"}')
        self.assertEqual(updated, '{"overview":"updated"}')

    def test_latest_articles_support_pagination_and_validate_bounds(self) -> None:
        articles = [
            {
                "title": f"Headline {index}",
                "category": "Technology",
                "source": "Example",
                "url": f"https://example.com/{index}",
            }
            for index in range(7)
        ]
        with tempfile.TemporaryDirectory() as directory:
            repository = ArticleRepository(Path(directory) / "news.db")
            repository.initialize()
            repository.save_articles(articles)

            first_page = repository.get_latest(limit=3, offset=0)
            second_page = repository.get_latest(limit=3, offset=3)

        self.assertEqual(len(first_page), 3)
        self.assertEqual(len(second_page), 3)
        self.assertTrue(
            set(article["url"] for article in first_page).isdisjoint(
                article["url"] for article in second_page
            )
        )
        with self.assertRaises(ValueError):
            repository.get_latest(limit=0)
        with self.assertRaises(ValueError):
            repository.get_latest(offset=-1)


if __name__ == "__main__":
    unittest.main()
