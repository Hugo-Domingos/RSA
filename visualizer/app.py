from flask import Flask, render_template
import paho.mqtt.client as mqtt
import threading
import json
from flask import request

from Simulation import Simulation

app = Flask(__name__)

obu1_lat = None
obu1_lng = None
obu2_lat = None
obu2_lng = None

s = Simulation()

@app.route('/')
def index():
    return render_template('index.html', refresh_rate=100)

@app.route('/state')
def get_state():
    status, connections, pulled_over, finished, cars_coordinates,signal_group, paths_table, best_path, graph = s.get_status()
    return json.dumps([status, connections, pulled_over, finished, cars_coordinates,signal_group, paths_table, best_path, graph])

@app.route('/start_simulation', methods=['POST'])
def start_simulation():
    print('starting simulation')
    global s
    situation_id = int(request.form.get('situation_id', 0))
    s.set_situation(situation_id)
    thread = threading.Thread(target=s.run)
    thread.start()
    # thread.join()
    return 'Simulation started'

@app.route('/kill_simulation', methods=['POST'])
def kill_simulation():
    s.kill_simulation()
    return 'Simulation killed'

if __name__ == '__main__':
    app.run(debug=True, threaded=True)

