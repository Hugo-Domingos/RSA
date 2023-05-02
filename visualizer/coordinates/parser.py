# POINT (40.63326016838951 -8.655699323271294)
# POINT (40.633773903580064 -8.653916806982412)

import csv
from geopy import distance

point1 = (40.63073684373091,-8.65419575254765)
point2 = (40.63325278264807,-8.655772891406016)

def interpolate(point1, point2, distance_interval):
    delta_x = point2[0] - point1[0]
    delta_y = point2[1] - point1[1]

    # calculate how many steps to get the points each distance_interval meters apart
    street_distance = distance.distance(point1, point2).meters
    steps = int(street_distance / distance_interval)

    return [(point1[0] + i * delta_x / steps, point1[1] + i * delta_y / steps) for i in range(steps)]

res = interpolate(point1, point2, 10)
res.append(point2)
print(res)

 
# field names
fields = ['latitude', 'longitude']
 
# data rows of csv file
rows = res
 
# name of csv file
filename = "street2.csv"
 
# writing to csv file
with open(filename, 'w') as csvfile:
    # creating a csv writer object
    csvwriter = csv.writer(csvfile)
     
    # writing the fields
    csvwriter.writerow(fields)
     
    # writing the data rows
    csvwriter.writerows(rows)
