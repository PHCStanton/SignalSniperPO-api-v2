# Extracting Your SSID from po.trade

This guide provides detailed instructions on how to extract your SSID cookie from po.trade, which is required for the WebSocket connection scripts.

## Preparation

1. **Log out of all Pocket Option related sites**
   - Visit po.trade and log out if you're currently logged in
   - Visit pocketoption.com and log out if you're currently logged in

2. **Clear your browser cookies** (or use incognito/private browsing)
   - This ensures you get a fresh session

## Step-by-Step Instructions

### Step 1: Log in to po.trade

1. Open your web browser
2. Go to [po.trade](https://po.trade)
3. Log in with your Pocket Option credentials

### Step 2: Open Developer Tools

#### Chrome
- Press `F12` or `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Option+I` (Mac)
- Or right-click anywhere on the page and select "Inspect"

#### Firefox
- Press `F12` or `Ctrl+Shift+I` (Windows/Linux) or `Cmd+Option+I` (Mac)
- Or right-click anywhere on the page and select "Inspect Element"

#### Edge
- Press `F12` or `Ctrl+Shift+I`
- Or right-click anywhere on the page and select "Inspect"

#### Safari
- First, enable the Developer menu: Safari > Preferences > Advanced > "Show Develop menu in menu bar"
- Then press `Cmd+Option+I`
- Or select Develop > Show Web Inspector from the menu bar

### Step 3: Navigate to Cookies

#### Chrome
1. Click on the "Application" tab in the Developer Tools
2. In the left sidebar, expand "Cookies" under "Storage"
3. Click on "https://po.trade"

#### Firefox
1. Click on the "Storage" tab in the Developer Tools
2. In the left sidebar, expand "Cookies"
3. Click on "https://po.trade"

#### Edge
1. Click on the "Application" tab in the Developer Tools
2. In the left sidebar, expand "Cookies" under "Storage"
3. Click on "https://po.trade"

#### Safari
1. Click on the "Storage" tab in the Web Inspector
2. Click on "Cookies" in the left sidebar
3. Filter for "po.trade"

### Step 4: Find and Copy the SSID

1. In the list of cookies, look for one named "SSID"
2. The "Value" column contains your SSID
3. Double-click on the value to select it, then right-click and select "Copy" or press `Ctrl+C` (Windows/Linux) or `Cmd+C` (Mac)

![Example of SSID in Chrome DevTools](https://i.imgur.com/example.png)

### Step 5: Use the SSID in the Scripts

1. Open `po_ws_auth_test.py` in a text editor and replace `YOUR_ACTUAL_SSID_HERE` with your copied SSID
   ```python
   SSID = "your_copied_ssid_value_here"
   ```

2. Or use the command-line tool:
   ```bash
   python test_websocket_connection.py --ssid your_copied_ssid_value_here
   ```

## Troubleshooting

### SSID Not Found
- Make sure you're logged in to po.trade
- Try refreshing the page and checking again
- Try logging out and logging back in

### Invalid SSID Error
- SSIDs expire after a period of time (usually a few hours to a few days)
- Get a fresh SSID by logging out and logging back in to po.trade
- Make sure you're copying the entire SSID value without any extra spaces

### Connection Issues
- Ensure you have a stable internet connection
- Check if po.trade is accessible in your browser
- Some networks might block WebSocket connections; try using a different network

## Security Note

The SSID cookie provides full access to your Pocket Option account. Treat it like a password:

- Never share your SSID with anyone
- Don't store it in public or shared repositories
- If you suspect your SSID has been compromised, log out and log back in to get a new one
