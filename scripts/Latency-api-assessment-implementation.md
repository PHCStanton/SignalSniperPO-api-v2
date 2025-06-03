Based on my analysis of the scripts in this directory, here's what you need to achieve successful latency checks to Pocket Option:

## **Prerequisites Required:**

### 1. **Node.js and npm**
- Must have Node.js installed on your system
- npm comes with Node.js and is needed for package management
- Download from: https://nodejs.org/

### 2. **Socket.io-client package**
- Required for WebSocket connection testing
- Install by running: `.\setup-dependencies.ps1` or `npm install socket.io-client`

### 3. **Python (for official API testing)**
- Python 3.x installation
- PocketOption API v2 package installed (`pip install -e .` in the PocketOptionAPI-v2 directory)

### 4. **Authentication Credentials**
- **Session ID**: A 32-character string from your browser session
- **User ID**: Your numeric Pocket Option user ID
- **Demo Mode flag**: Whether to test on demo or real account

## **How to Get Your Credentials:**

1. **Session ID and User ID:**
   - Open Pocket Option in your browser
   - Press F12 to open Developer Tools
   - Go to Network tab
   - Look for Socket.io connections (filter by "socket.io")
   - Find the authentication message containing your session_id and uid
   - The session_id is typically 32 characters long
   - Example: `2666465456adc00252df90dd2da488d1`

## **Available Tests and What They Measure:**

### 1. **test-pocketoption-live.ps1** (Most Comprehensive)
- Tests real Socket.io connection with authentication
- Measures:
  - Time synchronization latency (critical for trading)
  - Live quotes request/response times
  - Balance check latency
  - Real-time data feed reception
  - Overall trading API performance

### 2. **test-pocketoption-api.ps1** (Python API)
- Uses official PocketOption Python API
- Measures:
  - API connection time
  - Balance retrieval latency
  - Market data (candles) request latency
  - Payout information access speed
  - Trade execution latency (demo mode only)

### 3. **test-socketio-latency.ps1** (Basic Socket.io)
- Tests Socket.io connection without full authentication
- Can run with or without session ID
- Measures basic ping-pong latency

### 4. **test-api-latency.ps1** (HTTP endpoints)
- Tests HTTP API endpoints
- Measures REST API response times
- Tests TCP connection establishment

### 5. **check-system-latency.ps1** (Network diagnostics)
- Basic network connectivity tests
- DNS resolution speed
- General internet latency

## **Performance Benchmarks:**

The scripts classify latency as:
- **🟢 EXCELLENT** (<30ms): Perfect for high-frequency trading
- **🟢 VERY GOOD** (<50ms): Excellent for active trading
- **🟡 GOOD** (<100ms): Suitable for most trading strategies
- **🟡 ACCEPTABLE** (<200ms): May notice slight delays
- **🔴 POOR** (>200ms): May significantly affect trading performance

## **Recommended Testing Sequence:**

1. **First, run setup:**
   ```powershell
   .\setup-dependencies.ps1
   ```

2. **Basic connectivity test:**
   ```powershell
   .\check-system-latency.ps1
   ```

3. **Full trading latency test (requires credentials):**
   ```powershell
   .\test-pocketoption-live.ps1 -SessionId "your_session_id" -UserId "your_user_id" -TestDuration 30
   ```

4. **Python API test (if you have PocketOption API installed):**
   ```powershell
   .\test-pocketoption-api.ps1 -SessionId "your_session_id" -UserId "your_user_id"
   ```

## **Key Success Factors:**

1. **Low average latency** - Ideally under 50ms for active trading
2. **Consistent latency** - Low variance between min and max values
3. **Successful authentication** - Valid session ID and user ID
4. **Stable connection** - No disconnections during testing
5. **All test types passing** - HTTP, WebSocket, and API calls all working

Would you like me to help you run these tests or do you need assistance with getting your session credentials?