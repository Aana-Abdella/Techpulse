# 05 — Your First Telegram Bot

## D — Define

Our first goal is to create a Telegram bot that responds when a user sends `/start`.

The basic communication flow is:

```text
User
  ↓
Telegram
  ↓
Telegram Bot API
  ↓
aiogram
  ↓
Python Application
  ↓
Handler
  ↓
Telegram Bot API
  ↓
Telegram
  ↓
User
```

The bot will respond with:

```text
👋 Welcome to TechPulse!

Your source for software engineering
and digital technology news. 🚀
```

---

# L — Learn

## 1. Dispatcher

```python
dp = Dispatcher()
```

The `Dispatcher` receives updates from Telegram and finds the appropriate handler for each update.

Think of it as a traffic controller:

```text
Telegram Updates
       ↓
   Dispatcher
       ↓
 ┌─────┼─────┐
 ↓     ↓     ↓
/start /help /news
```

---

## 2. Handler

A handler is a function that responds to a particular event.

Example:

```python
@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer("Welcome!")
```

This tells aiogram:

> When a user sends `/start`, execute `start_handler()`.

---

## 3. `async def`

```python
async def start_handler(message: Message):
```

`async def` defines an asynchronous function.

Telegram bots communicate with external systems over the network. Asynchronous programming allows our application to handle waiting/network operations efficiently.

We will study asynchronous programming more deeply later.

---

## 4. `await`

```python
await message.answer("Welcome!")
```

`await` tells Python to wait for an asynchronous operation to complete without blocking the entire asynchronous application.

Here, the operation is sending a message through Telegram.

---

## 5. `start_polling()`

```python
await dp.start_polling(bot)
```

Polling means our bot continuously checks Telegram for new updates.

Conceptually:

```text
Check Telegram
      ↓
New update?
   ↙     ↘
 Yes      No
 ↓         ↓
Handle    Check again
 ↓
Check again
```

As long as the program is running, the bot can receive updates.

---

# Complete Code

```python
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import BOT_TOKEN


dp = Dispatcher()


@dp.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "👋 Welcome to TechPulse!\n\n"
        "Your source for software engineering "
        "and digital technology news. 🚀"
    )


async def main():
    bot = Bot(token=BOT_TOKEN)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
```

---

# Understanding the Program

The program starts here:

```python
if __name__ == "__main__":
    asyncio.run(main())
```

That starts our asynchronous `main()` function.

Inside `main()`:

```python
bot = Bot(token=BOT_TOKEN)
```

creates the Telegram bot using our BotFather token.

Then:

```python
await dp.start_polling(bot)
```

starts listening for Telegram updates.

When `/start` arrives:

```text
Telegram
   ↓
Dispatcher
   ↓
CommandStart()
   ↓
start_handler()
   ↓
message.answer()
   ↓
Telegram
```

---

# T — Try

## Task 1

Run:

```bash
python main.py
```

Keep the terminal running.

Then open your Telegram bot and send:

```text
/start
```

Expected response:

```text
👋 Welcome to TechPulse!

Your source for software engineering
and digital technology news. 🚀
```

---

## Task 2

Change the response.

For example:

```python
await message.answer(
    "🚀 Welcome to TechPulse!\n\n"
    "Daily software engineering and technology news."
)
```

Run the bot again and test `/start`.

---

## Task 3

Try changing the command response yourself without copying my code.

---

# R — Review

Answer these questions without looking at the explanation above.

### 1.

What is the purpose of:

```python
dp = Dispatcher()
```

### 2.

What does this do?

```python
@dp.message(CommandStart())
```

### 3.

What is `message`?

```python
async def start_handler(message: Message):
```

### 4.

What does this do?

```python
await message.answer("Hello")
```

### 5.

Why do we use:

```python
await dp.start_polling(bot)
```

### 6.

Explain the complete journey of `/start`:

```text
User → ? → ? → ? → Bot response
```

---

# Key Concepts

After this lesson, you should understand:

* Telegram Bot
* Telegram Bot API
* aiogram
* Dispatcher
* Handler
* `/start` command
* `async def`
* `await`
* Polling
* Message
* Bot token
* Environment variables

---

# Project Progress

```text
PART 1 — Telegram Bot Foundation

[✅] 01. Architecture
[✅] 02. BotFather
[✅] 03. Project setup
[✅] 04. Environment configuration
[✅] 05. First Telegram bot
[ ] 06. Commands & handlers
[ ] 07. Keyboards
[ ] 08. Error handling
[ ] 09. Logging
[ ] 10. TechPulse Bot v1
```

## Rule

Don't memorize the code.

Understand the flow:

```text
EVENT
  ↓
DISPATCHER
  ↓
HANDLER
  ↓
LOGIC
  ↓
RESPONSE
```

This pattern will become the foundation for the larger TechPulse system.
