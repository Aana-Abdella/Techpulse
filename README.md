# TechPulse

TechPulse is a Telegram bot that collects technology headlines from RSS and
Atom feeds. It filters headlines into configured categories and stores them in
a local SQLite database so the same URL is not saved repeatedly.

## Requirements

- Python 3.10 or newer
- A Telegram bot token from BotFather

## Run locally

1. Install the dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

2. Create `.env` from `.env.example` and set your token:

   ```text
   BOT_TOKEN=your_telegram_bot_token
   ```

3. Start the bot:

   ```bash
   python main.py
   ```

The SQLite database is created automatically at `data/techpulse.db`. The
database and `.env` file are excluded from Git.

## Telegram commands

- `/start` — welcome message
- `/help` — usage and channel setup
- `/news` — fetch and show the latest headlines across all tech categories
- `/news <category>` — show headlines for AI, Software, Cybersecurity, Linux,
  Startups, or Technology
- **✨ AI Summary** — generate a detailed Gemini briefing for the current page
- `/categories` — list supported categories
- `/addchannel` — connect a channel where TechPulse can publish
- `/mychannel` — view, change, or disconnect your channel
- `/cancel` — cancel channel selection
- `/about` — application details
- `/status` — bot and feed status

The start screen has buttons for all headlines, each news category, channel
setup, channel management, and help. Headline briefings use a compact,
clickable layout with page navigation. Moving between pages uses saved
articles without fetching every feed again.

Choose a channel you manage; Telegram will ask to grant the bot administrator
permission to post. Channel selection is saved per Telegram user. Use
`/mychannel` to view, change, or disconnect your channel. TechPulse only
publishes when you explicitly tap **Publish to my channel** on a headline
message.

## Gemini AI summaries

1. Create a Gemini API key in [Google AI Studio](https://aistudio.google.com/apikey).
2. Add it to your local `.env` file:

   ```text
   GEMINI_API_KEY=your_gemini_api_key
   GEMINI_MODEL=gemini-flash-latest
   ```

3. Restart TechPulse and choose a news category. Tap **✨ AI Summary** to
   generate an overview, summaries grouped by category, key takeaways, and
   clickable source headlines.

Summaries are opt-in: the Gemini API is called only when you tap the AI
summary button. TechPulse sends Gemini the public article title, category, and
source name (not the Telegram user, channel, or article URL). Gemini receives
headline metadata only, so summaries may be incomplete; open the source
headlines for full reporting. Each uncached summary uses your Gemini API quota
and may incur charges under your Google AI Studio plan. Successful summaries
are cached locally by article page and model to avoid repeat API calls.
Without a configured key, regular news collection and publishing continue to
work.

The news command fetches the configured feeds concurrently, saves articles from
all categories, and rotates categories in the all-news list so it is not
dominated by one topic. The general Technology category includes feeds from The
Verge, Wired, and Ars Technica. Feed failures are reported while successful
feeds continue to be used. Feed URLs and their categories are configured in
`config.py`.

## Tests

Run the test suite without making network requests:

```bash
python -m unittest discover -s tests -v
```
