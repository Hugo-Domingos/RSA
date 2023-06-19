from itertools import permutations, combinations
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
import math
import networkx as nx

class RSU:
    def __init__(self, name, id, address, mac_address, rsu, coords, special_vehicle, current_edge, graph, normal_obu_coordinates):
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
        self.ambulance_edge=self.graph.edges[(0,1)]
        self.connected = {
            5 : {
                5 : True,
                6 : True,
                7 : True,
                8 : True,
                9 : True,
                10 : True,
            },
            6 : {
                5 : True,
                6 : True,
                7 : True,
                8 : True,
                9 : True,
                10 : True,
            },
            7 : {
                5 : True,
                6 : True,
                7 : True,
                8 : True,
                9 : True,
                10 : True,
            },
            8 : {
                5 : True,
                6 : True,
                7 : True,
                8 : True,
                9 : True,
                10 : True,
            },
            9 : {
                5 : True,
                6 : True,
                7 : True,
                8 : True,
                9 : True,
                10 : True,
            },
            10 : {
                5 : True,
                6 : True,
                7 : True,
                8 : True,
                9 : True,
                10 : True,
            },
        }

        self.received_obu_coordinates = {
            5: {'coords': [40.62975477416346,-8.653675317764284], 'mac': '6e:06:e0:03:00:05', 'name': 'obu1'},
            6: {'coords': normal_obu_coordinates[0], 'mac': '6e:06:e0:03:00:06', 'name': 'obu2'},
            7: {'coords': normal_obu_coordinates[1], 'mac': '6e:06:e0:03:00:07', 'name': 'obu3'},
            8: {'coords': normal_obu_coordinates[2], 'mac': '6e:06:e0:03:00:08', 'name': 'obu4'},
            9: {'coords': normal_obu_coordinates[3], 'mac': '6e:06:e0:03:00:09', 'name': 'obu5'},
            10: {'coords': normal_obu_coordinates[4], 'mac': '6e:06:e0:03:00:10', 'name': 'obu6'},
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
            if self.id == 1:
                self.check_ranges()
            # cam_message = self.generate_cam()
            # self.send_message('vanetza/in/cam', cam_message)
            # print(f'IN -> RSU: {self.name} | MSG: {cam_message}\n')
            time.sleep(0.5)
        
        # end the client
        client.loop_stop()
        client.disconnect()

    def get_ambulance_edge(self,coords):
        self.ambulance_edge = self.special_vehicle.get_current_edge()

    def on_message(self, client, userdata, msg):
        message = json.loads(msg.payload.decode('utf-8'))
        msg_type = msg.topic
        # print(message['longitude'])
        # self.get_ambulance_edge(message['latitude'],message['longitude'])

        if msg_type == 'vanetza/out/cam':
            if self.id == 1 and message['stationID'] in self.received_obu_coordinates.keys():
                self.received_obu_coordinates[message['stationID']]['coords'] = [message['latitude'], message['longitude']]
            
            # resend message with data of the cam received
            if message['stationID'] != self.id and message['stationType'] == 19:
                cam_message = self.generate_cam([message['latitude'], message['longitude']], message['stationID'], 5)
                self.send_message('vanetza/in/cam', cam_message)
                # if message['stationID'] == 10:
                #     print(f"RESEND CAM -> RSU: {self.id} | stationID: {message['stationID']} | MSG: {message}\n")

            #     resend_cam = self.generate_cam([message['latitude'], message['longitude']], message['stationID'], message['stationType'])
            #     # print(f"RESEND CAM -> RSU: {self.name} | stationID: {message['stationID']} | MSG: {message}\n")
            #     self.send_message('vanetza/in/cam', resend_cam)
            # # print(f"OUT CAM -> RSU: {self.name} | stationID: {message['stationID']} | MSG: {message}\n")
        
        if msg_type == 'vanetza/out/denm':
            if message['fields']['denm']['situation']['eventType']['causeCode'] == 95:
                #get the edge of the ambulance
                self.get_ambulance_edge([(message['fields']['denm']['management']['eventPosition']['latitude'], message['fields']['denm']['management']['eventPosition']['longitude'])])
                graph_edges = self.graph.edges()
                egdes=[]
                
                egdes.append(self.graph.edges[self.ambulance_edge]['attr']['signalGroup'])
                states=[]
                states.append(5)
                for edge in graph_edges:
                    if (edge[1] == self.ambulance_edge[1]) and self.graph.edges[edge]['attr']['signalGroup'] not in egdes:
                        # print("edge",edge)
                        egdes.append(self.graph.edges[edge]['attr']['signalGroup'])
                        states.append(2)
                    
                spatem_message = self.generate_spatem(1,states,egdes)
                self.send_message('vanetza/in/spatem', spatem_message)
                
                print(f"RSU: {self.name} received DENM from OBU: {message['stationID']} | MSG: {message}\n")
                #     print(f"RSU: {self.name} sending SPATEM | MSG: {spatem_message}\n")



    def generate_cam(self, coords, station_id, station_type):
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
            coords[0],
            self.length,
            coords[1],
            0,
            0,
            0,
            cam.SpecialVehicle(cam.PublicTransportContainer(False)),
            self.speed,
            0,
            True,
            station_id,
            station_type,
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
                                "minEndTime":7
                            }
                        }
                    ]
                }
            )

        # print(spatem)
        return spatem


    def check_ranges(self):
        ids = list(self.received_obu_coordinates.keys())
        pairs = combinations(ids, 2)
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
        # measure delay between the call of the docker-compose exec and the change of the iptables
        for pair in pairs:
            id1, id2 = pair
            coord1 = self.received_obu_coordinates[id1]['coords']
            coord2 = self.received_obu_coordinates[id2]['coords']
            if coord1 != [] and coord2 != []:
                distance = geopy.distance.distance(coord1, coord2).m
                # print(f"Distance between {id1} with coords {coord1} and {id2} with coords {coord2} is {distance}")
                if distance < 100 and not self.connected[id1][id2]:
                    # print(f'RSU: {self.name} | OBU: {id1} and OBU: {id2} are in range\n')
                    subprocess.run(f"docker-compose exec {self.received_obu_coordinates[id1]['name']} unblock {self.received_obu_coordinates[id2]['mac']}", shell=True, check=True)
                    self.connected[id1][id2] = True
                    subprocess.run(f"docker-compose exec {self.received_obu_coordinates[id2]['name']} unblock {self.received_obu_coordinates[id1]['mac']}", shell=True, check=True)
                    self.connected[id2][id1] = True
                elif distance > 100 and self.connected[id1][id2]:
                    # print(f'RSU: {self.name} | OBU: {id1} and OBU: {id2} are not in range\n')
                    subprocess.run(f"docker-compose exec {self.received_obu_coordinates[id1]['name']} block {self.received_obu_coordinates[id2]['mac']}", shell=True, check=True)
                    # print(f"docker-compose exec {self.received_obu_coordinates[id1]['name']} block {self.received_obu_coordinates[id2]['mac']}")
                    self.connected[id1][id2] = False
                    subprocess.run(f"docker-compose exec {self.received_obu_coordinates[id2]['name']} block {self.received_obu_coordinates[id1]['mac']}", shell=True, check=True)
                    self.connected[id2][id1] = False
            else:
                # print(f'RSU: {self.name} | OBU: {id1} and OBU: {id2} are not in range\n')
                subprocess.run(f"docker-compose exec {self.received_obu_coordinates[id1]['name']} block {self.received_obu_coordinates[id2]['mac']}", shell=True, check=True)
                # print(f"docker-compose exec {self.received_obu_coordinates[id1]['name']} block {self.received_obu_coordinates[id2]['mac']}")
                self.connected[id1][id2] = False
                subprocess.run(f"docker-compose exec {self.received_obu_coordinates[id2]['name']} block {self.received_obu_coordinates[id1]['mac']}", shell=True, check=True)
                self.connected[id2][id1] = False
    
    def get_connected(self):
        return self.connected