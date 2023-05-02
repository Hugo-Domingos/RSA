from flask import Flask, render_template
import paho.mqtt.client as mqtt
import threading
import json

from Simulation import Simulation

app = Flask(__name__)

obu1_lat = None
obu1_lng = None
obu2_lat = None
obu2_lng = None

# obus = []

s = Simulation()

@app.route('/')
def index():
    # obu1_client = mqtt.Client()
    # obu1_client.on_connect = on_connect
    # obu1_client.on_message = on_message
    # obu1_client.connect('192.168.98.20', 1883, 60)
    # obu2_client = mqtt.Client()
    # obu2_client.on_connect = on_connect
    # obu2_client.on_message = on_message
    # obu2_client.connect('192.168.98.30', 1883, 60)
    
    # threading.Thread(target=obu1_client.loop_forever).start()
    # threading.Thread(target=obu2_client.loop_forever).start()
    # global obu1_lat, obu1_lng, obu2_lat, obu2_lng

    thread = threading.Thread(target=s.run)
    thread.start()
    # thread.join()
    

    return render_template('index.html', refresh_rate=1000)
   

# def on_message(client, userdata, msg):
#     message = json.loads(msg.payload.decode('utf-8'))
#     print('Topic: ' + msg.topic)
#     print('Message: ' + str(message)) 
#     global obu1_lat, obu1_lng, obu2_lat, obu2_lng
#     lat = message['latitude']
#     lng = message['longitude']
#     print('LATITUDE: ' + str(lat) + ' | LONGITUDE: ' + str(lng))         

# def on_connect(client, userdata, flags, rc):
#     print("Connected with result code "+str(rc))
#     client.subscribe("vanetza/out/cam")
#     # client.subscribe("vanetza/out/denm")
#     # ...

@app.route('/state')
def get_state():
    status = s.get_status()
    return json.dumps(status)

if __name__ == '__main__':
    app.run(debug=True, threaded=True)

