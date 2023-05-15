import json
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import time
import cam
from navigation import Navigation
import networkx as nx

class OBU:
    def __init__(self, name, id, address, obu, special_vehicle, coords, current_edge, graph):
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
        # self.current_route = starting_route
        # self.coords = self.navigation.get_next_coords(self.current_route, None)
        # self.coords = self.current_route.get_next_coordinates(None)
        self.graph = graph
        self.current_edge = current_edge
        self.coords = None
        self.coords = self.get_next_coords()
        self.special_vehicle = special_vehicle
        # self.road_network = road_network

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

            if self.is_on_node():
                self.change_edge()
            if self.finished:
                break
            self.coords = self.get_next_coords()
            print(f'Coords: {self.coords}')
            time.sleep(1)
        
        # end the client
        client.loop_stop()
        client.disconnect()
    
    def get_next_coords(self):
        print(self.current_edge)
        print( self.graph.get_edge_data(*self.current_edge)['attr']['list_of_coordinates'] )
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
        if len(list(self.graph.successors(self.current_edge[1]))) == 0:
            self.finished = True
            return
        successor_id = self.get_successor_min_distance()
        print(f'Successor id: {successor_id}')
        self.current_edge = (self.current_edge[1], successor_id)
        self.coords = None
        # successors = list(self.graph.successors(self.current_edge[1]))
        # print(f'Successors: {successors}')
        # self.current_edge = (self.current_edge[1], successors[-1])
        # print(f'Current edge: {self.current_edge}')
        # self.coords = None

    def get_successor_min_distance(self):
        successors = list(self.graph.successors(self.current_edge[1]))
        print(f'Successors: {successors}')
        min_distance = self.graph.get_edge_data(self.current_edge[1], successors[0])['attr']['distance']
        min_distance_successor = successors[0]
        for successor in successors:
            if self.graph.get_edge_data(self.current_edge[1], successor)['attr']['distance'] < min_distance:
                min_distance = self.graph.get_edge_data(self.current_edge[1], successor)['attr']['distance']
                min_distance_successor = successor
        return min_distance_successor

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