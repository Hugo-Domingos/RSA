import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import time
import cam
import json

class RSU:
    def __init__(self, name, id, address, rsu, route, coords):
        self.name = name
        self.id = id
        self.address = address
        self.rsu = rsu
        self.finished = False
        self.length = 4.5
        self.width = 1.8
        self.route = route
        self.coords = coords

        #to be removed
        self.speed = 0

    def start(self):
        client = mqtt.Client(self.name)
        client.on_message = self.on_message
        client.connect(self.address, 1883, 60)
        client.subscribe(topic=[("vanetza/out/cam", 0)])
        client.loop_start()

        while not self.finished:
            # cam_message = self.generate_cam()
            # self.send_message('vanetza/in/cam', cam_message)
            # print(f'IN -> RSU: {self.name} | MSG: {cam_message}\n')
            time.sleep(1)

    def on_message(self, client, userdata, msg):
        message = json.loads(msg.payload.decode('utf-8'))
        msg_type = msg.topic

        if msg_type == 'vanetza/out/cam':
            # self.coords[0] = message['latitude']
            # self.coords[1] = message['longitude']
            print(f'OUT -> RSU: {self.name} | MSG: {message}\n')

    def generate_cam(self):
        cam_message = cam.CAM(
            True,
            10.0,
            0,
            0,
            False,
            True,
            True,
            0,
            "FORWARD",
            False,
            True,
            0,
            0,
            self.coords[0],
            self.length,
            self.coords[1],
            0,
            0,
            0,
            cam.SpecialVehicle(cam.PublicTransportContainer(False)),
            self.speed,
            0,
            True,
            self.id,
            15,
            self.width,
            0,

        )
        return cam.CAM.to_dict(cam_message)
    
    def send_message(self, topic, message):
        publish.single(topic, json.dumps(message), hostname=self.address)

    def set_finished(self, value):
        self.finished = value
    