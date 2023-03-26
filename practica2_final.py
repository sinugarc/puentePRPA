"""
Solution to the one-way tunnel

No deadlocks or inanition. There is a limit on the number of pedestrians
or cars who can use the bridge at the same time, most of the parameters
could be modified at the start.

By Sinhue Garcia Gil
"""
import time
import random
from multiprocessing import Manager, Lock, Condition, Process
from multiprocessing import Value

SOUTH = 1
NORTH = 0

NCARS_NORTH = 100
NCARS_SOUTH = 60
NPED = 16

TIME_CARS_NORTH = 0.5  # a new car enters each 0.5s
TIME_CARS_SOUTH = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s

TIME_IN_BRIDGE_CARS_NORTH = (1, 0.5) # normal (1s, 0.5s)
TIME_IN_BRIDGE_CARS_SOUTH = (1, 0.5) # normal (1s, 0.5s)
TIME_IN_BRIDGE_PEDESTRIAN = (10, 5) # normal (10s, 0.5s)

MAX_WAITING_0 = 8
MAX_WAITING_1 = 4
MAX_WAITING_PED = 5

class Monitor():
    def __init__(self):
        manager = Manager()
        self.mutex = Lock()
        self.patata = Value('i', 0)
        
        self.waiting = Condition(self.mutex)
        self.waiting_list = manager.list([0]*3)
        self.waiting_max = manager.list([MAX_WAITING_0,MAX_WAITING_1,MAX_WAITING_PED])
        
        self.inside = Value('i', 0)
        self.free_bridge = Condition(self.mutex)
        self.who_is_inside = manager.list([False]*3) # Pedestrians = 2
        
    def is_anyone_waiting(self, direction: int) -> bool:
            return self.waiting_list[(direction+1)%3] == 0 and \
                   self.waiting_list[(direction-1)%3] == 0 and \
                   self.waiting_list[direction] < self.waiting_max[direction]

    def empty_bridge(self, direction: int) -> bool:
        return  not self.who_is_inside[(direction-1)%3] and \
            not self.who_is_inside[(direction+1)%3]

    def wants_enter(self, pid: int, direction: int) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        self.waiting.wait_for(lambda: self.is_anyone_waiting(direction,))
        if direction == 2: 
            print(f'Pedestrian {pid} waiting')
        else:
            print(f'Car {pid} waiting from {direction}')
        self.waiting_list[direction] += 1
        self.free_bridge.wait_for(lambda: self.empty_bridge(direction))
        self.who_is_inside[direction] = True
        self.inside.value += 1
        self.mutex.release()

    def leaves(self, direction: int) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        self.inside.value -= 1
        if self.inside.value == 0:
            print("Empty bridge, direction may change \n")
            self.who_is_inside[direction] = False
            self.free_bridge.notify_all()
            self.waiting_list[direction] = 0
            self.waiting.notify_all()
        self.mutex.release()

    def __repr__(self) -> str:
        return f'Monitor: {self.patata.value}'

def delay_car_north() -> None:
    a=random.normalvariate(TIME_IN_BRIDGE_CARS_NORTH[0],
                           TIME_IN_BRIDGE_CARS_NORTH[1])
    if a>=0 : time.sleep(a)

def delay_car_south() -> None:
    a=random.normalvariate(TIME_IN_BRIDGE_CARS_SOUTH[0],
                           TIME_IN_BRIDGE_CARS_SOUTH[1])
    if a>=0 : time.sleep(a)

def delay_pedestrian() -> None:
    a=random.normalvariate(TIME_IN_BRIDGE_PEDESTRIAN[0],
                           TIME_IN_BRIDGE_PEDESTRIAN[1])
    if a>=0 : time.sleep(a)

def car(cid: int, direction: int, monitor: Monitor)  -> None:
    print(f"car {cid} heading {direction} wants to enter. {monitor}")
    monitor.wants_enter(cid,direction)
    print(f"car {cid} heading {direction} enters the bridge. {monitor}")
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    print(f"car {cid} heading {direction} leaving the bridge. {monitor}")
    monitor.leaves(direction)
    print(f"car {cid} heading {direction} out of the bridge. {monitor}")

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"pedestrian {pid} wants to enter. {monitor}")
    monitor.wants_enter(pid,2)
    print(f"pedestrian {pid} enters the bridge. {monitor}")
    delay_pedestrian()
    print(f"pedestrian {pid} leaving the bridge. {monitor}")
    monitor.leaves(2)
    print(f"pedestrian {pid} out of the bridge. {monitor}")



def gen_pedestrian(monitor: Monitor) -> None:
    pid = 0
    plst = []
    for _ in range(NPED):
        pid += 1
        p = Process(target=pedestrian, args=(pid, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_PED))

    for p in plst:
        p.join()
    print("Ped generator has finished \n")

def gen_cars(direction: int, NCARS: int, time_cars, monitor: Monitor) -> None:
    cid = 0
    plst = []
    for _ in range(NCARS):
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/time_cars))

    for p in plst:
        p.join()
    if direction == NORTH:
        print('Car generator from North has finished \n')
    else:
        
        print('Car generator from South has finished \n')
    
def main():
    monitor = Monitor()
    gcars_north = Process(target=gen_cars, args=(NORTH, NCARS_NORTH, TIME_CARS_NORTH, monitor))
    gcars_south = Process(target=gen_cars, args=(SOUTH, NCARS_SOUTH, TIME_CARS_SOUTH, monitor))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars_north.start()
    gcars_south.start()
    gped.start()
    gcars_north.join()
    gcars_south.join()
    gped.join()

if __name__ == '__main__':
    main()
