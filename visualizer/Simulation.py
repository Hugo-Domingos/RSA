import threading
from obu import OBU
from route import Route
from rsu import RSU

class Simulation:
    # obus = []

    def __init__(self):
        self.obus = []
        self.rsus = []
        self.route1 = Route('coordinates/street2.csv')
        self.route2 = Route('coordinates/street1.csv')

    def run(self):
        self.rsus.append(RSU('rsu1', 1, '192.168.98.10', 'rsu1', self.route1, [40.6334546665471, -8.654870575236478]))
        self.rsus.append(RSU('rsu2', 2, '192.168.98.40', 'rsu2', self.route2, [40.632412479977084, -8.65541774587554]))

        self.obus.append(OBU('obu1', 1, '192.168.98.20', 'obu1', self.route1, 1))
        # self.obus.append(OBU('obu2', 2, '192.168.98.30', 'obu2', self.route2))

        rsu_threads = []
        for i in range(0, len(self.rsus)):
            rsu_threads.append(threading.Thread(target=self.rsus[i].start))
            rsu_threads[i].start()
        
        obu_threads = []
        for i in range(0, len(self.obus)):
            obu_threads.append(threading.Thread(target=self.obus[i].start))
            obu_threads[i].start()

        for thread in rsu_threads:
            thread.join()
        self.rsus = []

        for thread in obu_threads:
            thread.join()
        self.obus = []

    def get_status(self):
        status = {}
        for obu in self.obus:
            status[obu.name] = {'latitude': obu.coords[0], 'longitude': obu.coords[1]}
        return status

    def kill_simulation(self):
        for obu in self.obus:
            obu.set_finished(True)
    
if __name__ == '__main__':
    s = Simulation()
    s.run()