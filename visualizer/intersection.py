class Intersection:
    def __init__(self, coords, connections):
        self.coords = coords
        self.connections = connections

    def add_connection(self, connection):
        self.connections.append(connection)
    
    def get_connections(self):
        return self.connections
    
    def get_coords(self):
        return self.coords