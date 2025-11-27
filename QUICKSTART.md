# Bybit Volume Scanner - Quick Reference

## 🚀 Quick Start

```bash
# Start web interface (easiest)
./start_web.sh

# Or start manually
python web_app.py

# Then open: http://localhost:5000
```

## 📋 Files Overview

- **`web_app.py`** - Web interface (Flask app)
- **`main.py`** - Core scanner logic & CLI version
- **`templates/index.html`** - Web dashboard UI
- **`volume_data.json`** - Historical volume data (auto-generated)
- **`requirements.txt`** - Python dependencies
- **`start_web.sh`** - Quick startup script

## 🎯 Common Tasks

### Change Settings via Web UI

1. Open http://localhost:5000
2. Adjust values in Configuration panel
3. Click "Start" to apply

### Change Settings via CLI

Edit `main.py`, lines near bottom:

```python
CATEGORY = "spot"  # spot, linear, or inverse
TIMEFRAME_HOURS = 24  # hours to look back
VOLUME_INCREASE_THRESHOLD = 30.0  # minimum % increase
CHECK_INTERVAL_SECONDS = 300  # seconds between scans
```

### Reset All Data

**Web UI:** Click "Reset Data" button

**CLI:** Delete `volume_data.json` file

### View Alerts

**Web UI:** Scroll to "Volume Spike Alerts" section

**CLI:** Alerts print to console in real-time

## 🔧 Troubleshooting

### Port 5000 already in use

Edit `web_app.py`, change last line:

```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Use 5001 instead
```

### Scanner not finding any symbols

- Check your internet connection
- Try a different category (spot, linear, inverse)
- Bybit API might be temporarily unavailable

### No alerts appearing

- First run builds baseline (no alerts)
- Lower the threshold percentage
- Wait for actual volume spikes to occur
- Check if scanner is running (status indicator)

### Web page not updating

- Check browser console for errors (F12)
- Refresh the page
- Restart the web app

## 📊 Understanding the Data

### Volume Change Calculation

```
% Change = ((Current Volume - Average Volume) / Average Volume) × 100
```

### Alert Triggers

Alert fires when: `Current Volume Change >= Threshold`

Example: 30% threshold = alert when volume is 30% higher than average

### Data Storage

- One record per scan per symbol
- Automatically pruned to timeframe + 20%
- Stored in JSON format for easy inspection

## 🎨 Customization Ideas

### Add Email Notifications

Edit `web_app.py`, in `run_scanner_loop()`:

```python
for alert in alerts:
    send_email_alert(alert)  # Your email function
```

### Add Discord/Telegram Webhooks

```python
import requests

def send_webhook(alert):
    webhook_url = "YOUR_WEBHOOK_URL"
    requests.post(webhook_url, json={
        'content': f"🚨 {alert['symbol']}: +{alert['volume_change_pct']:.2f}%"
    })
```

### Change Refresh Rate

Edit `templates/index.html`, find:

```javascript
refreshInterval = setInterval(() => {
  // ...
}, 3000); // Change 3000 to desired milliseconds
```

### Add More Statistics

Edit `templates/index.html` to add cards/charts

Use Chart.js or similar for visualizations

## 📱 Mobile Access

The web interface is responsive and works on mobile devices.

To access from other devices on your network:

1. Find your computer's IP address
2. Access: `http://YOUR_IP:5000`
3. Make sure firewall allows port 5000

## 🔒 Security Notes

- Web interface has no authentication
- Only bind to localhost in production: `host='127.0.0.1'`
- Add authentication if exposing publicly
- API endpoints have no rate limiting

## 💡 Tips

- Start with higher threshold (50%) to test
- Spot markets usually more active than futures
- Lower timeframe = more sensitive to spikes
- Check interval affects API usage (be respectful)
- Keep browser tab open for live updates
- Volume spikes often precede price moves
