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

class OBUEmergency:
    def __init__(self, name, id, address, mac_address, obu, special_vehicle, coords, current_edge, graph):
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
        self.graph = graph
        self.current_edge = current_edge
        self.coords = None
        self.coords = self.get_next_coords()
        self.special_vehicle = special_vehicle
        self.best_path = self.best_distance_path(5)

    def start(self):
        client = mqtt.Client(self.name)
        client.on_message = self.on_message
        client.connect(self.address, 1883, 60)
        client.subscribe(topic=[("vanetza/out/denm", 0)])
        client.subscribe(topic=[("vanetza/out/cam", 0)])
        client.loop_start()
        while not self.finished:
            cam_message = self.generate_cam()
            self.send_message('vanetza/in/cam', cam_message)
            # print(f'IN -> OBU: {self.name} | MSG: {cam_message}\n')
            if self.special_vehicle == 1:
                denm_message = self.generate_denm()
                denm_message['management']['stationType'] = 10
                self.send_message('vanetza/in/denm', denm_message)
                # print(f'IN DENM -> OBU: {self.name} | MSG: {denm_message}\n')
            
            if self.is_on_node():
                self.change_edge('global')
            if self.finished:
                break
            self.coords = self.get_next_coords()
            time.sleep(1)
        
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

    def change_edge(self, type_of_search):
        if len(list(self.graph.successors(self.current_edge[1]))) == 0:
            self.finished = True
            return
        if type_of_search == 'local':
            successor_id = self.get_successor_min_distance()
            self.current_edge = (self.current_edge[1], successor_id)
        elif type_of_search == 'global':
            successor_id = self.best_path[self.best_path.index(self.current_edge[1]) + 1]
            self.current_edge = (self.current_edge[1], successor_id)
        self.coords = None

    def get_successor_min_distance(self):
        successors = list(self.graph.successors(self.current_edge[1]))
        min_distance = self.graph.get_edge_data(self.current_edge[1], successors[0])['attr']['distance']
        min_distance_successor = successors[0]
        for successor in successors:
            if self.graph.get_edge_data(self.current_edge[1], successor)['attr']['distance'] < min_distance:
                min_distance = self.graph.get_edge_data(self.current_edge[1], successor)['attr']['distance']
                min_distance_successor = successor
        return min_distance_successor

    # gets the best path based on the distance atribute of the edges
    def best_distance_path(self, destination_node):
        return nx.dijkstra_path(self.graph, self.current_edge[1], destination_node, weight='distance')

    def on_message(self, client, userdata, msg):
        message = json.loads(msg.payload.decode('utf-8'))
        msg_type = msg.topic

        # if msg_type == 'vanetza/out/denm':
        #     print(f'OUT DENM -> OBU: {self.name} | MSG: {message}\n')
                
            
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

    def move_obu(self):
        if Navigation.at_intersection(self.coords):
            self.current_route = self.set_route()
        self.coords = self.current_route.get_next_coords(self.coords)
        
    def set_route(self, route):
        self.current_route = route

    def get_coords(self):
        return self.coords
    
    def has_finished(self):
        return self.finished