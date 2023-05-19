import threading
from obu import OBU
from route import Route
from rsu import RSU
from graph import RoadNetwork, csv_to_road, Intersection, read_csv
import networkx as nx

class Simulation:
    # obus = []

    def __init__(self):
        self.obus = []
        self.rsus = []

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

        self.graph.add_edge(0, 1, attr={'list_of_coordinates':road1_coordinates, 'distance': 120})
        self.graph.add_edge(1, 2, attr={'list_of_coordinates':road2_coordinates, 'distance': 200})
        self.graph.add_edge(1, 3, attr={'list_of_coordinates':road5_coordinates, 'distance': 160})
        self.graph.add_edge(3, 4, attr={'list_of_coordinates':road4_coordinates, 'distance': 180})
        self.graph.add_edge(2, 5, attr={'list_of_coordinates':road3_coordinates, 'distance': 80})
        self.graph.add_edge(4, 5, attr={'list_of_coordinates':road6_coordinates, 'distance': 80})
        print(self.graph)
        print(self.graph.nodes)
        print(self.graph.edges)


    def at_node(self, current_coords):
        for node in self.graph.nodes:
            if self.graph.nodes[node]['latitude'] == current_coords[0] and self.graph.nodes[node]['longitude'] == current_coords[1]:
                return node
        return None

    def run(self):
        self.rsus.append(RSU('rsu1', 1, '192.168.98.10', 'rsu1', [40.6334546665471, -8.654870575236478]))
        self.rsus.append(RSU('rsu2', 2, '192.168.98.40', 'rsu2', [40.632412479977084, -8.65541774587554]))
        self.rsus.append(RSU('rsu3', 3, '192.168.98.50', 'rsu3', [40.63198986375213, -8.653578792259104]))
        self.rsus.append(RSU('rsu4', 4, '192.168.98.60', 'rsu4', [40.632942494084666, -8.653278384842281]))

        self.obus.append(OBU('obu1', 1, '192.168.98.20', 'obu1', 1, [40.630573087421965, -8.654125928878786], (0,1), graph=self.graph))
        self.obus.append(OBU('obu2', 2, '192.168.98.30', 'obu2', 0, [40.63349808896788, -8.654745741573835], (4,5), graph=self.graph))

        rsu_threads = []
        for i in range(0, len(self.rsus)):
            rsu_threads.append(threading.Thread(target=self.rsus[i].start))
            rsu_threads[i].start()
        
        obu_threads = []
        for i in range(0, len(self.obus)):
            obu_threads.append(threading.Thread(target=self.obus[i].start))
            obu_threads[i].start()

        for thread in rsu_threads:
            thread.join()
        self.rsus = []

        for thread in obu_threads:
            thread.join()
        self.obus = []

    def get_status(self):
        status = {}
        for obu in self.obus:
            status[obu.name] = {'latitude': obu.coords[0], 'longitude': obu.coords[1]}
        return status

    def kill_simulation(self):
        for obu in self.obus:
            obu.set_finished(True)
        for rsu in self.rsus:
            rsu.set_finished(True)
    
    
if __name__ == '__main__':
    s = Simulation()
    s.run()