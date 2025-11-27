#!/usr/bin/env python3
"""
Bybit Crypto Volume Scanner
Monitors all crypto pairs on Bybit for volume spikes and sends alerts when thresholds are exceeded.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from pybit.unified_trading import HTTP


class BybitVolumeScanner:
    """Scanner for detecting volume spikes on Bybit cryptocurrency pairs."""
    
    def __init__(self, 
                 category: str = "spot",
                 timeframe_hours: int = 24,
                 volume_increase_threshold: float = 30.0,
                 check_interval_seconds: int = 300,
                 data_file: str = "volume_data.json"):
        """
        Initialize the Bybit Volume Scanner.
        
        Args:
            category: Trading category ('spot', 'linear', 'inverse')
            timeframe_hours: Lookback period in hours to calculate average volume
            volume_increase_threshold: Minimum % increase to trigger alert
            check_interval_seconds: Time between scans in seconds
            data_file: Path to JSON file for storing volume history
        """
        self.session = HTTP(testnet=False)
        self.category = category
        self.timeframe_hours = timeframe_hours
        self.volume_increase_threshold = volume_increase_threshold
        self.check_interval_seconds = check_interval_seconds
        self.data_file = Path(data_file)
        self.volume_history = self._load_volume_history()
        self.first_run = len(self.volume_history) == 0
    
    def _load_volume_history(self) -> Dict:
        """
        Load volume history from local JSON file.
        
        Returns:
            Dictionary mapping symbols to their volume history
        """
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load volume history: {e}")
                return {}
        return {}
    
    def _save_volume_history(self):
        """
        Save volume history to local JSON file.
        """
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.volume_history, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save volume history: {e}")
    
    def _update_volume_record(self, symbol: str, volume: float):
        """
        Update volume history for a symbol.
        
        Args:
            symbol: Trading pair symbol
            volume: Current 24h volume
        """
        timestamp = datetime.now().isoformat()
        
        if symbol not in self.volume_history:
            self.volume_history[symbol] = []
        
        # Add new record
        self.volume_history[symbol].append({
            'timestamp': timestamp,
            'volume': volume
        })
        
        # Keep only records within timeframe + 20% buffer for better calculation
        cutoff_time = datetime.now() - timedelta(hours=int(self.timeframe_hours * 1.2))
        self.volume_history[symbol] = [
            record for record in self.volume_history[symbol]
            if datetime.fromisoformat(record['timestamp']) > cutoff_time
        ]
    
    def _get_average_volume_from_history(self, symbol: str) -> Optional[float]:
        """
        Calculate average volume from locally stored history.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Average volume or None if insufficient data
        """
        if symbol not in self.volume_history or len(self.volume_history[symbol]) < 2:
            return None
        
        # Calculate average from all stored records
        volumes = [record['volume'] for record in self.volume_history[symbol]]
        
        # Need at least 2 data points to calculate meaningful average
        if len(volumes) >= 2:
            # Exclude the most recent reading to avoid comparing current with current
            return sum(volumes[:-1]) / len(volumes[:-1])
        
        return None
        
    def get_all_tickers(self) -> List[Dict]:
        """
        Fetch all tickers for the specified category.
        
        Returns:
            List of ticker dictionaries containing symbol and volume data
        """
        try:
            response = self.session.get_tickers(category=self.category)
            if response['retCode'] == 0:
                return response['result']['list']
            else:
                print(f"Error fetching tickers: {response['retMsg']}")
                return []
        except Exception as e:
            print(f"Exception while fetching tickers: {e}")
            return []
    
    def get_historical_volume(self, symbol: str, hours: int) -> float:
        """
        Calculate average volume over the specified historical period.
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            hours: Number of hours to look back
            
        Returns:
            Average volume over the period, or 0 if data unavailable
        """
        try:
            # Calculate time range
            end_time = int(time.time() * 1000)
            start_time = int((time.time() - hours * 3600) * 1000)
            
            # Get hourly klines for the period
            response = self.session.get_kline(
                category=self.category,
                symbol=symbol,
                interval="60",  # 1 hour intervals
                start=start_time,
                end=end_time,
                limit=1000
            )
            
            if response['retCode'] == 0 and response['result']['list']:
                klines = response['result']['list']
                # kline format: [startTime, open, high, low, close, volume, turnover]
                volumes = [float(kline[5]) for kline in klines if kline[5]]
                
                if volumes:
                    return sum(volumes) / len(volumes)
            
            return 0.0
            
        except Exception as e:
            print(f"Exception while fetching historical volume for {symbol}: {e}")
            return 0.0
    
    def calculate_volume_change(self, current_volume: float, avg_volume: float) -> float:
        """
        Calculate percentage change between current and average volume.
        
        Args:
            current_volume: Current 24h volume
            avg_volume: Historical average volume
            
        Returns:
            Percentage change (e.g., 30.5 for 30.5% increase)
        """
        if avg_volume == 0:
            return 0.0
        return ((current_volume - avg_volume) / avg_volume) * 100
    
    def scan_volume_spikes(self) -> List[Dict]:
        """
        Scan all trading pairs for volume spikes exceeding the threshold.
        
        Returns:
            List of dictionaries containing alert information for pairs with volume spikes
        """
        alerts = []
        tickers = self.get_all_tickers()
        
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Scanning {len(tickers)} pairs...")
        
        if self.first_run:
            print("First run detected - building baseline data, no alerts will be triggered.")
        
        for ticker in tickers:
            symbol = ticker['symbol']
            current_volume_24h = float(ticker.get('volume24h', 0))
            
            # Skip if volume is negligible
            if current_volume_24h < 0.01:
                continue
            
            # Update volume record with current data
            self._update_volume_record(symbol, current_volume_24h)
            
            # Skip alerts on first run - just collect data
            if self.first_run:
                continue
            
            # Try to get average from local history first
            avg_volume = self._get_average_volume_from_history(symbol)
            
            # If no local history, fall back to API (slower but necessary for new pairs)
            if avg_volume is None:
                avg_volume = self.get_historical_volume(symbol, self.timeframe_hours)
                if avg_volume == 0:
                    continue
            
            # Calculate volume change
            volume_change_pct = self.calculate_volume_change(current_volume_24h, avg_volume)
            
            # Check if threshold exceeded
            if volume_change_pct >= self.volume_increase_threshold:
                alert_info = {
                    'symbol': symbol,
                    'current_volume': current_volume_24h,
                    'avg_volume': avg_volume,
                    'volume_change_pct': volume_change_pct,
                    'last_price': ticker.get('lastPrice', 'N/A'),
                    'price_change_24h': ticker.get('price24hPcnt', 'N/A'),
                    'timestamp': datetime.now().isoformat()
                }
                alerts.append(alert_info)
        
        # Save updated volume history
        self._save_volume_history()
        
        # After first run, subsequent runs will check for spikes
        if self.first_run:
            self.first_run = False
            print(f"Baseline data collected for {len(self.volume_history)} pairs.")
        
        return alerts
    
    def send_alert(self, alert: Dict):
        """
        Send alert for a volume spike. Currently prints to console.
        Can be extended to send emails, webhooks, etc.
        
        Args:
            alert: Dictionary containing alert information
        """
        print("\n" + "="*80)
        print("🚨 VOLUME SPIKE ALERT 🚨")
        print("="*80)
        print(f"Symbol:           {alert['symbol']}")
        print(f"Current Volume:   {alert['current_volume']:,.2f}")
        print(f"Average Volume:   {alert['avg_volume']:,.2f}")
        print(f"Volume Increase:  {alert['volume_change_pct']:.2f}%")
        print(f"Current Price:    {alert['last_price']}")
        print(f"Price Change 24h: {alert['price_change_24h']}")
        print(f"Time:             {alert['timestamp']}")
        print("="*80 + "\n")
    
    def run(self):
        """
        Main loop to continuously scan for volume spikes.
        """
        print("="*80)
        print("Bybit Volume Scanner Started")
        print("="*80)
        print(f"Category:              {self.category}")
        print(f"Timeframe:             {self.timeframe_hours} hours")
        print(f"Volume Threshold:      {self.volume_increase_threshold}%")
        print(f"Check Interval:        {self.check_interval_seconds} seconds")
        print(f"Data File:             {self.data_file.absolute()}")
        print(f"Tracked Symbols:       {len(self.volume_history)}")
        print("="*80)
        
        try:
            while True:
                alerts = self.scan_volume_spikes()
                
                if alerts:
                    print(f"\n✅ Found {len(alerts)} volume spike(s)!")
                    for alert in alerts:
                        self.send_alert(alert)
                else:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] No volume spikes detected.")
                
                print(f"Waiting {self.check_interval_seconds} seconds until next scan...\n")
                time.sleep(self.check_interval_seconds)
                
        except KeyboardInterrupt:
            print("\n\nScanner stopped by user.")
        except Exception as e:
            print(f"\n\nError in main loop: {e}")


def main():
    """
    Main entry point with configurable parameters.
    Modify these values to customize the scanner behavior.
    """
    # Configuration
    CATEGORY = "spot"  # Options: 'spot', 'linear' (perpetual futures), 'inverse'
    TIMEFRAME_HOURS = 24  # Lookback period for average volume calculation
    VOLUME_INCREASE_THRESHOLD = 30.0  # Minimum % increase to trigger alert
    CHECK_INTERVAL_SECONDS = 300  # Time between scans (5 minutes)
    
    # Create and run scanner
    scanner = BybitVolumeScanner(
        category=CATEGORY,
        timeframe_hours=TIMEFRAME_HOURS,
        volume_increase_threshold=VOLUME_INCREASE_THRESHOLD,
        check_interval_seconds=CHECK_INTERVAL_SECONDS
    )
    
    scanner.run()


if __name__ == "__main__":
    main()
