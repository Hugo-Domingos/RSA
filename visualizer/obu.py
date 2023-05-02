import json
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import time
import cam
from navigation import Navigation
import route

class OBU:
    def __init__(self, name, id, address, obu, starting_route, special_vehicle):
        self.name = name
        self.id = id
        self.address = address
        self.obu = obu
        self.finished = False
        self.length = 4.5
        self.width = 1.8
        self.speed = 0
        self.velocity = 0
        self.navigation = Navigation()
        self.current_route = starting_route
        self.coords = self.navigation.get_next_coords(self.current_route, None)
        self.special_vehicle = special_vehicle
    
    def start(self):
        client = mqtt.Client(self.name)
        client.on_message = self.on_message
        client.connect(self.address, 1883, 60)
        client.subscribe(topic=[("vanetza/out/cam", 0)])
        client.loop_start()

        while not self.finished:
            cam_message = self.generate_cam()
            self.send_message('vanetza/in/cam', cam_message)
            print(f'IN -> OBU: {self.name} | MSG: {cam_message}\n')
            # self.coords[0] += 0.01
            # self.coords[1] += 0.01
            if self.navigation.at_intersection(self.coords):
                self.current_route = self.navigation.change_route(self.current_route)
                self.coords = None
            self.coords = self.navigation.get_next_coords(self.current_route, self.coords)
            time.sleep(1)

    def on_message(self, client, userdata, msg):
        pass
        # message = json.loads(msg.payload.decode('utf-8'))
        # msg_type = msg.topic

        # if msg_type == 'vanetza/out/cam':
        #     # self.coords[0] = message['latitude']
        #     # self.coords[1] = message['longitude']
        #     # print(f'OUT -> OBU: {self.name} | MSG: {message}\n')
        #     pass

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

    def move_obu(self):
        if Navigation.at_intersection(self.coords):
            self.current_route = self.set_route()
        self.coords = self.current_route.get_next_coords(self.coords)
        

    def set_route(self, route):
        self.current_route = route