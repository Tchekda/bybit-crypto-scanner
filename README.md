# Bybit Crypto Volume Scanner

A Python-based scanner that monitors all cryptocurrency pairs on Bybit for volume spikes and sends alerts when trading activity exceeds configurable thresholds.

## Features

- 📊 Scans all available crypto pairs on Bybit (Spot, Linear, Inverse)
- 📈 Compares current 24h volume against historical average
- 💾 Stores volume data locally for fast historical analysis
- 🚨 Generates alerts when volume increase exceeds threshold
- ⚙️ Fully configurable parameters (timeframe, threshold, scan interval)
- 🔄 Continuous monitoring with automatic rescans
- ✅ Avoids false positives on first run by building baseline data

## How It Works

The scanner:

1. Fetches all trading pairs from Bybit via the V5 API
2. For each pair, retrieves the current 24-hour volume
3. Stores volume data locally in a JSON file for historical tracking
4. Calculates the average volume from stored historical data
5. Compares current volume to historical average
6. Triggers an alert if the increase exceeds the configured threshold

**Example**: If a crypto normally does 1000 BTC in 24h volume, and suddenly does 1300 BTC, that's a 30% increase - the scanner will alert you.

### First Run Behavior

On the **first run**, the scanner will:

- Collect baseline volume data for all pairs
- Store it in `volume_data.json`
- **NOT trigger any alerts** (avoiding false positives)

On **subsequent runs**, it will:

- Use locally stored historical data for comparisons
- Only fetch new data from the API for current volumes
- Trigger alerts when volume spikes are detected
- Continuously update the local history

## Installation

1. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate.fish  # On fish shell
# or
source venv/bin/activate  # On bash/zsh
# or
venv\Scripts\activate  # On Windows
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Edit the variables in the `main()` function of `main.py`:

```python
CATEGORY = "spot"  # Options: 'spot', 'linear', 'inverse'
TIMEFRAME_HOURS = 24  # Lookback period for average volume
VOLUME_INCREASE_THRESHOLD = 30.0  # Minimum % increase (e.g., 30 = 30%)
CHECK_INTERVAL_SECONDS = 300  # Time between scans (300 = 5 minutes)
```

### Parameters Explained

- **CATEGORY**: Type of trading pairs to monitor

  - `"spot"`: Spot trading pairs (BTC/USDT, ETH/USDT, etc.)
  - `"linear"`: USDT/USDC perpetual contracts
  - `"inverse"`: Inverse perpetual contracts

- **TIMEFRAME_HOURS**: Historical period to compare against (in hours)

  - `24`: Compare to yesterday's average
  - `168`: Compare to last week's average
  - Any positive integer

- **VOLUME_INCREASE_THRESHOLD**: Minimum percentage increase to trigger alert

  - `30.0`: Alert if volume is 30% higher than average
  - `50.0`: Alert if volume is 50% higher than average
  - Any positive number

- **CHECK_INTERVAL_SECONDS**: Time to wait between scans
  - `300`: Scan every 5 minutes
  - `600`: Scan every 10 minutes
  - `60`: Scan every minute

## Usage

### Option 1: Web Interface (Recommended)

**Quick Start:**

```bash
./start_web.sh
```

Or run manually:

```bash
python web_app.py
```

Then open your browser to `http://localhost:5000`

The web interface provides:

- 📊 Real-time dashboard with live status updates
- ⚙️ Easy configuration through the UI
- 🚨 Live alert monitoring with detailed information
- 📈 Tracked symbols table showing volume changes
- 🔄 Start/Stop/Reset controls
- 📱 Responsive design that works on mobile

### Option 2: Docker (Recommended for Production)

**Using Docker Compose:**

```bash
docker-compose up -d
```

**Using Docker directly:**

```bash
# Build the image
docker build -t bybit-scanner .

# Run the container
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  --name bybit-scanner \
  bybit-scanner
```

**Using pre-built image from GitHub Container Registry:**

```bash
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  --name bybit-scanner \
  ghcr.io/tchekda/bybit-crypto-scanner/bybit-scanner:latest
```

Then access the web interface at `http://localhost:5000`

**Docker Benefits:**

- 📦 No need to install Python or dependencies
- 🔄 Easy updates and rollbacks
- 💾 Persistent data via volume mounts
- 🚀 Ready for production deployment
- 🔒 Isolated environment

### Option 3: Command Line

Run the scanner in CLI mode:

```bash
python main.py
```

The scanner will run continuously, checking for volume spikes at the configured interval.

Press `Ctrl+C` to stop the scanner.

## Example Output

```
================================================================================
Bybit Volume Scanner Started
================================================================================
Category:              spot
Timeframe:             24 hours
Volume Threshold:      30.0%
Check Interval:        300 seconds
================================================================================

[2025-11-27 12:00:00] Scanning 542 pairs...

================================================================================
🚨 VOLUME SPIKE ALERT 🚨
================================================================================
Symbol:           BTCUSDT
Current Volume:   25431.50
Average Volume:   18654.23
Volume Increase:  36.32%
Current Price:    45231.50
Price Change 24h: 0.0425
Time:             2025-11-27T12:05:23.123456
================================================================================

✅ Found 1 volume spike(s)!
Waiting 300 seconds until next scan...
```

## Web Interface Features

The web dashboard (`web_app.py`) provides a modern, user-friendly interface:

### Dashboard Overview

- **Scanner Status**: Real-time status indicator showing if scanner is running
- **Live Statistics**: Total alerts, tracked symbols, and last scan time
- **Configuration Panel**: Adjust all parameters without editing code
- **Control Buttons**: Start, Stop, and Reset data with one click

### Alerts Display

- Live updating alerts list (refreshes every 3 seconds)
- Color-coded volume spike indicators
- Detailed information for each alert:
  - Symbol and percentage increase
  - Current vs. average volume
  - Price information and 24h change
  - Timestamp of detection

### Symbols Tracker

- Real-time table of top 20 tracked symbols
- Shows current volume, average volume, and change percentage
- Color-coded positive/negative changes
- Number of data points collected per symbol

### Configuration Options

All parameters can be adjusted through the web UI:

- Market category (Spot, Linear, Inverse)
- Timeframe in hours
- Volume increase threshold percentage
- Check interval in seconds

Changes take effect on the next scan cycle.

## Docker Deployment

### Building the Image

Build locally:

```bash
docker build -t bybit-scanner .
```

### Running with Docker Compose

The easiest way to run the scanner:

```bash
# Start the service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the service
docker-compose down
```

### Running with Docker

```bash
# Run in background
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  --name bybit-scanner \
  --restart unless-stopped \
  bybit-scanner

# View logs
docker logs -f bybit-scanner

# Stop container
docker stop bybit-scanner

# Remove container
docker rm bybit-scanner
```

### Using Pre-built Images

Images are automatically built and published to GitHub Container Registry on every commit to main:

```bash
# Pull the latest image
docker pull ghcr.io/tchekda/bybit-crypto-scanner/bybit-scanner:latest

# Run it
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/data:/app/data \
  --name bybit-scanner \
  ghcr.io/tchekda/bybit-crypto-scanner/bybit-scanner:latest
```

### Docker Volume Persistence

Volume data is stored in the mounted volume (`./data` directory) to persist across container restarts:

```bash
# Create data directory
mkdir -p data

# The container will use /app/data inside, mapped to ./data on host
# Your volume_data.json will be in ./data/volume_data.json
```

### GitHub Actions CI/CD

The project includes a GitHub Actions workflow that:

- ✅ Builds the Docker image on every push
- ✅ Pushes to GitHub Container Registry
- ✅ Supports multi-architecture (amd64, arm64)
- ✅ Tags with version numbers and commit SHA
- ✅ Creates artifact attestations for security

The workflow is triggered on:

- Push to `main` branch
- Pull requests
- Version tags (e.g., `v1.0.0`)
- Manual workflow dispatch

## Extending the Alert System

The current implementation prints alerts to the console. You can extend the `send_alert()` method to:

- 📧 Send email notifications
- 💬 Post to Telegram/Discord/Slack
- 🔔 Trigger webhooks
- 📱 Send push notifications
- 💾 Log to database or file

Example webhook integration:

```python
def send_alert(self, alert: Dict):
    # Console output (existing)
    print(f"Alert: {alert['symbol']} volume up {alert['volume_change_pct']:.2f}%")

    # Webhook notification (new)
    import requests
    requests.post('https://your-webhook-url.com', json=alert)
```

## API Rate Limits

The scanner includes small delays (`time.sleep(0.1)`) to avoid hitting Bybit's rate limits. If you monitor many pairs or use shorter intervals, consider:

- Increasing the delay between API calls
- Implementing more sophisticated rate limiting
- Using Bybit's WebSocket API for real-time data

## Data Storage

The scanner stores volume history in `volume_data.json` with the following structure:

```json
{
  "BTCUSDT": [
    {
      "timestamp": "2025-11-27T13:00:00.123456",
      "volume": 25431.50
    },
    ...
  ],
  "ETHUSDT": [...]
}
```

The file is automatically:

- Created on first run
- Updated after each scan
- Pruned to keep only relevant historical data
- Used for fast volume comparisons

You can delete this file to reset the baseline and start fresh.

## Notes

- The scanner uses Bybit's public API endpoints (no authentication required)
- **First run collects baseline data and does NOT trigger alerts**
- Subsequent runs use local data for fast comparisons
- Historical volume from API is only fetched for new pairs
- Pairs with negligible volume are automatically skipped
- Data is automatically cleaned to prevent file bloat

## License

MIT License - feel free to modify and use as needed.
