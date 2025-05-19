# Guide to Obtaining a Fresh SSID from Pocket Option

This guide provides detailed instructions on how to extract a valid SSID from your Pocket Option account, which is required for the trading bot to authenticate and execute trades.

## Why You Need a Fresh SSID

The SSID (Session ID) is a temporary authentication token that Pocket Option uses to maintain your login session. These tokens typically expire after a certain period (usually a few hours to a few days), which is why previously saved SSIDs may no longer work.

## Step-by-Step Instructions

### Method 1: Using Browser Developer Tools (Recommended)

1. **Open your web browser** (Chrome, Firefox, Edge, etc.)

2. **Navigate to Pocket Option**: Go to https://pocketoption.com/en/login/

3. **Log in to your account** using your email/username and password

4. **Open Developer Tools**:
   - In Chrome: Press F12 or right-click anywhere on the page and select "Inspect"
   - In Firefox: Press F12 or right-click and select "Inspect Element"
   - In Edge: Press F12 or right-click and select "Inspect"

5. **Navigate to the Application/Storage tab**:
   - In Chrome: Click on the "Application" tab in the developer tools
   - In Firefox: Click on the "Storage" tab
   - In Edge: Click on the "Application" tab

6. **Find the Cookies section**:
   - In Chrome: Expand "Cookies" in the left sidebar, then click on "https://pocketoption.com"
   - In Firefox: Expand "Cookies" and click on "pocketoption.com"
   - In Edge: Expand "Cookies" and click on "https://pocketoption.com"

7. **Find the SSID cookie**:
   - Look for a cookie named "ssid" in the list
   - The value will be a string like "A9B0cjxtNGQ1fFmxL"

8. **Copy the SSID value**:
   - Double-click on the value to select it
   - Right-click and select "Copy" or press Ctrl+C

9. **Test the SSID**:
   - Run the `test_ssid_direct.py` script
   - Paste the copied SSID when prompted
   - Select "n" when asked if using a demo account (unless you are using a demo account)

### Method 2: Using Browser Extensions

If you find the developer tools method difficult, you can use a cookie manager extension:

1. **Install a cookie manager extension**:
   - For Chrome: "EditThisCookie" or "Cookie-Editor"
   - For Firefox: "Cookie Quick Manager" or "Cookie-Editor"
   - For Edge: "Cookie-Editor"

2. **Navigate to Pocket Option**: Go to https://pocketoption.com and log in

3. **Open the cookie manager extension**:
   - Click on the extension icon in your browser toolbar

4. **Find and copy the SSID cookie**:
   - Look for the "ssid" cookie
   - Copy its value

5. **Test the SSID** using the `test_ssid_direct.py` script

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
