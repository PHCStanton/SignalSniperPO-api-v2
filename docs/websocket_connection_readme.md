# Pocket Option WebSocket Connection Test

This set of tools allows you to connect to Pocket Option's WebSocket API using your SSID cookie, authenticate as a real user, and receive the full session object.

## What These Scripts Do

1. ✅ Connect to Pocket Option's WebSocket server
2. ✅ Authenticate using your SSID cookie
3. ✅ Receive and save the full session object
4. ✅ Extract and save the session string for potential reuse

## Prerequisites

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Or install the specific package:

```bash
pip install websocket-client
```

## How to Use

### Option 1: Simple Script (po_ws_auth_test.py)

1. Open `po_ws_auth_test.py` in a text editor
2. Replace `YOUR_ACTUAL_SSID_HERE` with your Pocket Option SSID cookie value
3. Run the script:

```bash
python po_ws_auth_test.py
```

### Option 2: Command-Line Tool (test_websocket_connection.py)

This is a more user-friendly script with command-line arguments:

```bash
# Provide SSID as a command-line argument
python test_websocket_connection.py --ssid YOUR_ACTUAL_SSID_HERE

# Or run without arguments and enter SSID when prompted
python test_websocket_connection.py
```

## How to Get Your SSID

1. Log out of all Pocket Option related sites (pocketoption.com, po.trade, etc.)
2. Clear your browser cookies (or use incognito/private browsing)
3. Go directly to po.trade and log in with your credentials
4. Open Developer Tools (F12 or right-click > Inspect)
5. Go to the Application tab (Chrome) or Storage tab (Firefox)
6. Look for Cookies > po.trade
7. Find the SSID cookie and copy its value

For detailed instructions, refer to the `get_fresh_ssid_guide.md` file.

## Understanding the Output

When the script runs successfully, you'll see:

1. Connection confirmation
2. Authentication message
3. Session payload with details like:
   - Session string (can be used for temporary authentication)
   - User ID
   - Platform information

The script will save:
- Complete session data to `po_session_data.json`
- Session string to `po_session_string.txt`

## Important Notes

- The SSID is a browser cookie, not part of the WebSocket payload
- It's used during the handshake but not returned in the response
- You can only retrieve the SSID from your browser cookies
- The session string received can be used for temporary authentication (it expires with the SSID)
- If you have a valid SSID, the script will offer to update your config file

## Troubleshooting

- If you see connection errors, make sure your SSID is valid and not expired
- SSIDs typically expire after a few hours to a few days
- If authentication fails, get a fresh SSID from your browser
- Make sure you're connected to the internet and can access po.trade
