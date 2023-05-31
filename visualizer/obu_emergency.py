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
import json

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
        self.graph = graph
        self.current_edge = current_edge
        self.coords = None
        self.coords = self.get_next_coords()
        self.special_vehicle = special_vehicle
        self.best_path = self.best_distance_path(5)
        self.cars_on_lane = {}
        # get lane ids from self.graph and create a dict with lane id as key and an empty list as value
        for edge in self.graph.edges():
            id = self.graph.get_edge_data(*edge)['attr']['id']
            self.cars_on_lane[id] = []
        self.best_hybrid(5)

    def start(self):
        client = mqtt.Client(self.name)
        client.on_message = self.on_message
        client.connect(self.address, 1883, 60)
        client.subscribe(topic=[("vanetza/out/denm", 0)])
        client.subscribe(topic=[("vanetza/out/cam", 0)])
        client.loop_start()
        time.sleep(10)
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
                self.change_edge('hybrid')
            if self.finished:
                break
            self.coords = self.get_next_coords()
            time.sleep(3)
        
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
        elif type_of_search == 'congestion':
            successor_id = self.best_successor_congestion()
            self.current_edge = (self.current_edge[1], successor_id)
        elif type_of_search == 'hybrid':
            successor_id = self.best_hybrid(5)
            self.current_edge = (self.current_edge[1], successor_id)
        self.coords = None

    def best_hybrid(self, destination_node):
        # construct dict with the id of the lanes as keys and the number of cars on the lane as values
        number_of_cars_on_lane = {}
        for lane_id in self.cars_on_lane:
            number_of_cars_on_lane[lane_id] = len(self.cars_on_lane[lane_id])
        print(f'number_of_cars_on_lane: {number_of_cars_on_lane}')

        # compute the total distance on each path from all_paths and the total number of cars on each path
        total_distance = {}
        total_cars = {}
        for path in nx.all_simple_paths(self.graph, self.current_edge[1], destination_node):
            total_distance[str(path)] = 0
            total_cars[str(path)] = 0
            for i in range(len(path) - 1):
                total_distance[str(path)] += self.graph.get_edge_data(path[i], path[i + 1])['attr']['distance']
                total_cars[str(path)] += number_of_cars_on_lane[self.graph.get_edge_data(path[i], path[i + 1])['attr']['id']]
        print(f'total_distance: {total_distance}')
        print(f'total_cars: {total_cars}')

        # give a punctuation from 0 to 1 on the distance on each path
        total_distance_punctuation = {}
        for path in total_distance:
            total_distance_punctuation[path] = 1 - total_distance[path] / max(total_distance.values())

        # give a punctuation from 0 to 1 on the number of cars on each path
        total_cars_punctuation = {}
        for path in total_cars:
            if max(total_cars.values()) == 0:
                total_cars_punctuation[path] = 0
            else:
                total_cars_punctuation[path] = 1 - total_cars[path] / max(total_cars.values())

        # compute the hybrid punctuation
        hybrid_punctuation = {}
        for path in total_distance_punctuation:
            hybrid_punctuation[path] = total_distance_punctuation[path] * 0.3 + total_cars_punctuation[path] * 0.7
        print(f'hybrid_punctuation: {hybrid_punctuation}')
        # get the path with the highest hybrid punctuation
        best_path_key_str = max(hybrid_punctuation, key=hybrid_punctuation.get)
        self.best_path = json.loads(best_path_key_str)
        print(f'best_path: {self.best_path}')
        return self.best_path[1]

    def best_successor_congestion(self):
        # construct dict with the id of the lanes as keys and the number of cars on the lane as values
        number_of_cars_on_lane = {}
        for lane_id in self.cars_on_lane:
            number_of_cars_on_lane[lane_id] = len(self.cars_on_lane[lane_id])
        # get the successor with the least number of cars
        successors = list(self.graph.successors(self.current_edge[1]))
        min_cars = number_of_cars_on_lane[self.graph.get_edge_data(self.current_edge[1], successors[0])['attr']['id']]
        min_cars_successor = successors[0]
        for successor in successors:
            if number_of_cars_on_lane[self.graph.get_edge_data(self.current_edge[1], successor)['attr']['id']] < min_cars:
                min_cars = number_of_cars_on_lane[self.graph.get_edge_data(self.current_edge[1], successor)['attr']['id']]
                min_cars_successor = successor
        return min_cars_successor

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

        if msg_type == 'vanetza/out/cam':
            if message['stationID'] != self.id and message['stationType'] != 15:    #  CAM messages received from other OBUs
                # print(f"OUT CAM sender ( {message['stationID']} ) OBU: {self.name} | MSG: {message}\n")
                cam_latitude = message['latitude']
                cam_longitude = message['longitude']

                if self.get_lane_from_coords((cam_latitude, cam_longitude)) is not None:
                    if message['stationID'] not in self.cars_on_lane[self.get_lane_from_coords((cam_latitude, cam_longitude))]:
                        self.cars_on_lane[self.get_lane_from_coords((cam_latitude, cam_longitude))].append(message['stationID'])

    def get_lane_from_coords(self, coords):
        for edge in self.graph.edges():
            # aux is a list of self.graph.get_edge_data(*edge)['attr']['list_of_coordinates'] with the coordinates concatenated to only 7 decimal places with floor if the latitude is positive and ceil if the latitude is negative and the same for the longitude
            aux = self.convert_list_of_coordinates_to_list_of_coordinates_with_7_decimal_places(self.graph.get_edge_data(*edge)['attr']['list_of_coordinates'])
            if coords in aux:
                return self.graph.get_edge_data(*edge)['attr']['id']
            elif [coords[0]+0.0000001, coords[1]] in aux:
                return self.graph.get_edge_data(*edge)['attr']['id']
            elif [coords[0]-0.0000001, coords[1]] in aux:
                return self.graph.get_edge_data(*edge)['attr']['id']
            elif [coords[0], coords[1]+0.0000001] in aux:
                return self.graph.get_edge_data(*edge)['attr']['id']
            elif [coords[0], coords[1]-0.0000001] in aux:
                return self.graph.get_edge_data(*edge)['attr']['id']
        return None
    
    def convert_list_of_coordinates_to_list_of_coordinates_with_7_decimal_places(self, list_of_coordinates):
        aux = []
        for coordinate in list_of_coordinates:
            tmp = []
            for x in coordinate:
                if x < 0:
                    tmp.append(math.ceil(x*10000000)/10000000)
                else:
                    tmp.append(math.floor(x*10000000)/10000000)
            aux.append(tuple(tmp))
        return aux
            
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
            10,
            self.width,
            0
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