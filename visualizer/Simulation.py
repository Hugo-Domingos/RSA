import random
import subprocess
import threading
import time
from obu_emergency import OBUEmergency
from obu_normal import OBUNormal
from route import Route
from rsu import RSU
from graph import RoadNetwork, csv_to_road, Intersection, read_csv
import networkx as nx

class Simulation:

    def __init__(self):
        self.finished = True
        self.normal_obus = []
        self.special_obus = []
        self.rsus = []

        self.random_edges = []
        self.random_coordinates = []

        self.graph = nx.DiGraph()

        self.graph.add_node(0, attr={'latitude': 40.630573087421965, 'longitude': -8.654125928878786, 'connections': {1: (40.63162344496743, -8.654608726501467), 3: (40.63162344496743, -8.654597997665407)}})
        self.graph.add_node(1, attr={'latitude': 40.63162344496743, 'longitude': -8.654608726501467, 'connections': {2: (40.63327629974076, -8.655552864074709)}})
        self.graph.add_node(2, attr={'latitude': 40.63327629974076, 'longitude': -8.655552864074709, 'connections': {5: (40.63349808896788,-8.654745741573835)}})
        self.graph.add_node(3, attr={'latitude': 40.63162344496743, 'longitude': -8.654597997665407, 'connections': {4: (40.63367391921257, -8.653817896059198)}})
        self.graph.add_node(4, attr={'latitude': 40.63367391921257, 'longitude': -8.653817896059198, 'connections': {5: (40.63349808896788,-8.654745741573835)}})
        self.graph.add_node(5, attr={'latitude': 40.63349808896788, 'longitude': -8.654745741573835, 'connections': {}})
        
        road1_coordinates = read_csv('coordinates/street1.csv')
        road2_coordinates = read_csv('coordinates/street2.csv')
        road3_coordinates = read_csv('coordinates/street3.csv')
        road4_coordinates = read_csv('coordinates/street4.csv')
        road5_coordinates = read_csv('coordinates/street5.csv')
        road6_coordinates = read_csv('coordinates/street6.csv')

        self.graph.add_edge(0, 1, attr={'list_of_coordinates':road1_coordinates, 'distance': 120, 'id': 1,'signalGroup': 1})
        self.graph.add_edge(1, 2, attr={'list_of_coordinates':road2_coordinates, 'distance': 200, 'id': 2 ,'signalGroup': 2})
        self.graph.add_edge(1, 3, attr={'list_of_coordinates':road5_coordinates, 'distance': 160, 'id': 5,'signalGroup': 3})
        self.graph.add_edge(3, 4, attr={'list_of_coordinates':road4_coordinates, 'distance': 180, 'id': 4,'signalGroup': 4})
        self.graph.add_edge(2, 5, attr={'list_of_coordinates':road3_coordinates, 'distance': 80, 'id': 3,'signalGroup': 5})
        self.graph.add_edge(4, 5, attr={'list_of_coordinates':road6_coordinates, 'distance': 80, 'id': 6,'signalGroup': 5})


    def at_node(self, current_coords):
        for node in self.graph.nodes:
            if self.graph.nodes[node]['latitude'] == current_coords[0] and self.graph.nodes[node]['longitude'] == current_coords[1]:
                return node
        return None

    def run(self):
        self.finished = False
        process = subprocess.Popen("docker-compose up -d", shell=True)
        process.wait()

        subprocess.run("docker ps", shell=True, check=True)
        self.special_obus.append(OBUEmergency('obu1', 5, '192.168.98.15', '6e:06:e0:03:00:05', 'obu1', 1, [40.630573087421965, -8.654125928878786], (0,1), graph=self.graph))
        time.sleep(3)
        print("GRAPH")
        print(self.graph)
        # get n random coordinates from the random edges of the graph
        n = 5
        self.random_edges = []
        self.random_coordinates = []
        for i in range(n):
            self.random_edges.append(random.choice(list(self.graph.edges)))
            self.random_coordinates.append(random.choice(self.graph.edges[self.random_edges[i]]['attr']['list_of_coordinates']))

        self.normal_obus.append(OBUNormal('obu2', 6, '192.168.98.16', '6e:06:e0:03:00:06', 'obu2', 0, self.random_coordinates[0], self.random_edges[0], graph=self.graph, obu_emergency=self.special_obus[0]))
        self.normal_obus.append(OBUNormal('obu3', 7, '192.168.98.17', '6e:06:e0:03:00:07', 'obu3', 0, self.random_coordinates[1], self.random_edges[1], graph=self.graph, obu_emergency=self.special_obus[0]))
        self.normal_obus.append(OBUNormal('obu4', 8, '192.168.98.18', '6e:06:e0:03:00:08', 'obu4', 0, self.random_coordinates[2], self.random_edges[2], graph=self.graph, obu_emergency=self.special_obus[0]))
        self.normal_obus.append(OBUNormal('obu5', 9, '192.168.98.19', '6e:06:e0:03:00:09', 'obu5', 0, self.random_coordinates[3], self.random_edges[3], graph=self.graph, obu_emergency=self.special_obus[0]))
        self.normal_obus.append(OBUNormal('obu6', 10, '192.168.98.20', '6e:06:e0:03:00:10', 'obu6', 0, self.random_coordinates[4], self.random_edges[4], graph=self.graph, obu_emergency=self.special_obus[0]))

        self.rsus.append(RSU('rsu1', 1, '192.168.98.11', '6e:06:e0:03:00:01', 'rsu1', [40.6334546665471, -8.654870575236478], special_vehicle=self.special_obus[0], current_edge=(4, 5), graph=self.graph))
        # self.rsus.append(RSU('rsu2', 2, '192.168.98.12', '6e:06:e0:03:00:02', 'rsu2', [40.632412479977084, -8.65541774587554], special_vehicle=self.special_obus[0]))
        # self.rsus.append(RSU('rsu3', 3, '192.168.98.13', '6e:06:e0:03:00:03', 'rsu3', [40.63198986375213, -8.653578792259104], special_vehicle=self.special_obus[0]))
        # self.rsus.append(RSU('rsu4', 4, '192.168.98.14', '6e:06:e0:03:00:04', 'rsu4', [40.632942494084666, -8.653278384842281], special_vehicle=self.special_obus[0]))

        rsu_threads = []
        for i in range(0, len(self.rsus)):
            rsu_threads.append(threading.Thread(target=self.rsus[i].start))
            rsu_threads[i].start()

        special_obu_threads = []
        for i in range(0, len(self.special_obus)):
            special_obu_threads.append(threading.Thread(target=self.special_obus[i].start))
            special_obu_threads[i].start()

        normal_obu_threads = []
        for i in range(0, len(self.normal_obus)):
            normal_obu_threads.append(threading.Thread(target=self.normal_obus[i].start))
            normal_obu_threads[i].start()

        for thread in rsu_threads:
            thread.join()
        self.rsus = []

        for thread in special_obu_threads:
            thread.join()
        self.special_obus = []

        for thread in normal_obu_threads:
            thread.join()
        self.normal_obus = []

        self.kill_simulation()

        process = subprocess.Popen("docker-compose down", shell=True)
        process.wait()
        print("Simulation finished")

    def get_status(self):
        status = {}
        connections = {}
        pulled_over = {}
        for obu in self.normal_obus:
            status[obu.name] = {'latitude': obu.coords[0], 'longitude': obu.coords[1]}
            pulled_over[obu.id] = obu.get_pulled_over()

        for obu in self.special_obus:
            status[obu.name] = {'latitude': obu.coords[0], 'longitude': obu.coords[1]}

        for rsu in self.rsus:
            connections = rsu.get_connected()

        return status, connections, pulled_over, self.finished, self.random_coordinates

    def kill_simulation(self):
        for obu in self.normal_obus:
            obu.set_finished(True)
        for obu in self.special_obus:
            obu.set_finished(True)
        for rsu in self.rsus:
            rsu.set_finished(True)
        # process = subprocess.Popen("docker-compose down", shell=True)
        # process.wait()
        self.finished = True
    
    
if __name__ == '__main__':
    s = Simulation()
    s.run()