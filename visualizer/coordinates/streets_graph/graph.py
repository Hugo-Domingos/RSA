import networkx as nx

class Coordinate:
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

class Road:
    def __init__(self, id, start, end, list_of_coordinates):
        self.id = id
        self.start = start
        self.end = end
        self.list_of_coordinates = list_of_coordinates
    
    def __str__(self) -> str:
        return f'[ROAD]: {self.start} -> {self.end}'


class Intersection:
    def __init__(self, id, latitude, longitude):
        self.id = id
        self.latitude = latitude
        self.longitude = longitude
        self.connections = {}

    def add_connection(self, road_id, connection_point):
        self.connections[road_id] = connection_point

    def __str__(self) -> str:
        return f'[INTERSECTION]: {self.latitude}, {self.longitude}'

class RoadNetwork:
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_road(self, road):
        self.graph.add_edge((road.start.latitude, road.start.longitude), (road.end.latitude, road.end.longitude), coordinates=road.list_of_coordinates)

    def add_intersection(self, intersection):
        self.graph.add_node((intersection.latitude, intersection.longitude), id=intersection.id, connections=intersection.connections)

    def __str__(self) -> str:
        return f'[ROAD NETWORK]: {self.graph} | Number of nodes: {self.graph.number_of_nodes()} | Number of edges: {self.graph.number_of_edges()}'

def read_csv(filename):
    res = []
    with open(filename, 'r') as f:
        for line in f:
            res.append(line.strip().split(','))
    return res

def to_coordinate_list(list_of_coordinates):
    res = []
    for coordinate in list_of_coordinates:
        res.append(Coordinate(float(coordinate[0]), float(coordinate[1])))
    return res

def csv_to_road(filename, id):
    road_points = read_csv(filename)
    road = Road(id=id, start=Coordinate(float(road_points[0][0]), float(road_points[0][1])), end=Coordinate(float(road_points[-1][0]), float(road_points[-1][1])), list_of_coordinates=road_points)
    return road

def main():
    road1 = csv_to_road('street1.csv', 1)
    road2 = csv_to_road('street2.csv', 2)
    road3 = csv_to_road('street3.csv', 3)
    road4 = csv_to_road('street4.csv', 4)
    road5 = csv_to_road('street5.csv', 5)

    road_network = RoadNetwork()

    road_network.add_road(road1)
    road_network.add_road(road2)
    road_network.add_road(road3)
    road_network.add_road(road4)
    road_network.add_road(road5)

    intersection0 = Intersection(id=0, latitude=40.63159901823542, longitude=-8.654694557189943)
    intersection1 = Intersection(id=1, latitude=40.63162344496743, longitude=-8.654608726501467)
    road_network.add_intersection(intersection=intersection0)
    intersection0.add_connection(road_id=2, connection_point=road2.start)
    road_network.add_intersection(intersection=intersection1)
    

if __name__ == '__main__':
    main()