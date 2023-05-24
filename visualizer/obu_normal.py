import json
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import geopy.distance
import time
import cam
import denm
from navigation import Navigation
import math
import networkx as nx
import subprocess
from obu_emergency import OBUEmergency


class OBUNormal:
    def __init__(self, name, id, address, mac_address, obu, special_vehicle, coords, current_edge, graph, obu_emergency):
        self.name = name
        self.id = id
        self.address = address
        self.mac_address = mac_address
        self.obu = obu
        self.finished = False
        self.length = 4.5
        self.width = 1.8
        self.speed = 0
        self.velocity = 0
        self.navigation = Navigation()
        self.distance_to_ambulance = 0
        self.graph = graph
        self.current_edge = current_edge
        self.coords = coords
        self.special_vehicle = special_vehicle
        self.distance_to_ambulance = None
        self.obu_emergency = obu_emergency
        self.blocked = False

    def start(self):
        client = mqtt.Client(self.name)
        client.on_message = self.on_message
        client.connect(self.address, 1883, 60)
        client.subscribe(topic=[("vanetza/out/denm", 0)])
        client.subscribe(topic=[("vanetza/out/cam", 0)])
        client.loop_start()

        while not self.finished:
            # self.distance_to_ambulance = self.get_distance_from_ambulance(ambulance_coords=self.obu_emergency.get_coords())
            # print(f"Distance to ambulance: {self.distance_to_ambulance}")
            # if self.distance_to_ambulance <= 80 and self.blocked:
            #     print("IN RANGE")
            #     res = subprocess.call(f"docker-compose exec {self.name} unblock 6e:06:e0:03:00:02", shell=True)
            #     print(res)
            #     self.blocked = False
            # elif self.distance_to_ambulance > 80 and not self.blocked:
            #     print("OUT OF RANGE")
            #     subprocess.call(f"docker-compose exec {self.name} block 6e:06:e0:03:00:02", shell=True)
            #     self.blocked = True
                
            cam_message = self.generate_cam()
            self.send_message('vanetza/in/cam', cam_message)
            # print(f'IN -> OBU: {self.name} | MSG: {cam_message}\n')
            if self.special_vehicle == 1:
                denm_message = self.generate_denm()
                denm_message['management']['stationType'] = 10
                self.send_message('vanetza/in/denm', denm_message)
                # print(f'IN DENM -> OBU: {self.name} | MSG: {denm_message}\n')
            
            time.sleep(1)
        
        # end the client
        client.loop_stop()
        client.disconnect()

    def on_message(self, client, userdata, msg):
        message = json.loads(msg.payload.decode('utf-8'))
        msg_type = msg.topic

        if msg_type == 'vanetza/out/denm':
            print(f"OUT DENM OBU[{ message['fields']['denm']['management']['actionID']['originatingStationID'] }] -> OBU[{ self.id }]: {self.name}\n")
            
            # if( geopy.distance.distance((message['fields']['denm']['management']['eventPosition']['latitude'], message['fields']['denm']['management']['eventPosition']['longitude']), (self.coords[0], self.coords[1])).meters < 125 and message['fields']['denm']['management']['stationType']==10) :
            #     print("IN RANGE") #check station id para ver se é da ambulancia ou da rsu
            #     print("amb IS CLOSER,STOPPING")
            #     # subprocess.call(f"docker-compose exec {self.name} unblock 6e:06:e0:03:00:02", shell=True)
            #     #ver se a mbulanci tem long> e lat< que a do obu
            # elif message['fields']['denm']['management']['stationType']==15:
            #     print("rsu is says that amb IS CLOSER,STOPPING")
            # else:
            #     print("OUT OF RANGE")
            #     # subprocess.call(f"docker-compose exec {self.name} block 6e:06:e0:03:00:02", shell=True)

    def get_distance_from_ambulance(self, ambulance_coords):
        return geopy.distance.distance(ambulance_coords, self.coords).meters

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
    
    def generate_denm(self):
        denm_message = denm.DENM(
            denm.Management(
                denm.ActionID(self.id,0),
                0.0,
                0.0,
                denm.EventPosition(self.coords[0], self.coords[1], 
                denm.PositionConfidenceEllipse(0,0,0), 
                denm.Altitude(0,0)),
                0,
                0
            ),
            denm.Situation(7,denm.EventType(14,14))
        )
        return denm.DENM.to_dict(denm_message)
    
    def send_message(self, topic, message):
        publish.single(topic, json.dumps(message), hostname=self.address)

    def set_finished(self, value):
        self.finished = value

    def set_route(self, route):
        self.current_route = route