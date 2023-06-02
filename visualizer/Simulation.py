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

    def __init__(self, situation=0):
        self.finished = True
        self.normal_obus = []
        self.special_obus = []
        self.rsus = []

        self.normal_obu_edges = []
        self.normal_obu_coordinates = []

        self.graph = nx.DiGraph()

        self.graph.add_node(0, attr={'latitude': 40.630573087421965, 'longitude': -8.654125928878786, 'connections': {1: (40.63162344496743, -8.654608726501467), 6: (40.6300466215235, -8.654799637383748), 9: (40.631306540191524, -8.652005912660032)}})
        self.graph.add_node(1, attr={'latitude': 40.63162344496743, 'longitude': -8.654608726501467, 'connections': {2: (40.63327629974076, -8.655552864074709), 3: (40.63222490781146, -8.65287555130587)}})
        self.graph.add_node(2, attr={'latitude': 40.63327629974076, 'longitude': -8.655552864074709, 'connections': {5: (40.63349808896788,-8.654745741573835)}})
        self.graph.add_node(3, attr={'latitude': 40.63222490781146, 'longitude': -8.65287555130587, 'connections': {1: (40.63162344496743, -8.654608726501467), 4: (40.63367391921257, -8.653817896059198)}})
        self.graph.add_node(4, attr={'latitude': 40.63367391921257, 'longitude': -8.653817896059198, 'connections': {5: (40.63349808896788,-8.654745741573835)}})
        self.graph.add_node(5, attr={'latitude': 40.63349808896788, 'longitude': -8.654745741573835, 'connections': {}})
        self.graph.add_node(6, attr={'latitude': 40.6300466215235, 'longitude': -8.654799637383748, 'connections': {7: (40.63187020342297,-8.657101544495264)}})
        self.graph.add_node(7, attr={'latitude': 40.63187020342297, 'longitude': -8.657101544495264, 'connections': {2: (40.63327629974076, -8.655552864074709)}})
        self.graph.add_node(8, attr={'latitude': 40.62975477416346, 'longitude': -8.653675317764284, 'connections': {0: (40.630573087421965, -8.654125928878786)}})
        self.graph.add_node(9, attr={'latitude': 40.631306540191524, 'longitude': -8.652005912660032, 'connections': {3: (40.63222490781146, -8.65287555130587)}})

        road1_coordinates = read_csv('coordinates/street1.csv')
        road2_coordinates = read_csv('coordinates/street2.csv')
        road3_coordinates = read_csv('coordinates/street3.csv')
        road4_coordinates = read_csv('coordinates/street4.csv')
        road5_coordinates = read_csv('coordinates/street5.csv')
        road6_coordinates = read_csv('coordinates/street6.csv')
        road7_coordinates = read_csv('coordinates/street7.csv')
        road8_coordinates = read_csv('coordinates/street8.csv')
        road9_coordinates = read_csv('coordinates/street9.csv')
        road10_coordinates = read_csv('coordinates/street10.csv')
        road11_coordinates = read_csv('coordinates/street11.csv')
        road12_coordinates = read_csv('coordinates/street12.csv')
        road13_coordinates = read_csv('coordinates/street13.csv')

        self.graph.add_edge(0, 1, attr={'list_of_coordinates':road1_coordinates, 'distance': 120, 'id': 1,'signalGroup': 1})
        self.graph.add_edge(1, 2, attr={'list_of_coordinates':road2_coordinates, 'distance': 200, 'id': 2 ,'signalGroup': 2})
        self.graph.add_edge(1, 3, attr={'list_of_coordinates':road5_coordinates, 'distance': 160, 'id': 5,'signalGroup': 3,})
        self.graph.add_edge(3, 1, attr={'list_of_coordinates':road13_coordinates, 'distance': 160, 'id': 13,'signalGroup': 3})
        self.graph.add_edge(3, 4, attr={'list_of_coordinates':road4_coordinates, 'distance': 180, 'id': 4,'signalGroup': 4})
        self.graph.add_edge(2, 5, attr={'list_of_coordinates':road3_coordinates, 'distance': 80, 'id': 3,'signalGroup': 5})
        self.graph.add_edge(4, 5, attr={'list_of_coordinates':road6_coordinates, 'distance': 80, 'id': 6,'signalGroup': 5})

        self.graph.add_edge(0, 6, attr={'list_of_coordinates':road7_coordinates, 'distance': 80, 'id': 7,'signalGroup': 6})
        self.graph.add_edge(6, 7, attr={'list_of_coordinates':road8_coordinates, 'distance': 270, 'id': 8,'signalGroup': 7})
        self.graph.add_edge(7, 2, attr={'list_of_coordinates':road9_coordinates, 'distance': 180, 'id': 9,'signalGroup': 8})
        self.graph.add_edge(8, 0, attr={'list_of_coordinates':road10_coordinates, 'distance': 100, 'id': 10,'signalGroup': 9})
        self.graph.add_edge(0, 9, attr={'list_of_coordinates':road11_coordinates, 'distance': 180, 'id': 11,'signalGroup': 10})
        self.graph.add_edge(9, 3, attr={'list_of_coordinates':road12_coordinates, 'distance': 120, 'id': 12,'signalGroup': 11})

        self.situation = situation

    def set_situation(self, situation):
        self.situation = situation

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
        self.special_obus.append(OBUEmergency('obu1', 5, '192.168.98.15', '6e:06:e0:03:00:05', 'obu1', 1, [40.62975477416346,-8.653675317764284], (8, 0), graph=self.graph))
        time.sleep(3)
        if self.situation == 0:
            # get n random coordinates from the random edges of the graph
            n = 5
            self.normal_obu_edges = []
            self.normal_obu_coordinates = []
            for i in range(n):
                # chose a random edge from the graph except the edge (8, 0)
                choice = random.choice(list(self.graph.edges))
                while choice == (8, 0):
                    choice = random.choice(list(self.graph.edges))
                self.normal_obu_edges.append(choice)
                # chose a random coordinate from the list of coordinates of the edge that was not chosen before and that is not the first neither the last coordinate of the edge
                coords_choice = random.choice(self.graph.edges[choice]['attr']['list_of_coordinates'][1:-1])
                while coords_choice in self.normal_obu_coordinates:
                    coords_choice = random.choice(self.graph.edges[choice]['attr']['list_of_coordinates'][1:-1])
                self.normal_obu_coordinates.append(coords_choice)

            self.normal_obus.append(OBUNormal('obu2', 6, '192.168.98.16', '6e:06:e0:03:00:06', 'obu2', 0, self.normal_obu_coordinates[0], self.normal_obu_edges[0], graph=self.graph, obu_emergency=self.special_obus[0]))
            self.normal_obus.append(OBUNormal('obu3', 7, '192.168.98.17', '6e:06:e0:03:00:07', 'obu3', 0, self.normal_obu_coordinates[1], self.normal_obu_edges[1], graph=self.graph, obu_emergency=self.special_obus[0]))
            self.normal_obus.append(OBUNormal('obu4', 8, '192.168.98.18', '6e:06:e0:03:00:08', 'obu4', 0, self.normal_obu_coordinates[2], self.normal_obu_edges[2], graph=self.graph, obu_emergency=self.special_obus[0]))
            self.normal_obus.append(OBUNormal('obu5', 9, '192.168.98.19', '6e:06:e0:03:00:09', 'obu5', 0, self.normal_obu_coordinates[3], self.normal_obu_edges[3], graph=self.graph, obu_emergency=self.special_obus[0]))
            self.normal_obus.append(OBUNormal('obu6', 10, '192.168.98.20', '6e:06:e0:03:00:10', 'obu6', 0, self.normal_obu_coordinates[4], self.normal_obu_edges[4], graph=self.graph, obu_emergency=self.special_obus[0]))
        elif self.situation == 1:
            self.normal_obu_edges = []
            self.normal_obu_coordinates = []
            self.normal_obu_edges = [(1,2) for i in range(3)]
            self.normal_obu_edges.append((0,1))
            self.normal_obu_edges.append((0,1))
            self.normal_obu_coordinates.append([40.631788100933775,-8.654704107656132])
            self.normal_obu_coordinates.append([40.632117412866464,-8.654894869965462])
            self.normal_obu_coordinates.append([40.63244672479915,-8.655085632274792])
            self.normal_obu_coordinates.append([40.630904133350626,-8.654311403031949])
            self.normal_obu_coordinates.append([40.63123517927929,-8.654496877185112])
            self.normal_obus.append(OBUNormal('obu2', 6, '192.168.98.16', '6e:06:e0:03:00:06', 'obu2', 0, self.normal_obu_coordinates[0], self.normal_obu_edges[0], graph=self.graph, obu_emergency=self.special_obus[0]))
            self.normal_obus.append(OBUNormal('obu3', 7, '192.168.98.17', '6e:06:e0:03:00:07', 'obu3', 0, self.normal_obu_coordinates[1], self.normal_obu_edges[1], graph=self.graph, obu_emergency=self.special_obus[0]))
            self.normal_obus.append(OBUNormal('obu4', 8, '192.168.98.18', '6e:06:e0:03:00:08', 'obu4', 0, self.normal_obu_coordinates[2], self.normal_obu_edges[2], graph=self.graph, obu_emergency=self.special_obus[0]))
            self.normal_obus.append(OBUNormal('obu5', 9, '192.168.98.19', '6e:06:e0:03:00:09', 'obu5', 0, self.normal_obu_coordinates[3], self.normal_obu_edges[3], graph=self.graph, obu_emergency=self.special_obus[0]))
            self.normal_obus.append(OBUNormal('obu6', 10, '192.168.98.20', '6e:06:e0:03:00:10', 'obu6', 0, self.normal_obu_coordinates[4], self.normal_obu_edges[4], graph=self.graph, obu_emergency=self.special_obus[0]))
        elif self.situation == 2:
            self.normal_obu_edges = []
            self.normal_obu_coordinates = []
            self.normal_obu_edges = [(3,4) for i in range(2)]
            self.normal_obu_edges.append((3,4))
            self.normal_obu_edges.append((0,1))
            self.normal_obu_edges.append((6,7))
            self.normal_obu_coordinates.append([40.632719474758346,-8.653154215551432])
            self.normal_obu_coordinates.append([40.63335577106116,-8.653596669223276])
            self.normal_obu_coordinates.append([40.63256040068264,-8.65304360213347])
            self.normal_obu_coordinates.append([40.630904133350626,-8.654311403031949])
            self.normal_obu_coordinates.append([40.63108398287046,-8.656127454414731])
            self.normal_obus.append(OBUNormal('obu2', 6, '192.168.98.16', '6e:06:e0:03:00:06', 'obu2', 0, self.normal_obu_coordinates[0], self.normal_obu_edges[0], graph=self.graph, obu_emergency=self.special_obus[0]))
            self.normal_obus.append(OBUNormal('obu3', 7, '192.168.98.17', '6e:06:e0:03:00:07', 'obu3', 0, self.normal_obu_coordinates[1], self.normal_obu_edges[1], graph=self.graph, obu_emergency=self.special_obus[0]))
            self.normal_obus.append(OBUNormal('obu4', 8, '192.168.98.18', '6e:06:e0:03:00:08', 'obu4', 0, self.normal_obu_coordinates[2], self.normal_obu_edges[2], graph=self.graph, obu_emergency=self.special_obus[0]))
            self.normal_obus.append(OBUNormal('obu5', 9, '192.168.98.19', '6e:06:e0:03:00:09', 'obu5', 0, self.normal_obu_coordinates[3], self.normal_obu_edges[3], graph=self.graph, obu_emergency=self.special_obus[0]))
            self.normal_obus.append(OBUNormal('obu6', 10, '192.168.98.20', '6e:06:e0:03:00:10', 'obu6', 0, self.normal_obu_coordinates[4], self.normal_obu_edges[4], graph=self.graph, obu_emergency=self.special_obus[0]))
            

        self.rsus.append(RSU('rsu1', 1, '192.168.98.11', '6e:06:e0:03:00:01', 'rsu1', [40.6334546665471, -8.654870575236478], special_vehicle=self.special_obus[0], current_edge=(4, 5), graph=self.graph, normal_obu_coordinates=self.normal_obu_coordinates))
        self.rsus.append(RSU('rsu2', 2, '192.168.98.12', '6e:06:e0:03:00:02', 'rsu2', [40.632412479977084, -8.65541774587554], special_vehicle=self.special_obus[0], current_edge=(1, 2), graph=self.graph, normal_obu_coordinates=self.normal_obu_coordinates))
        self.rsus.append(RSU('rsu3', 3, '192.168.98.13', '6e:06:e0:03:00:03', 'rsu3', [40.63198986375213, -8.653578792259104], special_vehicle=self.special_obus[0], current_edge=(1, 3), graph=self.graph, normal_obu_coordinates=self.normal_obu_coordinates))
        self.rsus.append(RSU('rsu4', 4, '192.168.98.14', '6e:06:e0:03:00:04', 'rsu4', [40.632942494084666, -8.653278384842281], special_vehicle=self.special_obus[0], current_edge=(3, 4), graph=self.graph, normal_obu_coordinates=self.normal_obu_coordinates))

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
        signal_group = {}
        paths_table = {}
        best_path = {}

        for obu in self.normal_obus:
            status[obu.name] = {'latitude': obu.coords[0], 'longitude': obu.coords[1]}
            pulled_over[obu.id] = obu.get_pulled_over()
            signal_group[obu.id] = obu.get_signal_group()
            # print(f"OBU {obu.id} -> {obu.get_signal_group()}")

        for obu in self.special_obus:
            status[obu.name] = {'latitude': obu.coords[0], 'longitude': obu.coords[1]}
            total_distance = obu.get_total_distance()
            total_cars = obu.get_total_cars()
            hybrid_punctuation = obu.get_hybrid_punctuation()
            best_path = obu.best_path

            for path in hybrid_punctuation:
                paths_table[path] = {
                    'total_distance' : total_distance[path],
                    'total_cars' : total_cars[path],
                    'hybrid_punctuation' : hybrid_punctuation[path]
                }

        for rsu in self.rsus:
            if rsu.id == 1:
                connections = rsu.get_connected()
        return status, connections, pulled_over, self.finished, self.normal_obu_coordinates ,signal_group, paths_table, best_path, self.graph_representation()
    
    def graph_representation(self):
        # initialize graph representation with node as key and attributes as value
        graph_representation = {}
        for node in self.graph.nodes:
            graph_representation[node] = {'coords': [self.graph.nodes[node]['attr']['latitude'], self.graph.nodes[node]['attr']['longitude']], 'connections': self.graph.nodes[node]['attr']['connections']}


        # print(self.graph.nodes)
        # print(nx.get_node_attributes(self.graph, 'attr'))

        return graph_representation

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