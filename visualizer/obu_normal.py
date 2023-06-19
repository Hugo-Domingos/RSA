from asyncio import sleep
import json
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import geopy.distance
import time
import cam
import denm
import math
import networkx as nx
import subprocess
from obu_emergency import OBUEmergency
from random import choice


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
        self.last_received_spatem = None

    def start(self):
        client = mqtt.Client(self.name)
        client.on_message = self.on_message
        client.connect(self.address, 1883, 60)
        client.subscribe(topic=[("vanetza/out/denm", 0)])
        client.subscribe(topic=[("vanetza/out/cam", 0)])
        client.subscribe(topic=[("vanetza/out/spatem", 0)])
        client.loop_start()
        tick_num = 0
        while not self.finished:
            # print(f"OBU[{ self.id }]: {self.current_edge} with coords {self.coords}")
            tick_num += 1
            if self.obu_emergency.has_finished():
                self.finished = True
                break
            cam_message = self.generate_cam()
            self.send_message('vanetza/in/cam', cam_message)
            # if self.id == 10:
            # print(f'IN CAM -> OBU: {self.id} | MSG: {cam_message}\n')
            
            # if the last recevied denm is older than 3 seconds, then the obu is not pulled over
            while self.last_received_denm is not None and time.time() - self.last_received_denm < 2 or self.last_received_spatem is not None and time.time() - self.last_received_spatem < 3:
                cam_message = self.generate_cam()
                self.send_message('vanetza/in/cam', cam_message)
                time.sleep(0.2)
            self.pulled_over = False

            # if self.last_received_denm is not None and time.time() - self.last_received_denm > 3:
            # while self.last_received_spatem is not None and time.time() - self.last_received_spatem < 3:
            #     cam_message = self.generate_cam()
            #     self.send_message('vanetza/in/cam', cam_message)
            #     time.sleep(0.2)
            
            self.signal_group = 5   
            
            if tick_num % 2 == 0:
                if self.is_on_node():
                    self.change_edge()
                if self.finished:
                    break
                self.coords = self.get_next_coords()
            # print(f"OBU[{ self.id }]: {self.name} | COORDS: {self.coords} | EDGE: {self.current_edge} | SIGNAL GROUP: {self.signal_group} | PULLED OVER: {self.pulled_over}\n")

            time.sleep(0.5)
        
        # end the client
        client.loop_stop()
        client.disconnect()

    def get_next_coords(self):
        if self.coords == None:
            aux = list(self.graph.get_edge_data(*self.current_edge)['attr']['list_of_coordinates'])[0]
            return aux
        current_coords_index = list(self.graph.get_edge_data(*self.current_edge)['attr']['list_of_coordinates']).index(self.coords)
        return list(self.graph.get_edge_data(*self.current_edge)['attr']['list_of_coordinates'])[current_coords_index + 1]

    def is_on_node(self):
        if self.graph.get_edge_data(*self.current_edge)['attr']['list_of_coordinates'].index(self.coords) == len(self.graph.get_edge_data(*self.current_edge)['attr']['list_of_coordinates']) - 1:
            return True
        return False
    
    def change_edge(self):
        # choose the next edge randomly
        successor_id = choice(list(self.graph.successors(self.current_edge[1])))
        self.current_edge = (self.current_edge[1], successor_id)
        self.coords = None

    def get_obu_edge(self):
        return self.current_edge

    def on_message(self, client, userdata, msg):
        message = json.loads(msg.payload.decode('utf-8'))
        msg_type = msg.topic

        if msg_type == 'vanetza/out/denm':
            self.pulled_over = True
            self.last_received_denm = message['timestamp']
            print(f"OBU[{ self.id }] received denm | MSG: {message}\n")

        if msg_type == 'vanetza/out/spatem':
            # if self.id == 10:
            #     print(f"OBU[{ self.id }] received spatem | MSG: {message}\n")
            # print(f"OUT SPATEM OBU[{ message}] -> OBU[{ self.current_edge }]: {self.name}\n")
            edges = self.graph.edges()
            states = message['fields']['spat']['intersections'][0]['states']

            for state in states:
                if state['signalGroup'] == edges[self.current_edge]['attr']['signalGroup']:
                    if state['state-time-speed'][0]['eventState'] == 2:
                        self.signal_group = state['state-time-speed'][0]['eventState']

                        self.last_received_spatem = message['timestamp']                
            
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