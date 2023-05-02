import csv

class Route:
    def __init__(self, filename):
        self.filename = filename
        self.coords_list = []
        # read csv file with header "latitude,longitude" and return a list of coordinates
        # ignore the first line of the file
        with open(self.filename, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.coords_list.append([float(row['latitude']), float(row['longitude'])])
        print(self.coords_list)

    def get_coords(self):
        return self.coords_list
    
    def get_next_coords(self, current_coords):
        print(self.filename)
        if current_coords == None:
            return self.coords_list[0]
        return self.coords_list[self.coords_list.index(current_coords) + 1]
    