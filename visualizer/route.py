import csv

class Route:
    def __init__(self, filename):
        self.filename = filename
        self.coords_list = []
        with open(filename, 'r') as f:
            for line in f:
                self.coords_list.append(line.strip().split(','))
                self.coords_list[-1][0] = float(self.coords_list[-1][0])
                self.coords_list[-1][1] = float(self.coords_list[-1][1])
        print(self.coords_list)

    def get_coords(self):
        return self.coords_list
    
    def get_next_coords(self, current_coords):
        print(self.filename)
        if current_coords == None:
            return self.coords_list[0]
        return self.coords_list[self.coords_list.index(current_coords) + 1]
    