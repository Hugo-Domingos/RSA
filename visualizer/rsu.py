from itertools import permutations
import subprocess
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import time
import cam
import denm
import json

import json
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import geopy.distance
import time
import cam
import denm
from navigation import Navigation
import math
import networkx as nx

connected = {
    2 : {
        2 : True,
        3 : True,
        7 : True,
    },
    3 : {
        2 : True,
        3 : True,
        7 : True,
    },
    7 : {
        2 : True,
        3 : True,
        7 : True,
    },
}

class RSU:
    def __init__(self, name, id, address, mac_address, rsu, coords, special_vehicle, current_edge, graph):
        self.name = name
        self.id = id
        self.address = address
        self.mac_address = mac_address
        self.rsu = rsu
        self.finished = False
        self.length = 4.5
        self.width = 1.8
        # self.route = route
        self.coords = coords
        self.special_vehicle = special_vehicle
        #to be removed
        self.speed = 0
        self.current_edge = current_edge
        self.graph = graph

        self.received_obu_coordinates = {
            2: {'coords': [], 'mac': '6e:06:e0:03:00:02', 'name': 'obu1'},
            3: {'coords': [], 'mac': '6e:06:e0:03:00:03', 'name': 'obu2'},
            7: {'coords': [], 'mac': '6e:06:e0:03:00:07', 'name': 'obu3'}
        }

    def start(self):
        client = mqtt.Client(self.name)
        client.on_message = self.on_message
        client.connect(self.address, 1883, 60)
        client.subscribe(topic=[("vanetza/out/cam", 0)])
        client.subscribe(topic=[("vanetza/out/denm", 0)])
        client.loop_start()

        while not self.finished:
            if self.special_vehicle.has_finished():
                self.finished = True
                break
            # if self.id == 1:
            #     self.check_ranges()
            cam_message = self.generate_cam()
            self.send_message('vanetza/in/cam', cam_message)
            # print(f'IN -> RSU: {self.name} | MSG: {cam_message}\n')
            time.sleep(1)
        
        # end the client
        client.loop_stop()
        client.disconnect()
        

    def on_message(self, client, userdata, msg):
        message = json.loads(msg.payload.decode('utf-8'))
        msg_type = msg.topic
        # print(f'IN -> RSU: {self.name} | MSG: {msg_type}\n')
        if msg_type == 'vanetza/out/cam':
            # print(f"OUT CAM -> RSU: {self.name} | stationID: {message['stationID']} | MSG: {message}\n")
            if self.id == 1 and message['stationID'] in self.received_obu_coordinates.keys():
                self.received_obu_coordinates[message['stationID']]['coords'] =[message['latitude'], message['longitude']]


        elif msg_type == 'vanetza/out/denm':
            # denm=self.generate_denm()
            # denm["management"]["stationType"]=15
            # self.send_message('vanetza/in/denm', denm)
            # spt=self.generate_spatem(1,[1,2,3,4],[1,2,3,4])
            # print(f'OUT DENM -> RSU: {self.name} | MSG: {message}\n')
            # self.send_message('vanetza/in/spatem',spt)

            pass

    def generate_cam(self):
        cam_message = cam.CAM(
            True,
            10.0,
            0,
            0,
            False,
            True,
            True,
            0,
            "FORWARD",
            False,
            True,
            0,
            0,
            self.coords[0],
            self.length,
            self.coords[1],
            0,
            0,
            0,
            cam.SpecialVehicle(cam.PublicTransportContainer(False)),
            self.speed,
            0,
            True,
            self.id,
            15,
            self.width,
            0
        )
        return cam.CAM.to_dict(cam_message)
    
     
    def generate_denm(self):
        denm_message = denm.DENM(
            denm.Management(
                denm.ActionID(1798587532,0),
                0.0,
                0.0,
                denm.EventPosition(self.coords[0], self.coords[1], 
                denm.PositionConfidenceEllipse(0,0,0), 
                denm.Altitude(0,0)),
                0,
                0
            ),
            denm.Situation(7,denm.EventType(14,14))
        )
        return denm.DENM.to_dict(denm_message)

    def send_message(self, topic, message):
        publish.single(topic, json.dumps(message), hostname=self.address)

    def set_finished(self, value):
        self.finished = value
    
    def generate_spatem(self,id,state,signalgroup):
        ##generate spatem message with id and signalGroups as input
        spatem={
            "intersections":[
                {
                    "id":{
                        "id":id
                    },
                    "revision":1,
                    "states":[
                        
                    ],
                    "status":{
                        "failureFlash": False,
                        "failureMode": False,
                        "fixedTimeOperation": False,
                        "manualControlIsEnabled": False,
                        "noValidMAPisAvailableAtThisTime": False,
                        "noValidSPATisAvailableAtThisTime": False,
                        "off": False,
                        "preemptIsActive": False,
                        "recentChangeInMAPassignedLanesIDsUsed": False,
                        "recentMAPmessageUpdate": False,
                        "signalPriorityIsActive": False,
                        "standbyOperation": False,
                        "stopTimeIsActivated": False,
                        "trafficDependentOperation": False
                    }

                }
            ]
        }

        # for each signal group append to the states list in the spatem message
        for i in range(len(signalgroup)):
            spatem["intersections"][0]["states"].append(
                {
                    "signalGroup":signalgroup[i],
                    "state-time-speed":[
                        {
                            "eventState":state[i],
                            "timing":{
                                "minEndTime":28342
                            }
                        }
                    ]
                }
            )

        print(spatem)
        return spatem


    def check_ranges(self):
        ids = list(self.received_obu_coordinates.keys())
        pairs = permutations(ids, 2)
        '''
        connected = {
            'id1': {
                'id1': False,
                'id2': True,
                'id3': False,
                'id4': True
            },
            'id2': {
                'id1': True,
                'id2': False,
                'id3': False,
                'id4': True
            },
            'id3': {
                'id1': False,
                'id2': False,
                'id3': False,
                'id4': False
            },
            'id4': {
                'id1': True,
                'id2': True,
                'id3': False,
                'id4': False
            }
        }
        '''
        for pair in pairs:
            id1, id2 = pair
            coord1 = self.received_obu_coordinates[id1]['coords']
            coord2 = self.received_obu_coordinates[id2]['coords']
            global connected
            if coord1 != [] and coord2 != []:
                distance = geopy.distance.distance(coord1, coord2).m
                if distance < 80 and not connected[id1][id2]:
                    # print(f'RSU: {self.name} | OBU: {id1} and OBU: {id2} are in range\n')
                    subprocess.run(f"docker-compose exec {self.received_obu_coordinates[id1]['name']} unblock {self.received_obu_coordinates[id2]['mac']}", shell=True, check=True)
                    connected[id1][id2] = True
                elif distance > 80 and connected[id1][id2]:
                    # print(f'RSU: {self.name} | OBU: {id1} and OBU: {id2} are not in range\n')
                    subprocess.run(f"docker-compose exec {self.received_obu_coordinates[id1]['name']} block {self.received_obu_coordinates[id2]['mac']}", shell=True, check=True)
                    # print(f"docker-compose exec {self.received_obu_coordinates[id1]['name']} block {self.received_obu_coordinates[id2]['mac']}")
                    connected[id1][id2] = False
            else:
                # print(f'RSU: {self.name} | OBU: {id1} and OBU: {id2} are not in range\n')
                subprocess.run(f"docker-compose exec {self.received_obu_coordinates[id1]['name']} block {self.received_obu_coordinates[id2]['mac']}", shell=True, check=True)
                # print(f"docker-compose exec {self.received_obu_coordinates[id1]['name']} block {self.received_obu_coordinates[id2]['mac']}")
                connected[id1][id2] = False
    
    def get_connected(self):
        global connected
        return connected