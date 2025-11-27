#!/usr/bin/env python3
"""
Bybit Volume Scanner - Web Interface
A Flask-based web UI for monitoring and configuring the volume scanner.
"""

import os
import threading
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from main import BybitVolumeScanner

# Get data file path from environment or use default
DEFAULT_DATA_FILE = os.environ.get('DATA_FILE', 'volume_data.json')

app = Flask(__name__)

# Global scanner instance and state
scanner = None
scanner_thread = None
scanner_running = False
latest_alerts = []
scan_status = {
    'is_running': False,
    'last_scan_time': None,
    'total_pairs': 0,
    'alerts_count': 0,
    'first_run': True
}

def run_scanner_loop():
    """Background thread to run the scanner continuously."""
    global scanner, scanner_running, latest_alerts, scan_status
    
    while scanner_running:
        try:
            # Perform scan
            scan_status['last_scan_time'] = datetime.now().isoformat()
            alerts = scanner.scan_volume_spikes()
            
            # Update alerts (keep last 50)
            for alert in alerts:
                latest_alerts.insert(0, alert)
            latest_alerts[:] = latest_alerts[:50]
            
            scan_status['alerts_count'] = len(latest_alerts)
            scan_status['first_run'] = scanner.first_run
            
            # Wait for next scan
            time.sleep(scanner.check_interval_seconds)
            
        except Exception as e:
            print(f"Error in scanner loop: {e}")
            time.sleep(10)

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')

@app.route('/api/config', methods=['GET', 'POST'])
def config():
    """Get or update scanner configuration."""
    global scanner
    
    if request.method == 'POST':
        data = request.json
        
        # Update scanner configuration
        if scanner:
            scanner.category = data.get('category', scanner.category)
            scanner.timeframe_hours = int(data.get('timeframe_hours', scanner.timeframe_hours))
            scanner.volume_increase_threshold = float(data.get('volume_increase_threshold', scanner.volume_increase_threshold))
            scanner.check_interval_seconds = int(data.get('check_interval_seconds', scanner.check_interval_seconds))
        
        return jsonify({'status': 'success', 'message': 'Configuration updated'})
    
    # GET - return current config
    if scanner:
        return jsonify({
            'category': scanner.category,
            'timeframe_hours': scanner.timeframe_hours,
            'volume_increase_threshold': scanner.volume_increase_threshold,
            'check_interval_seconds': scanner.check_interval_seconds,
            'data_file': str(scanner.data_file),
            'tracked_symbols': len(scanner.volume_history)
        })
    
    # Return default configuration if scanner not initialized
    return jsonify({
        'category': 'spot',
        'timeframe_hours': 24,
        'volume_increase_threshold': 30.0,
        'check_interval_seconds': 300,
        'data_file': DEFAULT_DATA_FILE,
        'tracked_symbols': 0
    })

@app.route('/api/start', methods=['POST'])
def start_scanner():
    """Start the scanner."""
    global scanner, scanner_thread, scanner_running, scan_status
    
    if scanner_running:
        return jsonify({'status': 'info', 'message': 'Scanner already running'})
    
    # Get configuration from request
    data = request.json or {}
    
    # Initialize scanner
    scanner = BybitVolumeScanner(
        category=data.get('category', 'spot'),
        timeframe_hours=int(data.get('timeframe_hours', 24)),
        volume_increase_threshold=float(data.get('volume_increase_threshold', 30.0)),
        check_interval_seconds=int(data.get('check_interval_seconds', 300)),
        data_file=data.get('data_file', DEFAULT_DATA_FILE)
    )
    
    # Start scanner thread
    scanner_running = True
    scan_status['is_running'] = True
    scan_status['first_run'] = scanner.first_run
    scanner_thread = threading.Thread(target=run_scanner_loop, daemon=True)
    scanner_thread.start()
    
    return jsonify({'status': 'success', 'message': 'Scanner started'})

@app.route('/api/stop', methods=['POST'])
def stop_scanner():
    """Stop the scanner."""
    global scanner_running, scan_status
    
    scanner_running = False
    scan_status['is_running'] = False
    
    return jsonify({'status': 'success', 'message': 'Scanner stopped'})

@app.route('/api/status')
def status():
    """Get current scanner status."""
    return jsonify(scan_status)

@app.route('/api/alerts')
def alerts():
    """Get latest alerts."""
    return jsonify({
        'alerts': latest_alerts,
        'count': len(latest_alerts)
    })

@app.route('/api/volume-history/<symbol>')
def volume_history(symbol):
    """Get volume history for a specific symbol."""
    if scanner and symbol in scanner.volume_history:
        return jsonify({
            'symbol': symbol,
            'history': scanner.volume_history[symbol]
        })
    return jsonify({'error': 'Symbol not found'}), 404

@app.route('/api/all-symbols')
def all_symbols():
    """Get list of all tracked symbols with their latest volume."""
    if not scanner:
        return jsonify({'error': 'Scanner not initialized'}), 400
    
    symbols_data = []
    for symbol, history in scanner.volume_history.items():
        if history:
            latest = history[-1]
            avg_volume = scanner._get_average_volume_from_history(symbol)
            
            symbols_data.append({
                'symbol': symbol,
                'current_volume': latest['volume'],
                'avg_volume': avg_volume,
                'last_update': latest['timestamp'],
                'data_points': len(history)
            })
    
    # Sort by current volume descending
    symbols_data.sort(key=lambda x: x['current_volume'], reverse=True)
    
    return jsonify({
        'symbols': symbols_data,
        'total': len(symbols_data)
    })

@app.route('/api/reset', methods=['POST'])
def reset_data():
    """Reset volume history data."""
    global scanner, latest_alerts
    
    if scanner:
        scanner.volume_history = {}
        scanner.first_run = True
        scanner._save_volume_history()
        latest_alerts.clear()
        
        return jsonify({'status': 'success', 'message': 'Volume history reset'})
    
    return jsonify({'error': 'Scanner not initialized'}), 400

if __name__ == '__main__':
    print("="*80)
    print("Bybit Volume Scanner - Web Interface")
    print("="*80)
    print("Access the dashboard at: http://localhost:5000")
    print("="*80)
    
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
