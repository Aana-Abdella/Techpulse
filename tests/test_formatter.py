import unittest

from src.formatter import format_ai_summary, format_articles
from src.services.ai_summary_service import NewsSummary


class FormatterTests(unittest.TestCase):
    def test_all_news_format_includes_each_article_category(self) -> None:
        articles = [
            {
                "title": "New processor announced",
                "category": "Technology",
                "source": "The Verge",
                "url": "https://example.com/processor",
            },
            {
                "title": "New AI model announced",
                "category": "AI",
                "source": "arXiv AI",
                "url": "https://example.com/model",
            },
        ]

        message = format_articles(articles, page=1, page_size=5)

        self.assertIn("Latest Tech News", message)
        self.assertIn("Briefing · 06–07", message)
        self.assertIn("Technology · The Verge", message)
        self.assertIn("AI · arXiv AI", message)

    def test_ai_briefing_groups_categories_and_links_original_headlines(self) -> None:
        articles = [
            {
                "title": "New processor announced",
                "category": "Technology",
                "source": "The Verge",
                "url": "https://example.com/processor",
            },
            {
                "title": "New AI model announced",
                "category": "AI",
                "source": "arXiv AI",
                "url": "https://example.com/model",
            },
        ]
        summary = NewsSummary(
            overview="New developments span hardware and AI.",
            topics=[
                {
                    "category": "Technology",
                    "summary": "A processor launch was reported.",
                    "key_points": ["New processor"],
                },
                {
                    "category": "AI",
                    "summary": "A model announcement was reported.",
                    "key_points": ["New model"],
                },
            ],
            takeaways=["Both categories have new announcements."],
        )

        message = format_ai_summary(summary, articles)

        self.assertIn("<b>AI Tech Briefing</b>", message)
        self.assertIn("<b>Technology</b>", message)
        self.assertIn("<b>AI</b>", message)
        self.assertIn("Key takeaways", message)
        self.assertIn('href="https://example.com/processor"', message)


if __name__ == "__main__":
    unittest.main()
