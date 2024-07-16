import os
import time
import logging
from datetime import datetime
from flask import Flask, flash, render_template, request, jsonify
from flask_socketio import SocketIO
import threading
from engineio.async_drivers import gevent
import psutil
import MetaTrader5 as mt5
from telmsg import send_message
from metricschart import get_cpu_metrics, get_network_speed, create_violin_plot, create_gauge_chart
from copy import deepcopy
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
import jinja2.ext
from threading import Thread
import sys


# Initialize Flask and SocketIO
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'mynameisprincejerrymypasswordisBeautysoap01#')
socketio = SocketIO(app, async_mode='gevent', async_handler='threading')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
positions = []
last_sent_positions = []
signal_thread_running = False
metrics_thread_running = False
signal_details_provided = False

signal_details_info = {
    'login': None,
    'password': None,
    'server': None,
}

lock = threading.Lock()  # Lock for thread safety

# MetaTrader 5 initialization
if not mt5.initialize():
    logger.error("Failed to initialize MetaTrader 5")
    mt5.shutdown()

# Routes
@app.route('/')
def loader():
    return render_template('loader.html')

@app.route('/signal')
def signal():
    return render_template('sig2.html', positions=positions)

@app.route('/signal_details', methods=['GET', 'POST'])
def signal_details():
    global signal_details_provided, signal_details_info
    if request.method == 'POST':
        signal_details_info['login'] = request.form['Login']
        signal_details_info['password'] = request.form['Password']
        signal_details_info['server'] = request.form['Server']
        signal_details_provided = True
        logger.info("Successfully logged in to MetaTrader 5")
        socketio.emit('message', {'message': "Successfully logged in to MetaTrader 5", 'category': 'info'})
        flash("logged in successfully")
        print("signal details provided", signal_details_provided)
    return render_template('sig2.html')

@app.route('/thread_status')
def thread_status():
    return jsonify({
        "signal_thread_running": signal_thread_running,
        "metrics_thread_running": metrics_thread_running
    })

@app.route('/toggle_fetch_signals', methods=['POST'])
def toggle_fetch_signals():
    data = request.json
    start = data.get('start', False)
    toggle_fetch_signals_thread(start)
    message = "Signal fetching loop started." if start else "Signal fetching loop stopped."
    logger.info(message)
    socketio.emit('message', {'message': message, 'category': 'info'})
    return jsonify({"message": message})

@app.route('/shutdown_mt5', methods=['POST'])
def shutdown_mt5():
    global signal_thread_running
    try:
        mt5.shutdown()
        message = "Emitter shutting down..."
        logger.info(message)
        socketio.emit('message', {'message': message, 'category': 'info'})
        signal_thread_running = False
        return {"message": "MT5 shutdown successful"}, 200
    except Exception as e:
        error_message = f"Error shutting down MT5: {e}"
        logger.error(error_message)
        return {"message": error_message}, 500

@app.route('/metrics')
def metrics():
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    data = {
        'cpu_usage': cpu_usage,
        'memory_usage': memory_info.percent,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return jsonify(data)

@app.route('/network_speed')
def network_speed():
    download_speed = random.uniform(50, 150)
    upload_speed = random.uniform(10, 50)
    data = {
        'download_speed': download_speed,
        'upload_speed': upload_speed
    }
    return jsonify(data)

@app.route('/toggle_metrics', methods=['POST'])
def toggle_metrics():
    data = request.json
    start = data.get('start', False)
    toggle_metrics_thread(start)
    return jsonify({"status": "success", "metrics_thread_running": metrics_thread_running})

@socketio.on('connect')
def handle_connect():
    toggle_metrics_thread(True)

def fetch_signals():
    if signal_details_provided:
        toggle_fetch_signals_thread(True)

def toggle_fetch_signals_thread(start):
    global signal_thread_running
    with lock:
        if start and not signal_thread_running:
            signal_thread_running = True
            thread = threading.Thread(target=fetch_signals_loop)
            thread.start()
            logger.info("Signal fetching loop started.")
            socketio.emit('message', {'message': "Signal fetching loop started.", 'category': 'info'})
            flash('Fetching signal...')
        elif not start and signal_thread_running:
            signal_thread_running = False
            logger.info("Signal fetching loop stopped.")
            socketio.emit('message', {'message': "Signal fetching loop stopped.", 'category': 'info'})

def fetch_signals_loop():
    global last_sent_positions, positions, signal_thread_running
    while signal_thread_running and signal_details_provided:
        try:
            time.sleep(5)
            new_pos = mt5.positions_get()
            if new_pos is not None:
                if len(new_pos) == 0:
                    logger.info("No open positions found.")
                    socketio.emit('message', {'message': "No open positions found.", 'category': 'info'})
                else:
                    new_positions = []
                    for p in new_pos:
                        try:
                            date = datetime.utcfromtimestamp(p.time).strftime('%Y-%m-%d')
                            time_str = datetime.utcfromtimestamp(p.time).strftime('%H:%M')
                            action = f"{'Buy' if p.type == 0 else 'Sell'} - {p.symbol}"
                            new_positions.append({
                                'date': date,
                                'time': time_str,
                                'symbol': p.symbol,
                                'action': action,
                                'entry_price': p.price_open,
                                'tp1': p.tp,
                                'tp2': p.tp + 2,
                                'tp3': p.tp + 4,
                                'tp4': p.tp + 8,
                                'sl': p.sl,
                            })
                        except Exception as e:
                            error_message = f"Error appending position: {e}"
                            logger.error(error_message)
                            socketio.emit('message', {'message': error_message, 'category': 'error'})

                    with lock:
                        if new_positions != last_sent_positions:
                            positions.clear()
                            positions.extend(new_positions)
                            socketio.emit('new_signal', positions)
                            message_text = "BMV for Telegram.\nWith Love from Big Move Software.\n"
                            for pos in positions:
                                message_text += f"Date: {pos['date']}\nTime: {pos['time']}\nSymbol: {pos['symbol']}\nAction: {pos['action']}\n"
                                message_text += f"Entry Price: {pos['entry_price']}\nTake Profit 1: {pos['tp1']}\n"
                                message_text += f"Take Profit 2: {pos['tp2']}\nTake Profit 3: {pos['tp3']}\n"
                                message_text += f"Take Profit 4: {pos['tp4']}\nSTOP LOSS: {pos['sl']}\n\n"
                            send_message(message_text)
                            last_sent_positions = deepcopy(new_positions)
            else:
                logger.info("No open positions found.")
                flash('No Open Positions Found.')
                socketio.emit('message', {'message': "No open positions found.", 'category': 'info'})
        except Exception as e:
            error_message = f"Error in fetch_signals: {e}"
            logger.error(error_message)
            socketio.emit('message', {'message': error_message, 'category': 'error'})

def toggle_metrics_thread(start):
    global metrics_thread_running
    with lock:
        if start and not metrics_thread_running:
            metrics_thread_running = True
            thread = threading.Thread(target=emit_metrics)
            thread.start()
        elif not start and metrics_thread_running:
            metrics_thread_running = False

def emit_metrics():
    while metrics_thread_running:
        cpu_metrics = get_cpu_metrics()
        download_speed, upload_speed = get_network_speed()
        cpu_violin_plot = create_violin_plot(cpu_metrics)
        download_speed_gauge = create_gauge_chart(download_speed, 'Download Speed (Mbps)', 150)
        upload_speed_gauge = create_gauge_chart(upload_speed, 'Upload Speed (Mbps)', 50)
        socketio.emit('update_metrics', {
            'cpu_violin_plot': cpu_violin_plot,
            'download_speed_gauge': download_speed_gauge,
            'upload_speed_gauge': upload_speed_gauge,
        })
        time.sleep(5)

@app.route('/conError')
def conError():
    return render_template('connectionerror.html')

@app.route('/timeout')
def timeout():
    return render_template('timeout.html')

def run_flask_app():
    socketio.run(app)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Emitter GUI")
        self.setGeometry(100, 100, 1024, 768)
        
        self.web_view = QWebEngineView()
        self.setCentralWidget(self.web_view)
        
        # Use QUrl.fromLocalFile for local files
        self.web_view.load(QUrl("http://127.0.0.1:5000"))

def main():
    # Run Flask app in a separate thread
    flask_thread = Thread(target=run_flask_app)
    flask_thread.daemon = True
    flask_thread.start()

    # Create and display the PyQt5 window
    qt_app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(qt_app.exec_())

if __name__ == '__main__':
    main()
    if os.environ.get('PRODUCTION'):
        # In production, use Gunicorn with Gevent
        import gunicorn.app.base

        class StandaloneApplication(gunicorn.app.base.BaseApplication):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                config = {key: value for key, value in self.options.items()
                          if key in self.cfg.settings and value is not None}
                for key, value in config.items():
                    self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        app = Flask(__name__)
        socketio = SocketIO(app)
        options = {
            'worker_class': 'gevent',
            'workers': 1,
            'bind': '0.0.0.0:5000'
        }
        StandaloneApplication(app, options).run()
    else:
        # In development, use the Flask development server
        app = Flask(__name__)
        socketio = SocketIO(app)
        socketio.run(app, debug=True)
