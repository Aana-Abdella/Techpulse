import unittest

from main import (
    article_actions_keyboard,
    channel_picker_keyboard,
    channel_management_keyboard,
    main_menu_keyboard,
    summary_actions_keyboard,
)
from src.formatter import format_articles


class TelegramUiTests(unittest.TestCase):
    def test_main_menu_offers_all_news_categories_channel_and_help(self) -> None:
        keyboard = main_menu_keyboard()
        buttons = [
            button
            for row in keyboard.inline_keyboard
            for button in row
        ]

        self.assertIn("📰 All Tech News", [button.text for button in buttons])
        self.assertIn("🌐 Technology", [button.text for button in buttons])
        self.assertIn("➕ Add Channel", [button.text for button in buttons])
        self.assertIn("📣 My Channel", [button.text for button in buttons])
        self.assertIn("❔ Help", [button.text for button in buttons])

    def test_channel_picker_requests_permission_to_post(self) -> None:
        keyboard = channel_picker_keyboard()
        request = keyboard.keyboard[0][0].request_chat

        self.assertIsNotNone(request)
        assert request is not None
        assert request.bot_administrator_rights is not None
        self.assertTrue(request.chat_is_channel)
        self.assertTrue(request.bot_administrator_rights.can_post_messages)

    def test_article_actions_include_explicit_publish_button(self) -> None:
        keyboard = article_actions_keyboard("AI", page=2, has_next=True)
        buttons = [
            button
            for row in keyboard.inline_keyboard
            for button in row
        ]

        publish_button = next(button for button in buttons if "Publish" in button.text)
        self.assertEqual(publish_button.callback_data, "publish:AI:2")
        summary_button = next(button for button in buttons if "AI Summary" in button.text)
        self.assertEqual(summary_button.callback_data, "summary:AI:2")
        self.assertEqual(
            [button.text for button in keyboard.inline_keyboard[0]],
            ["‹ Previous", "Next ›"],
        )

    def test_channel_management_offers_disconnect_only_when_connected(self) -> None:
        connected_buttons = [
            button
            for row in channel_management_keyboard(connected=True).inline_keyboard
            for button in row
        ]
        empty_buttons = [
            button
            for row in channel_management_keyboard(connected=False).inline_keyboard
            for button in row
        ]

        self.assertIn("Disconnect Channel", [button.text for button in connected_buttons])
        self.assertNotIn("Disconnect Channel", [button.text for button in empty_buttons])

    def test_summary_actions_return_to_same_page(self) -> None:
        keyboard = summary_actions_keyboard("AI", page=2)
        buttons = [
            button
            for row in keyboard.inline_keyboard
            for button in row
        ]

        self.assertEqual(buttons[0].callback_data, "page:AI:2")
        self.assertEqual(buttons[1].callback_data, "publish:AI:2")

    def test_news_formatter_escapes_feed_text_and_links_valid_urls(self) -> None:
        article = {
            "title": "<script>unsafe & headline</script>",
            "category": "Technology",
            "source": "News & Co",
            "url": "https://example.com/story?a=1&b=2",
        }

        formatted = format_articles([article])

        self.assertNotIn("<script>", formatted)
        self.assertIn("&lt;script&gt;", formatted)
        self.assertIn("News &amp; Co", formatted)
        self.assertIn('href="https://example.com/story?a=1&amp;b=2"', formatted)

    def test_news_formatter_does_not_link_malformed_urls(self) -> None:
        article = {
            "title": "Headline",
            "category": "Technology",
            "source": "Example",
            "url": "https://[invalid",
        }

        formatted = format_articles([article])

        self.assertIn("Headline", formatted)
        self.assertNotIn("<a href=", formatted)


if __name__ == "__main__":
    unittest.main()
