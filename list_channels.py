import asyncio
from telethon import TelegramClient
import json

async def list_channels():
    # Load config
    with open('config/telegram_config.json', 'r') as f:
        config = json.load(f)
    
    client = TelegramClient(
        f"sessions/{config['session_name']}", 
        config['api_id'], 
        config['api_hash']
    )
    
    await client.start()
    
    try:
        print("Available channels:")
        async for dialog in client.iter_dialogs():
            if dialog.is_channel:
                print(f"Channel: {dialog.name} | ID: {dialog.id}")
                if "signal" in dialog.name.lower() or "sniper" in dialog.name.lower() or "test" in dialog.name.lower():
                    print(f"  *** POTENTIAL MATCH: {dialog.name} | ID: {dialog.id}")
        
    except Exception as e:
        print(f"Error listing channels: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(list_channels())
