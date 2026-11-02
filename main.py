"""Telegram entry point and command handlers for TechPulse."""

import asyncio
import logging
import sqlite3
from html import escape

from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command, CommandStart
from aiogram.filters.command import CommandObject
from aiogram.types import (
    CallbackQuery,
    ChatAdministratorRights,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    KeyboardButtonRequestChat,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from collector import collect_articles
from config import (
    APP_NAME,
    APP_VERSION,
    DATABASE_PATH,
    FEEDS,
    NEWS_CATEGORIES,
    get_bot_token,
    get_gemini_api_key,
    get_gemini_model,
)
from src.formatter import format_ai_summary, format_articles
from src.services.ai_summary_service import (
    NewsSummary,
    SummaryUnavailableError,
    summarize_articles,
    summary_cache_key,
)
from src.services.article_repository import ArticleRepository

logger = logging.getLogger(__name__)
CHANNEL_REQUEST_ID = 1
NEWS_PAGE_SIZE = 5
CATEGORY_ICONS = {
    "Technology": "🌐",
    "AI": "🤖",
    "Software": "💻",
    "Cybersecurity": "🛡️",
    "Linux": "🐧",
    "Startups": "🚀",
}


def main_menu_keyboard() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="📰 All Tech News", callback_data="news:all")],
    ]
    for index in range(0, len(NEWS_CATEGORIES), 2):
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{CATEGORY_ICONS.get(category, '🗞️')} {category}",
                    callback_data=f"news:{category}",
                )
                for category in NEWS_CATEGORIES[index : index + 2]
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="➕ Add Channel", callback_data="channel:add"
            ),
            InlineKeyboardButton(
                text="📣 My Channel", callback_data="channel:manage"
            ),
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text="❔ Help", callback_data="help:show"
            ),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _channel_admin_rights(*, can_post_messages: bool) -> ChatAdministratorRights:
    return ChatAdministratorRights(
        is_anonymous=False,
        can_manage_chat=True,
        can_delete_messages=False,
        can_manage_video_chats=False,
        can_restrict_members=False,
        can_promote_members=False,
        can_change_info=False,
        can_invite_users=False,
        can_post_messages=can_post_messages,
        can_post_stories=False,
        can_edit_stories=False,
        can_delete_stories=False,
        can_send_welcome_messages=False,
    )


def channel_picker_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📣 Select a channel",
                    request_chat=KeyboardButtonRequestChat(
                        request_id=CHANNEL_REQUEST_ID,
                        chat_is_channel=True,
                        user_administrator_rights=_channel_admin_rights(
                            can_post_messages=False
                        ),
                        bot_administrator_rights=_channel_admin_rights(
                            can_post_messages=True
                        ),
                        request_title=True,
                        request_username=True,
                    ),
                )
            ],
            [KeyboardButton(text="Cancel")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Choose a channel you manage",
    )


def article_actions_keyboard(
    category: str | None,
    *,
    page: int = 0,
    has_next: bool = False,
) -> InlineKeyboardMarkup:
    category_value = category or "all"
    pagination = []
    if page > 0:
        pagination.append(
            InlineKeyboardButton(
                text="‹ Previous",
                callback_data=f"page:{category_value}:{page - 1}",
            )
        )
    if has_next:
        pagination.append(
            InlineKeyboardButton(
                text="Next ›",
                callback_data=f"page:{category_value}:{page + 1}",
            )
        )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            pagination,
            [
                InlineKeyboardButton(
                    text="✨ AI Summary",
                    callback_data=f"summary:{category_value}:{page}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="📣 Publish to my channel",
                    callback_data=f"publish:{category_value}:{page}",
                )
            ],
            [
                InlineKeyboardButton(
                    text="↩️ News menu", callback_data="menu:show"
                )
            ],
        ]
    )


def summary_actions_keyboard(
    category: str | None,
    *,
    page: int,
) -> InlineKeyboardMarkup:
    category_value = category or "all"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="↩️ Headlines",
                    callback_data=f"page:{category_value}:{page}",
                ),
                InlineKeyboardButton(
                    text="📣 Publish headlines",
                    callback_data=f"publish:{category_value}:{page}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="↩️ News menu", callback_data="menu:show"
                )
            ],
        ]
    )


def channel_management_keyboard(*, connected: bool) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text="🔄 Change Channel",
                callback_data="channel:add",
            )
        ]
    ]
    if connected:
        rows.append(
            [
                InlineKeyboardButton(
                    text="Disconnect Channel",
                    callback_data="channel:disconnect:confirm",
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton(text="↩️ News menu", callback_data="menu:show")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def disconnect_confirmation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Yes, disconnect",
                    callback_data="channel:disconnect:yes",
                ),
                InlineKeyboardButton(
                    text="Keep channel",
                    callback_data="channel:manage",
                ),
            ]
        ]
    )


def help_text() -> str:
    return (
        "✨ <b>How to use TechPulse</b>\n\n"
        "Choose a topic below to browse the latest headlines, or tap "
        "<b>All Tech News</b> for a mix of technology stories.\n\n"
        "Use /news or /news &lt;category&gt; to request headlines directly.\n"
        "Use /addchannel to connect a channel or /mychannel to manage it.\n\n"
        "Tap <b>✨ AI Summary</b> for a Gemini briefing grouped by category.\n"
        "➕ <b>Add Channel</b> connects a channel where the bot can post. "
        "You must manage the channel and grant the bot permission to post.\n"
        "📣 Publishing only happens when you tap the publish button."
    )


async def show_news(
    message: Message,
    repository: ArticleRepository,
    category: str | None,
    *,
    page: int = 0,
    refresh: bool = True,
    edit_message: bool = False,
) -> None:
    category_label = category or "technology"
    progress_text = f"✨ <b>Finding the latest {category_label} stories…</b>"
    if edit_message:
        await message.edit_text(progress_text, parse_mode="HTML")
        progress_message = message
    else:
        progress_message = await message.answer(
            progress_text,
            parse_mode="HTML",
        )

    failures: list[str] = []
    try:
        if refresh:
            result = await collect_articles()
            repository.save_articles(result.articles)
            failures = result.failures
        articles = repository.get_latest(
            category,
            limit=NEWS_PAGE_SIZE + 1,
            offset=page * NEWS_PAGE_SIZE,
        )
    except sqlite3.Error:
        logger.exception("Could not read or save articles")
        await progress_message.edit_text(
            "TechPulse could not access its article database. Please try again later."
        )
        return

    has_next = len(articles) > NEWS_PAGE_SIZE
    articles = articles[:NEWS_PAGE_SIZE]
    if articles:
        response = format_articles(
            articles,
            category,
            page=page,
            page_size=NEWS_PAGE_SIZE,
        )
        markup = article_actions_keyboard(
            category,
            page=page,
            has_next=has_next,
        )
    else:
        response = (
            f"<b>No more {category_label} articles are available.</b>"
            if page
            else f"<b>No {category_label} articles are available right now.</b>"
        )
        markup = main_menu_keyboard()

    if failures:
        failed_sources = escape(", ".join(failures))
        response += (
            f"\n\n<i>Some feeds could not be reached: "
            f"{failed_sources}.</i>"
        )

    await progress_message.edit_text(
        response,
        parse_mode="HTML",
        reply_markup=markup,
        link_preview_options={"is_disabled": True},
    )


def create_dispatcher(repository: ArticleRepository) -> Dispatcher:
    dispatcher = Dispatcher()

    @dispatcher.message(CommandStart())
    async def start_handler(message: Message) -> None:
        await message.answer(
            "✨ <b>Welcome to TechPulse</b>\n\n"
            "Your personal pulse on technology. Explore fresh stories by topic, "
            "or browse all tech news in one place.\n\n"
            "<i>Choose a category to get started:</i>",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )

    @dispatcher.message(Command("help"))
    async def help_handler(message: Message) -> None:
        await message.answer(
            help_text(), parse_mode="HTML", reply_markup=main_menu_keyboard()
        )

    @dispatcher.message(Command("news"))
    async def news_handler(message: Message, command: CommandObject) -> None:
        requested_category = (command.args or "").strip()
        category = None
        if requested_category:
            category = next(
                (
                    known_category
                    for known_category in NEWS_CATEGORIES
                    if known_category.casefold() == requested_category.casefold()
                ),
                None,
            )
            if category is None:
                await message.answer(
                    "Unknown category. Use /categories to see the available topics."
                )
                return

        await show_news(message, repository, category)

    @dispatcher.message(Command("categories"))
    async def categories_handler(message: Message) -> None:
        await message.answer(
            "🗂️ <b>Choose your news categories</b>",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )

    @dispatcher.message(Command("addchannel"))
    async def add_channel_handler(message: Message) -> None:
        if message.chat.type != "private":
            await message.answer("Please add a channel from your private chat with TechPulse.")
            return
        await message.answer(
            "📣 <b>Connect your channel</b>\n\n"
            "Select a channel you manage. Telegram will ask you to grant TechPulse "
            "permission to post there.\n\n"
            "<i>Nothing will be published until you choose “Publish to my channel.”</i>",
            parse_mode="HTML",
            reply_markup=channel_picker_keyboard(),
        )

    @dispatcher.message(Command("mychannel"))
    async def my_channel_handler(message: Message) -> None:
        if message.chat.type != "private":
            await message.answer("Please manage your channel in a private chat with TechPulse.")
            return
        user = message.from_user
        if user is None:
            await message.answer("Open TechPulse in a private chat to manage your channel.")
            return
        try:
            destination = repository.get_channel(user.id)
        except sqlite3.Error:
            logger.exception("Could not load the saved channel")
            await message.answer("TechPulse could not load your channel settings.")
            return

        if destination is None:
            text = (
                "📣 <b>No channel connected yet</b>\n\n"
                "Connect a channel you manage to publish your selected headlines."
            )
        else:
            username = (
                f"\n@{escape(destination.username)}"
                if destination.username
                else ""
            )
            text = (
                f"📣 <b>Connected channel</b>\n\n"
                f"{escape(destination.title)}{username}\n\n"
                "Publishing is always started manually from a news briefing."
            )
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=channel_management_keyboard(
                connected=destination is not None
            ),
        )

    @dispatcher.message(F.chat_shared)
    async def channel_shared_handler(message: Message) -> None:
        shared_chat = message.chat_shared
        user = message.from_user
        if (
            message.chat.type != "private"
            or shared_chat is None
            or shared_chat.request_id != CHANNEL_REQUEST_ID
            or user is None
        ):
            return

        title = shared_chat.title or shared_chat.username or "Your channel"
        try:
            repository.save_channel(
                user_id=user.id,
                chat_id=shared_chat.chat_id,
                title=title,
                username=shared_chat.username,
            )
        except sqlite3.Error:
            logger.exception("Could not save the selected channel")
            await message.answer(
                "TechPulse could not save your channel. Please try /addchannel again.",
                reply_markup=ReplyKeyboardRemove(),
            )
            return

        await message.answer(
            f"✅ <b>{escape(title)}</b> is connected.\n\n"
            "You can now choose a news category and tap "
            "“Publish to my channel” whenever you want to post headlines.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove(),
        )

    @dispatcher.message(Command("cancel"))
    async def cancel_handler(message: Message) -> None:
        await message.answer(
            "Channel selection cancelled.",
            reply_markup=ReplyKeyboardRemove(),
        )

    @dispatcher.message(F.text.casefold() == "cancel")
    async def cancel_button_handler(message: Message) -> None:
        await message.answer(
            "Channel selection cancelled.",
            reply_markup=ReplyKeyboardRemove(),
        )

    @dispatcher.callback_query(F.data == "menu:show")
    async def menu_callback(callback: CallbackQuery) -> None:
        await callback.answer()
        if callback.message:
            await callback.message.answer(
                "🗂️ <b>Choose a news category</b>",
                parse_mode="HTML",
                reply_markup=main_menu_keyboard(),
            )

    @dispatcher.callback_query(F.data == "help:show")
    async def help_callback(callback: CallbackQuery) -> None:
        await callback.answer()
        if callback.message:
            await callback.message.answer(
                help_text(), parse_mode="HTML", reply_markup=main_menu_keyboard()
            )

    @dispatcher.callback_query(F.data == "channel:add")
    async def add_channel_callback(callback: CallbackQuery) -> None:
        await callback.answer()
        if callback.message is None:
            return
        if callback.message.chat.type != "private":
            await callback.message.answer(
                "Please connect a channel from your private chat with TechPulse."
            )
            return
        await callback.message.answer(
            "📣 <b>Connect your channel</b>\n\n"
            "Select a channel you manage. Telegram will ask you to grant TechPulse "
            "permission to post there.\n\n"
            "<i>Nothing will be published until you choose “Publish to my channel.”</i>",
            parse_mode="HTML",
            reply_markup=channel_picker_keyboard(),
        )

    @dispatcher.callback_query(F.data == "channel:manage")
    async def channel_manage_callback(callback: CallbackQuery) -> None:
        if callback.message is None or callback.message.chat.type != "private":
            await callback.answer(
                "Manage your channel in a private chat with TechPulse.",
                show_alert=True,
            )
            return
        try:
            destination = repository.get_channel(callback.from_user.id)
        except sqlite3.Error:
            logger.exception("Could not load the saved channel")
            await callback.answer("Could not load your channel settings.", show_alert=True)
            return

        await callback.answer()
        if destination is None:
            text = (
                "📣 <b>No channel connected yet</b>\n\n"
                "Connect a channel you manage to publish your selected headlines."
            )
        else:
            username = (
                f"\n@{escape(destination.username)}"
                if destination.username
                else ""
            )
            text = (
                f"📣 <b>Connected channel</b>\n\n"
                f"{escape(destination.title)}{username}\n\n"
                "Publishing is always started manually from a news briefing."
            )
        await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=channel_management_keyboard(
                connected=destination is not None
            ),
        )

    @dispatcher.callback_query(F.data == "channel:disconnect:confirm")
    async def disconnect_confirm_callback(callback: CallbackQuery) -> None:
        if callback.message is None or callback.message.chat.type != "private":
            await callback.answer(
                "Manage your channel in a private chat with TechPulse.",
                show_alert=True,
            )
            return
        await callback.answer()
        await callback.message.answer(
            "Are you sure you want to disconnect this channel? "
            "You can connect it again later.",
            reply_markup=disconnect_confirmation_keyboard(),
        )

    @dispatcher.callback_query(F.data == "channel:disconnect:yes")
    async def disconnect_channel_callback(callback: CallbackQuery) -> None:
        if callback.message is None or callback.message.chat.type != "private":
            await callback.answer(
                "Manage your channel in a private chat with TechPulse.",
                show_alert=True,
            )
            return
        try:
            removed = repository.remove_channel(callback.from_user.id)
        except sqlite3.Error:
            logger.exception("Could not disconnect the saved channel")
            await callback.answer("Could not update your channel settings.", show_alert=True)
            return

        await callback.answer(
            "Channel disconnected." if removed else "No channel was connected."
        )
        await callback.message.edit_text(
            "✅ Channel disconnected. You can connect another channel any time.",
            reply_markup=main_menu_keyboard(),
        )

    @dispatcher.callback_query(F.data.startswith("news:"))
    async def category_callback(callback: CallbackQuery) -> None:
        if callback.message is None or callback.data is None:
            await callback.answer()
            return

        selected = callback.data.removeprefix("news:")
        category = None if selected == "all" else next(
            (
                known_category
                for known_category in NEWS_CATEGORIES
                if known_category == selected
            ),
            None,
        )
        if selected != "all" and category is None:
            await callback.answer("That category is not available.", show_alert=True)
            return

        await callback.answer("Fetching the latest headlines…")
        await show_news(callback.message, repository, category)

    @dispatcher.callback_query(F.data.startswith("page:"))
    async def page_callback(callback: CallbackQuery) -> None:
        if callback.message is None or callback.data is None:
            await callback.answer()
            return
        try:
            _, selected, page_text = callback.data.split(":", maxsplit=2)
            page = int(page_text)
        except ValueError:
            await callback.answer("That page is not available.", show_alert=True)
            return

        category = None if selected == "all" else next(
            (item for item in NEWS_CATEGORIES if item == selected),
            None,
        )
        if (selected != "all" and category is None) or page < 0:
            await callback.answer("That page is not available.", show_alert=True)
            return

        await callback.answer()
        await show_news(
            callback.message,
            repository,
            category,
            page=page,
            refresh=False,
            edit_message=True,
        )

    @dispatcher.callback_query(F.data.startswith("summary:"))
    async def summary_callback(callback: CallbackQuery) -> None:
        if callback.message is None or callback.data is None:
            await callback.answer()
            return
        try:
            _, selected, page_text = callback.data.split(":", maxsplit=2)
            page = int(page_text)
        except ValueError:
            await callback.answer("That briefing is not available.", show_alert=True)
            return

        category = None if selected == "all" else next(
            (item for item in NEWS_CATEGORIES if item == selected),
            None,
        )
        if (selected != "all" and category is None) or page < 0:
            await callback.answer("That briefing is not available.", show_alert=True)
            return

        try:
            articles = repository.get_latest(
                category,
                limit=NEWS_PAGE_SIZE,
                offset=page * NEWS_PAGE_SIZE,
            )
        except sqlite3.Error:
            logger.exception("Could not load articles for AI summarization")
            await callback.answer("Could not load these headlines.", show_alert=True)
            return

        if not articles:
            await callback.answer("There are no headlines to summarize.", show_alert=True)
            return

        model = get_gemini_model()
        cache_key = summary_cache_key(articles, model)
        try:
            cached_json = repository.get_cached_summary(cache_key)
        except sqlite3.Error:
            logger.exception("Could not check the Gemini summary cache")
            await callback.answer("Could not load the AI summary cache.", show_alert=True)
            return

        summary = None
        if cached_json is not None:
            try:
                summary = NewsSummary.model_validate_json(cached_json)
            except ValueError:
                logger.warning("Ignoring invalid cached Gemini summary")

        if summary is None and get_gemini_api_key() is None:
            await callback.answer(
                "Add GEMINI_API_KEY to .env and restart TechPulse to enable AI summaries.",
                show_alert=True,
            )
            return

        await callback.answer("Preparing your AI briefing…")
        progress_message = await callback.message.answer(
            "🧠 <b>Gemini is organizing this page of headlines…</b>",
            parse_mode="HTML",
        )
        cache_warning = False
        if summary is None:
            api_key = get_gemini_api_key()
            if api_key is None:
                await progress_message.edit_text(
                    "Gemini API key is missing. Add GEMINI_API_KEY to .env "
                    "and restart TechPulse."
                )
                return
            try:
                summary = await summarize_articles(
                    articles,
                    api_key=api_key,
                    model=model,
                )
            except SummaryUnavailableError:
                logger.exception("Gemini could not summarize the selected headlines")
                await progress_message.edit_text(
                    "Gemini could not generate a usable summary this time. "
                    "Your original headlines are still available above; please retry later."
                )
                return

            try:
                repository.save_cached_summary(
                    cache_key,
                    summary.model_dump_json(),
                )
            except sqlite3.Error:
                logger.exception("Could not cache the Gemini summary")
                cache_warning = True

        response = format_ai_summary(
            summary,
            articles,
            category,
            page=page,
            page_size=NEWS_PAGE_SIZE,
        )
        if cache_warning:
            response += "\n\n<i>Summary generated; local caching is unavailable.</i>"
        await progress_message.edit_text(
            response,
            parse_mode="HTML",
            reply_markup=summary_actions_keyboard(category, page=page),
            link_preview_options={"is_disabled": True},
        )

    @dispatcher.callback_query(F.data.startswith("publish:"))
    async def publish_callback(callback: CallbackQuery, bot: Bot) -> None:
        if callback.message is None or callback.message.chat.type != "private":
            await callback.answer(
                "Publish to your channel from a private chat with TechPulse.",
                show_alert=True,
            )
            return
        user = callback.from_user
        try:
            _, selected, page_text = (callback.data or "").split(":", maxsplit=2)
            page = int(page_text)
        except ValueError:
            await callback.answer("That news briefing is not available.", show_alert=True)
            return
        category = None if selected == "all" else next(
            (item for item in NEWS_CATEGORIES if item == selected),
            None,
        )
        if (selected != "all" and category is None) or page < 0:
            await callback.answer("That category is not available.", show_alert=True)
            return
        try:
            destination = repository.get_channel(user.id)
            articles = repository.get_latest(
                category,
                limit=NEWS_PAGE_SIZE,
                offset=page * NEWS_PAGE_SIZE,
            )
        except sqlite3.Error:
            logger.exception("Could not load channel or articles for publishing")
            await callback.answer("Could not load your channel or news.", show_alert=True)
            return

        if destination is None:
            await callback.answer("Add a channel first using ➕ Add Channel.", show_alert=True)
            return
        if not articles:
            await callback.answer("There are no headlines to publish yet.", show_alert=True)
            return

        await callback.answer("Publishing your headlines…")
        try:
            await bot.send_message(
                destination.chat_id,
                format_articles(
                    articles,
                    category,
                    page=page,
                    page_size=NEWS_PAGE_SIZE,
                ),
                parse_mode="HTML",
                link_preview_options={"is_disabled": True},
            )
        except TelegramAPIError:
            logger.exception("Could not publish to channel %s", destination.chat_id)
            if callback.message:
                await callback.message.answer(
                    "I couldn't post to that channel. Check that TechPulse is still "
                    "an administrator with permission to post, then reconnect it."
                )
            return

        if callback.message:
            await callback.message.answer(
                f"✅ Published {len(articles)} headlines to "
                f"<b>{escape(destination.title)}</b>.",
                parse_mode="HTML",
            )

    @dispatcher.message(Command("about"))
    async def about_handler(message: Message) -> None:
        await message.answer(
            f"✨ <b>{APP_NAME} {APP_VERSION}</b>\n"
            "Your personal technology-news briefing, collected from trusted "
            "RSS and Atom feeds.",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )

    @dispatcher.message(Command("status"))
    async def status_handler(message: Message) -> None:
        await message.answer(
            f"✅ <b>{APP_NAME} is online</b>\n"
            f"Monitoring {len(FEEDS)} news feeds.",
            parse_mode="HTML",
        )

    return dispatcher


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    token = get_bot_token()
    if token is None:
        raise SystemExit("BOT_TOKEN is missing. Add it to your .env file.")

    repository = ArticleRepository(DATABASE_PATH)
    repository.initialize()
    dispatcher = create_dispatcher(repository)

    async with Bot(token=token) as bot:
        await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
