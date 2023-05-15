import networkx as nx
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

class Coordinate:
    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

class Road:
    def __init__(self, id, start, end, list_of_coordinates):
        self.id = id
        self.start = start
        print(self.start)
        self.end = end
        print(self.end)
        self.list_of_coordinates = list_of_coordinates

    def get_next_coordinates(self, current_coords):
        if current_coords == None:
            return self.list_of_coordinates[0]
        return self.list_of_coordinates[self.list_of_coordinates.index(current_coords) + 1]
    
    def is_end(self, current_coords):
        if current_coords == None:
            return False
        return self.list_of_coordinates.index(current_coords) == len(self.list_of_coordinates) - 1

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

    def add_road(self, road, start_intersection, end_intersection):
        self.graph.add_edge(start_intersection, end_intersection, attr={'start_coords':(road.start.latitude, road.start.longitude), 'end_coords':(road.end.latitude, road.end.longitude), 'list_of_coordinates':road.list_of_coordinates})

    def add_intersection(self, intersection):
        self.graph.add_node(intersection.id, attr={'latitude': intersection.latitude, 'longitude': intersection.longitude, 'connections': intersection.connections})
    
    def decide_new_road(self, current_road):
        print(f'Current road: {current_road.id}')
        print(f'Current road end: {current_road.end}')
        intersection_id = list(self.graph[current_road.end.id].keys())[0]
        print(f'Intersection: {intersection_id}')
        connections = self.graph.nodes[intersection_id]
        print(f'Connections: {connections}')
        
        print( self.graph.nodes[list(connections.keys())[0]] )

    def plot_road_network(self):
        # create a cartopy projection using Plate Carree (a cylindrical projection)
        proj = ccrs.PlateCarree()

        # create a plot with coastlines and political boundaries
        fig, ax = plt.subplots(subplot_kw={'projection': proj})
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS, linestyle=':')

        # plot the edges
        for u, v, data in self.graph.edges(data=True):
            latitudes = [data['attr']['start_coords'][0], data['attr']['end_coords'][0]]
            longitudes = [data['attr']['start_coords'][1], data['attr']['end_coords'][1]]
            ax.plot(longitudes, latitudes, transform=proj)

        # plot the nodes
        for node, data in self.graph.nodes(data=True):
            ax.plot(data['attr']['longitude'], data['attr']['latitude'], 'ro', markersize=10, transform=proj)

        # show the plot
        plt.show()

    def __str__(self) -> str:
        return f'[ROAD NETWORK]: {self.graph} \n NODES: {self.graph.nodes} \n EDGES: {self.graph.edges}\n'

def read_csv(filename):
    res = []
    with open(filename, 'r') as f:
        for line in f:
            aux = line.strip().split(',')
            res.append([float(aux[0]), float(aux[1])])
    return res

def to_coordinate_list(list_of_coordinates):
    res = []
    for coordinate in list_of_coordinates:
        res.append(Coordinate(float(coordinate[0]), float(coordinate[1])))
    return res

def csv_to_road(filename, id, intersection_start=None, intersection_end=None):
    road_points = read_csv(filename)
    # road = Road(id=id, start=Coordinate(float(road_points[0][0]), float(road_points[0][1])), end=Coordinate(float(road_points[-1][0]), float(road_points[-1][1])), list_of_coordinates=road_points)
    road = Road(id=id, start=intersection_start, end=intersection_end, list_of_coordinates=to_coordinate_list(road_points))
    return road

# def main():
#     road1 = csv_to_road('coordinates/street1.csv', 1)
#     road2 = csv_to_road('coordinates/street2.csv', 2)
#     road3 = csv_to_road('coordinates/street3.csv', 3)
#     road4 = csv_to_road('coordinates/street4.csv', 4)
#     road5 = csv_to_road('coordinates/street5.csv', 5)

#     road_network = RoadNetwork()

#     road_network.add_road(road1)
#     road_network.add_road(road2)
#     road_network.add_road(road3)
#     road_network.add_road(road4)
#     road_network.add_road(road5)

#     intersection0 = Intersection(id=0, latitude=40.63159901823542, longitude=-8.654694557189943)
#     intersection1 = Intersection(id=1, latitude=40.63162344496743, longitude=-8.654608726501467)
#     road_network.add_intersection(intersection=intersection0)
#     intersection0.add_connection(road_id=2, connection_point=road2.start)
#     road_network.add_intersection(intersection=intersection1)
    

# if __name__ == '__main__':
#     main()