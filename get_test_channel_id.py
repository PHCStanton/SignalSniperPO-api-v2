import asyncio
from telethon import TelegramClient
import json

async def get_channel_id():
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
        # Get the test channel
        test_channel = await client.get_entity("🎯Signal_Sniper_Test_Channel🎯")
        print(f"Test Channel ID: {test_channel.id}")
        print(f"Test Channel Title: {test_channel.title}")
        
        # Also get the original channel for reference
        original_channel = await client.get_entity("BINARY TRADING CLUB")
        print(f"Original Channel ID: {original_channel.id}")
        print(f"Original Channel Title: {original_channel.title}")
        
        return test_channel.id
        
    except Exception as e:
        print(f"Error getting channel: {e}")
        return None
    finally:
        await client.disconnect()

if __name__ == "__main__":
    channel_id = asyncio.run(get_channel_id())
