# 🎯 Self Bot v3.0 - Session Management Guide

## 📋 **OVERVIEW**

The Self Bot v3.0 uses a session management system to track trading activities, prevent duplicate sessions, and maintain data integrity. This guide explains how to manage sessions effectively for daily trading operations.

---

## 🔧 **SESSION SYSTEM ARCHITECTURE**

### **Session Files:**
- `data/active_session.json` - Currently active session data
- `data/session_recovery.json` - Recovery data for interrupted sessions
- `data/sessions.json` - Historical session records
- `data/session_data.json` - Current session trading data

### **Session Limits:**
- **Daily Limit**: 1 session per day (configurable)
- **Concurrent Limit**: 1 active session at a time
- **Recovery**: Automatic recovery from interruptions

---

## 🚀 **QUICK SESSION COMMANDS**

### **1. Start New Session**
```bash
# Start with auto-generated session name
python session_control.py --start

# Start with custom session name
python session_control.py --start --name "morning_session"
python session_control.py --start --name "evening_session"
```

### **2. Stop Current Session**
```bash
# Stop and save current session
python session_control.py --stop

# Force stop (emergency)
python session_control.py --force-stop
```

### **3. List Sessions**
```bash
# List all sessions
python session_control.py --list

# List today's sessions
python session_control.py --list --today
```

### **4. Clear Sessions**
```bash
# Clear all session data (fresh start)
python session_control.py --clear-all

# Clear only today's sessions
python session_control.py --clear-today

# Clear specific session
python session_control.py --clear --name "session_name"
```

### **5. Session Status**
```bash
# Check current session status
python session_control.py --status
```

---

## 📅 **DAILY TRADING WORKFLOW**

### **Morning Session Setup:**
```bash
# 1. Clear previous sessions (if needed)
python session_control.py --clear-today

# 2. Start morning session
python session_control.py --start --name "morning_session"

# 3. Run the bot
python self_bot_v3_integrated.py --verbose

# 4. Stop session when done
python session_control.py --stop
```

### **Evening Session Setup:**
```bash
# 1. Start evening session
python session_control.py --start --name "evening_session"

# 2. Run the bot
python self_bot_v3_integrated.py --verbose

# 3. Stop session when done
python session_control.py --stop
```

---

## 🛠️ **TROUBLESHOOTING**

### **Problem: "Active session already exists"**
**Solution:**
```bash
# Check what session is active
python session_control.py --status

# Stop the active session
python session_control.py --stop

# Or force clear if needed
python session_control.py --clear-all
```

### **Problem: "Daily session limit reached"**
**Solution:**
```bash
# Clear today's sessions
python session_control.py --clear-today

# Or modify daily limit in config
python session_control.py --set-limit 3
```

### **Problem: Session recovery issues**
**Solution:**
```bash
# Clear recovery data
python session_control.py --clear-recovery

# Fresh start
python session_control.py --clear-all
```

### **Problem: Bot won't start due to session conflicts**
**Emergency Solution:**
```bash
# Nuclear option - clear everything
python session_control.py --nuclear-reset

# This clears ALL session data and starts fresh
```

---

## ⚙️ **CONFIGURATION OPTIONS**

### **Modify Session Limits:**
```bash
# Set daily session limit
python session_control.py --set-limit 5

# Disable session limits (unlimited)
python session_control.py --set-limit 0

# Reset to default (1 per day)
python session_control.py --reset-limits
```

### **Session Naming Patterns:**
- **Auto-generated**: `session_YYYYMMDD_HHMMSS`
- **Custom**: Any name you specify
- **Recommended**: `morning_session`, `evening_session`, `test_session`

---

## 📊 **SESSION DATA TRACKING**

Each session tracks:
- **Start/End Times**
- **Trade Count & Results**
- **Profit/Loss**
- **Signal Processing Stats**
- **Error Counts**
- **Balance Changes**

### **View Session Report:**
```bash
# Current session report
python session_control.py --report

# Specific session report
python session_control.py --report --name "morning_session"

# Daily summary
python session_control.py --daily-report
```

---

## 🔄 **FRESH SSID INTEGRATION**

When you get a fresh SSID:

### **1. Update SSID:**
```bash
# Update config with new SSID
python session_control.py --update-ssid "your_new_ssid_here"
```

### **2. Test Connection:**
```bash
# Test new SSID
python test_ssid_fixed.py
```

### **3. Start Fresh Session:**
```bash
# Clear old sessions and start fresh
python session_control.py --clear-all
python session_control.py --start --name "fresh_ssid_test"
python self_bot_v3_integrated.py --verbose
```

---

## 🎯 **BEST PRACTICES**

### **Daily Routine:**
1. **Morning**: Clear yesterday's sessions, start morning session
2. **Trading**: Run bot with verbose logging
3. **Break**: Stop session, review reports
4. **Evening**: Start evening session, run bot
5. **End**: Stop session, backup important data

### **Session Naming:**
- Use descriptive names: `morning_session`, `evening_session`
- Include date for important sessions: `2025_05_30_morning`
- Use test names for testing: `test_new_ssid`, `debug_session`

### **Maintenance:**
- **Weekly**: Clear old session data
- **Monthly**: Backup session reports
- **After Issues**: Use nuclear reset and start fresh

---

## 🚨 **EMERGENCY PROCEDURES**

### **Bot Stuck/Won't Start:**
```bash
# Step 1: Check status
python session_control.py --status

# Step 2: Force stop
python session_control.py --force-stop

# Step 3: Clear all data
python session_control.py --nuclear-reset

# Step 4: Test SSID
python test_ssid_fixed.py

# Step 5: Start fresh
python session_control.py --start
python self_bot_v3_integrated.py --verbose
```

### **Connection Issues:**
```bash
# Clear sessions and test
python session_control.py --clear-all
python test_ssid_fixed.py

# If SSID works, start fresh session
python session_control.py --start --name "connection_test"
```

---

## 📈 **MONITORING & LOGGING**

### **Real-time Monitoring:**
```bash
# Monitor active session
python session_control.py --monitor

# Watch session logs
python session_control.py --tail-logs
```

### **Performance Tracking:**
```bash
# Session performance
python session_control.py --performance

# Compare sessions
python session_control.py --compare morning_session evening_session
```

---

## 🎉 **CONCLUSION**

This session management system provides:
- **Full Control**: Start/stop sessions as needed
- **Flexibility**: Named sessions for different purposes
- **Safety**: Prevents conflicts and data loss
- **Monitoring**: Complete tracking and reporting
- **Recovery**: Automatic recovery from interruptions

**For daily trading, simply use:**
1. `python session_control.py --clear-today` (if needed)
2. `python session_control.py --start --name "your_session"`
3. `python self_bot_v3_integrated.py --verbose`
4. `python session_control.py --stop` (when done)

This gives you complete control over your trading sessions without the frustration of session conflicts!
