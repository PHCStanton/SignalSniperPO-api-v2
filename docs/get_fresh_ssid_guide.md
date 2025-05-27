# Guide to Obtaining a Fresh SSID from Pocket Option

This guide provides detailed instructions on how to extract a valid SSID from your Pocket Option account, which is required for the trading bot to authenticate and execute trades.

## Why You Need a Fresh SSID

The SSID (Session ID) is a temporary authentication token that Pocket Option uses to maintain your login session. These tokens typically expire after a certain period (usually a few hours to a few days), which is why previously saved SSIDs may no longer work.

## Important Update: WebSocket SSID Format

**Note:** The PocketOptionAPI-v2 library requires the SSID in WebSocket message format, not the cookie format. The correct format looks like:

```
42["auth",{"session":"your_session_string_here","isDemo":1,"uid":12345678,"platform":2}]
```

We've created a new tool `extract_websocket_ssid.py` to help you extract the SSID in the correct format.

## Step-by-Step Instructions

### Method 1: Using the WebSocket SSID Extractor (Recommended)

1. **Open your web browser** (Chrome, Firefox, Edge, etc.)

2. **Navigate to Pocket Option**: Go to https://pocketoption.com/en/login/ or https://po.trade/

3. **Log in to your account** using your email/username and password

4. **Open Developer Tools**:
   - In Chrome: Press F12 or right-click anywhere on the page and select "Inspect"
   - In Firefox: Press F12 or right-click and select "Inspect Element"
   - In Edge: Press F12 or right-click and select "Inspect"

5. **Navigate to the Network tab**:
   - Click on the "Network" tab in the developer tools
   - Filter for "WS" to show only WebSocket connections

6. **Find the WebSocket connection**:
   - Look for a connection to "socket.io" or similar
   - Click on it to see the messages

7. **Find the authentication message**:
   - In the messages list, look for a message that starts with `42["auth",` or contains "session"
   - This message is sent when you first connect and contains your authentication details

8. **Copy the entire message**:
   - Select and copy the complete message including the `42["auth",` prefix

9. **Run the WebSocket SSID Extractor**:
   ```bash
   python extract_websocket_ssid.py
   ```

10. **Paste the WebSocket message** when prompted

11. **Follow the prompts** to save the SSID to a file and/or update your configuration

### Method 2: Manual WebSocket Message Extraction

If you prefer to manually extract the SSID:

1. Follow steps 1-8 from Method 1 to find and copy the WebSocket authentication message

2. Make sure the message is in the correct format:
   ```
   42["auth",{"session":"your_session_string_here","isDemo":1,"uid":12345678,"platform":2}]
   ```

3. Update your `config/pocket_option_config.json` file with this SSID

4. Test the SSID using the `test_ssid_direct.py` script:
   ```bash
   python test_ssid_direct.py
   ```

### Method 3: Using Browser Cookies (Not Recommended)

**Note:** This method is no longer recommended as the cookie SSID format is different from the WebSocket SSID format required by the API.

1. **Open Developer Tools** and navigate to the Application/Storage tab

2. **Find the Cookies section** for pocketoption.com

3. **Find the SSID cookie** and copy its value

4. **Convert the cookie SSID to WebSocket format** using the WebSocket SSID Extractor:
   ```bash
   python extract_websocket_ssid.py --message "your_cookie_ssid_here"
   ```

## Important Notes

1. **SSID Expiration**: The SSID will eventually expire, typically within a few hours to a few days. If the bot stops working, you may need to obtain a fresh SSID.

2. **Security**: The SSID provides full access to your Pocket Option account. Keep it secure and never share it with unauthorized individuals.

3. **Multiple Devices**: Logging in from multiple devices or browsers may invalidate previous SSIDs.

4. **Demo vs. Real Account**: Make sure you're logged into the correct account type (demo or real) when extracting the SSID, depending on which one you want the bot to use.

## Troubleshooting

If you're having trouble obtaining a valid SSID:

1. **Clear browser cookies** and log in again to get a fresh session

2. **Try a different browser** if you're experiencing issues with your current one

3. **Ensure you're fully logged in** - you should see your account dashboard, not just the login page

4. **Check for special characters** in the SSID - if present, make sure they're properly copied

5. **Verify your account status** - ensure your Pocket Option account is active and not locked or restricted

## Next Steps

Once you have a valid SSID:

1. Update the `config/pocket_option_config.json` file with your new SSID

2. Run the bot in test mode first to verify it can connect and execute trades

3. Monitor the bot's performance closely when first switching to real trading mode
