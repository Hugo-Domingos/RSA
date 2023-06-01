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
        self.distance_to_ambulance = 0
        self.graph = graph
        self.current_edge = current_edge
        self.coords = coords
        self.special_vehicle = special_vehicle
        self.distance_to_ambulance = None
        self.obu_emergency = obu_emergency
        self.blocked = False
        self.pulled_over = False
        # self.signal_group = self.graph.edges(self.current_edge)['attr']['signalGroup']
        self.signal_group = 5
        self.last_received_denm = None
        self.time = 0
        self.endtime = 0

    def start(self):
        client = mqtt.Client(self.name)
        client.on_message = self.on_message
        client.connect(self.address, 1883, 60)
        client.subscribe(topic=[("vanetza/out/denm", 0)])
        client.subscribe(topic=[("vanetza/out/cam", 0)])
        client.subscribe(topic=[("vanetza/out/spatem", 0)])
        client.loop_start()

        while not self.finished:
            if self.obu_emergency.has_finished():
                self.finished = True
                break
            cam_message = self.generate_cam()
            self.send_message('vanetza/in/cam', cam_message)
            # print(f'IN -> OBU: {self.name} | MSG: {cam_message}\n')
            
            # if the last recevied denm is older than 2 seconds, then the obu is not pulled over
            if self.last_received_denm is not None and time.time() - self.last_received_denm > 5:
                self.pulled_over = False
            if self.time != 0 and self.time==self.endtime:
                self.signal_group = 5
            
            # print(f"CURRENT EDGE: {self.current_edge}")
            # # get current edge id from self.graph
            # print(nx.get_edge_attributes(self.graph, 'attr')[self.current_edge]['id'])

            time.sleep(1)
        
        # end the client
        client.loop_stop()
        client.disconnect()

    def get_obu_edge(self):
        return self.current_edge

    def on_message(self, client, userdata, msg):
        message = json.loads(msg.payload.decode('utf-8'))
        msg_type = msg.topic

        if msg_type == 'vanetza/out/denm':
            # print(f"OUT DENM OBU[{ message['fields']['denm']['management']['actionID']['originatingStationID'] }] -> OBU[{ self.id }]: {self.name}\n")
            self.pulled_over = True
            self.last_received_denm = message['timestamp']

        if msg_type == 'vanetza/out/spatem':
            # print(f"OUT SPATEM OBU[{ message}] -> OBU[{ self.current_edge }]: {self.name}\n")
            edges = self.graph.edges()
            states = message['fields']['spat']['intersections'][0]['states']

            for state in states:
                print (state['signalGroup'])
                if state['signalGroup'] == edges[self.current_edge]['attr']['signalGroup']:
                    if state['state-time-speed'][0]['eventState'] == 2:
                        self.signal_group = state['state-time-speed'][0]['eventState']
                        # print("OBU" + str(self.current_edge) + " -> ROSSO")
                        self.endtime=state['state-time-speed'][0]['timing']['minEndTime']
                        self.time=time.time()
                    
                        # print("OBU" + str(self.current_edge) + " -> VERDE")              
         
        # if msg_type == 'vanetza/out/cam':
        #     # resend message with data of the cam received
        #     if message['fields']['cam']['header']['stationID'] != self.id:
        #         print(f"OUT CAM OBU[{ message['fields']['cam']['header']['stationID'] }] -> OBU[{ self.id }]: {self.name}\n")
        #         self.send_message('vanetza/in/cam', message)
                # self.pulled_over = False
                
            
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
            19,
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

    def get_pulled_over(self):
        return self.pulled_over
    
    def get_signal_group(self):
        return self.signal_group