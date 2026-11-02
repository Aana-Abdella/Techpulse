import asyncio
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from google.genai import errors

from src.services.ai_summary_service import (
    NewsSummary,
    SummaryUnavailableError,
    summarize_articles,
    summary_cache_key,
)


class GeminiSummaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.articles = [
            {
                "title": "New processor announced",
                "category": "Technology",
                "source": "The Verge",
                "url": "https://example.com/processor",
            },
            {
                "title": "New model released",
                "category": "AI",
                "source": "Example AI",
                "url": "https://example.com/model",
            },
        ]
        self.summary_data = {
            "overview": "Technology and AI both saw notable announcements.",
            "topics": [
                {
                    "category": "Technology",
                    "summary": "A new processor was announced.",
                    "key_points": ["Processor announcement"],
                },
                {
                    "category": "AI",
                    "summary": "A new model was released.",
                    "key_points": ["Model release"],
                },
            ],
            "takeaways": ["Hardware and AI remain active areas."],
        }

    def test_summary_uses_structured_gemini_output(self) -> None:
        client = Mock()
        client.__enter__ = Mock(return_value=client)
        client.__exit__ = Mock(return_value=False)
        client.interactions.create.return_value = SimpleNamespace(
            output_text=json.dumps(self.summary_data)
        )

        with patch(
            "src.services.ai_summary_service.genai.Client",
            return_value=client,
        ) as client_factory:
            summary = asyncio.run(
                summarize_articles(
                    self.articles,
                    api_key="test-key",
                    model="gemini-flash-latest",
                )
            )

        self.assertIsInstance(summary, NewsSummary)
        self.assertEqual(len(summary.topics), 2)
        client.interactions.create.assert_called_once()
        call = client.interactions.create.call_args
        self.assertEqual(call.kwargs["model"], "gemini-flash-latest")
        self.assertEqual(call.kwargs["response_format"]["mime_type"], "application/json")
        self.assertEqual(call.kwargs["response_format"]["type"], "text")
        self.assertNotIn(self.articles[0]["url"], call.kwargs["input"])
        self.assertEqual(call.kwargs["timeout"], 30.0)
        client_factory.assert_called_once()

    def test_summary_rejects_missing_or_invented_categories(self) -> None:
        client = Mock()
        client.__enter__ = Mock(return_value=client)
        client.__exit__ = Mock(return_value=False)
        invalid_summary = {
            **self.summary_data,
            "topics": [
                {
                    "category": "Crypto",
                    "summary": "Unrelated story.",
                    "key_points": [],
                }
            ],
        }
        client.interactions.create.return_value = SimpleNamespace(
            output_text=json.dumps(invalid_summary)
        )

        with patch(
            "src.services.ai_summary_service.genai.Client",
            return_value=client,
        ):
            with self.assertRaises(SummaryUnavailableError):
                asyncio.run(
                    summarize_articles(
                        self.articles,
                        api_key="test-key",
                        model="gemini-flash-latest",
                    )
                )

    def test_summary_requires_articles_and_an_api_key(self) -> None:
        with self.assertRaises(ValueError):
            asyncio.run(
                summarize_articles(
                    self.articles,
                    api_key=" ",
                    model="gemini-flash-latest",
                )
            )
        with self.assertRaises(ValueError):
            asyncio.run(
                summarize_articles(
                    [],
                    api_key="test-key",
                    model="gemini-flash-latest",
                )
            )

    def test_api_error_becomes_an_explicit_summary_failure(self) -> None:
        client = Mock()
        client.__enter__ = Mock(return_value=client)
        client.__exit__ = Mock(return_value=False)
        client.interactions.create.side_effect = errors.APIError(
            429,
            {"error": {"message": "rate limited"}},
        )

        with patch(
            "src.services.ai_summary_service.genai.Client",
            return_value=client,
        ):
            with self.assertRaises(SummaryUnavailableError):
                asyncio.run(
                    summarize_articles(
                        self.articles,
                        api_key="test-key",
                        model="gemini-flash-latest",
                    )
                )

    def test_cache_key_changes_with_article_content_or_model(self) -> None:
        original = summary_cache_key(self.articles, "model-a")
        same_input = summary_cache_key(self.articles, "model-a")
        different_model = summary_cache_key(self.articles, "model-b")
        changed_articles = [*self.articles]
        changed_articles[0] = {
            **self.articles[0],
            "title": "A different processor",
        }

        self.assertEqual(original, same_input)
        self.assertNotEqual(original, different_model)
        self.assertNotEqual(
            original,
            summary_cache_key(changed_articles, "model-a"),
        )


if __name__ == "__main__":
    unittest.main()
