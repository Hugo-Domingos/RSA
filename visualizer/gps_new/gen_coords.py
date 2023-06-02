from geopy import Point
from geopy.distance import distance

lat1 = 40.630604352538114
lon1 = -8.654127027854887
distMiles = 0.1
bearing = -24.572
# given: lat1, lon1, bearing, distMiles
lat2,lon2,_ = distance(miles=distMiles).destination((lat1, lon1), bearing)

