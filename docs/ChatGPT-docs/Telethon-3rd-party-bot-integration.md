Since you already have your Telethon client and configuration working (receiving messages, interacting, and parsing logic in place), all that’s left is to **hook the incoming messages** to your parser.

Here’s a **minimal integration blueprint** that connects everything:

---

## ✅ Step-by-Step: Connect Message Listener to Your Parser

Assuming:

* You already have your client in a config file (`client = TelegramClient(...)`)
* You have a function like `parse_bot_message(text)` in your config

---

### 🔧 1. **In Your Main Script or Entry Point**

```python
from telethon import events
from my_config import client, parse_bot_message  # Import your client and logic

# Optional: filter to only bots
@client.on(events.NewMessage(incoming=True))
async def handle_incoming(event):
    sender = await event.get_sender()

    if sender.bot:
        print(f"🤖 Message from bot @{sender.username or sender.id}: {event.text}")
        parse_bot_message(event.text)  # Call your parsing logic

    # Optional: if you want to capture all messages regardless of sender
    # parse_bot_message(event.text)

# Start client
client.start()
client.run_until_disconnected()
```

---

### ✅ 2. **If Your Parser Uses More Context**

If your parser requires message metadata like timestamp or sender:

```python
@client.on(events.NewMessage(incoming=True))
async def handle_incoming(event):
    sender = await event.get_sender()
    if sender.bot:
        message_data = {
            "text": event.text,
            "sender_id": sender.id,
            "username": sender.username,
            "timestamp": event.date,
            "chat_id": event.chat_id,
            "message_id": event.id
        }
        parse_bot_message(message_data)
```

Then your `parse_bot_message()` can look like:

```python
def parse_bot_message(data):
    text = data["text"]
    print(f"🔍 Parsing text: {text}")
    # Your actual logic here
```

---

### ⚠️ Notes:

* `event.text` handles regular messages. For media, buttons, or replies, you may need `.message`, `.raw_text`, `.buttons`, etc.
* You can apply filters like `@client.on(events.NewMessage(from_users='BotUsername'))` to target specific bots.
* If your parser requires dynamic updates (like storing results), you can also pass the whole `event` object and process from there.

