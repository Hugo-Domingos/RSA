from intersection import Intersection
from route import Route


class Navigation:
    def __init__(self):
        self.route1 = Route('coordinates/street1.csv')
        self.route2 = Route('coordinates/street2.csv')
        self.intersection12 = Intersection([40.63325278264807,-8.655772891406016], [self.route1, self.route2])

    def iterate_over_route(self, route, current_coords):
        self.get_next_coords(route, current_coords)

    def get_next_coords(self, route, current_coords):
        return route.get_next_coords(current_coords)

    def at_intersection(self, current_coords):
        return current_coords == self.intersection12.get_coords()

    def change_route(self, current_route):
        return self.route1