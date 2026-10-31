# import asyncio

# from aiogram import Bot, Dispatcher
# from aiogram.filters import CommandStart ,Command
# from aiogram.types import Message

# from config import BOT_TOKEN


# dp = Dispatcher()


# @dp.message(CommandStart())
# async def start_handler(message: Message):
#     await message.answer(
#         "👋 Welcome to TechPulse!\n\n"
#         "Your source for software engineering "
#         "and digital technology news. 🚀"
#     )

# @dp.message(Command("help"))
# async def help_handler(message: Message):
#     await message.answer(
#         "🆘 Help\n\n"
#         "/start - Start the bot\n"
#         "/news - Latest tech news\n"
#         "/about - About TechPulse\n"
#         "/status - Check bot status"
#     )


# @dp.message(Command("news"))
# async def news_handler(message: Message):
#     await message.answer(
#         "📰 Latest News\n\n"
#         "News collection is coming soon..."
#     )


# @dp.message(Command("about"))
# async def about_handler(message: Message):
#     await message.answer(
#         "🚀 TechPulse\n\n"
#         "Technology and software engineering news "
#         "for developers."
#     )

# @dp.message(Command("status"))
# async def status_handler(message: Message):
#     await message.answer(
#         "TechPulse \n\n"
#         "The system is online and running smoothly. ✅"
#     )

# async def main():
#     bot = Bot(token=BOT_TOKEN)

#     await dp.start_polling(bot)


# if __name__ == "__main__":
#     asyncio.run(main())

# from filters import is_technology_news

# title = "New Python tools for developers"

# if is_technology_news(title):
#     print("This article is relevant.")

news_articles = [
    {
        "title": "Python releases a new developer tool",
        "category": "software",
        "source": "Example Tech",
        "url": "https://example.com/python"
    },
    {
        "title": "New AI model announced",
        "category": "AI",
        "source": "Example AI News",
        "url": "https://example.com/ai"
    },
    {
        "title": "Linux security update released",
        "category": "Linux",
        "source": "Example Linux News",
        "url": "https://example.com/linux"
    }
]


def display_news(articles):
    for article in articles:
        print(f"Title: {article['title']}")
        print(f"Category: {article['category']}")
        print(f"Source: {article['source']}")
        print(f"URL: {article['url']}")
        print("-" * 40)


display_news(news_articles)

def filter_by_category(articles, category):
    filtered_articles = []

    for article in articles :
        if article ["category"].lower() == category.lower():
            filtered_articles.append(article)

    return filtered_articles

ai_articles = filter_by_category(news_articles, "AI")
display_news(ai_articles)