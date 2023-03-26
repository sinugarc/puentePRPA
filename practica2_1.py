"""
Solution to the one-way tunnel

No deadlocks or inanition, although there is no limit on the amount
of vehicles waiting to use the bridge at the same time.

By Sinhue Garcia Gil
"""
import time
import random
from multiprocessing import Manager, Lock, Condition, Process
from multiprocessing import Value

SOUTH = 1
NORTH = 0

NCARS = 10
NPED = 5
TIME_CARS_NORTH = 0.5  # a new car enters each 0.5s
TIME_CARS_SOUTH = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRIAN = (10, 5) # normal 1s, 0.5s

class Monitor():
    def __init__(self):
        manager = Manager()
        self.mutex = Lock()
        self.patata = Value('i', 0)
        self.inside = Value('i', 0)
        self.who_is_inside = manager.list([False]*3) # Pedestrians = 2
        self.who_is_waiting = manager.list([False]*3) # Pedestrians = 2
        self.free_bridge = Condition(self.mutex)
        self.waiting = Condition(self.mutex)
        
    def is_anyone_waiting(self, direction):
        return not self.who_is_waiting[(direction-1)%3] and \
            not self.who_is_waiting[(direction+1)%3]

    def empty_bridge(self, direction):
        return  not self.who_is_inside[(direction-1)%3] and \
            not self.who_is_inside[(direction+1)%3]

    def wants_enter_car(self, cid: int,direction: int) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        self.waiting.wait_for(lambda: self.is_anyone_waiting(direction))
        print(f'Car {cid} waiting from {direction}')
        self.who_is_waiting[direction] = True
        self.free_bridge.wait_for(lambda: self.empty_bridge(direction))
        self.who_is_inside[direction] = True
        self.inside.value += 1
        self.who_is_waiting[direction] = False
        self.waiting.notify_all()
        self.mutex.release()

    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire() 
        self.patata.value += 1
        self.inside.value -= 1
        if self.inside.value == 0:
            print("Empty bridge, direction may be changed \n")
            self.who_is_inside[direction] = False
            self.free_bridge.notify_all()
        self.mutex.release()

    def wants_enter_pedestrian(self,pid: int) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        self.waiting.wait_for(lambda: self.is_anyone_waiting(2))
        print(f'Pedestrian {pid} waiting')
        self.who_is_waiting[2] = True
        self.free_bridge.wait_for(lambda: self.empty_bridge(2))
        self.who_is_inside[2] = True
        self.inside.value += 1
        self.who_is_waiting[2] = False
        self.waiting.notify_all()
        self.mutex.release()

    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        self.inside.value -= 1
        if self.inside.value == 0:
            print("Empty bridge, direction may be changed \n")
            self.who_is_inside[2] = False
            self.free_bridge.notify_all()
        self.mutex.release()

    def __repr__(self) -> str:
        return f'Monitor: {self.patata.value}'

def delay_car_north() -> None:
    a=random.normalvariate(TIME_IN_BRIDGE_CARS[0],
                           TIME_IN_BRIDGE_CARS[1])
    if a>=0 : time.sleep(a)

def delay_car_south() -> None:
    a=random.normalvariate(TIME_IN_BRIDGE_CARS[0],
                           TIME_IN_BRIDGE_CARS[1])
    if a>=0 : time.sleep(a)

def delay_pedestrian() -> None:
    a=random.normalvariate(TIME_IN_BRIDGE_PEDESTRIAN[0],
                           TIME_IN_BRIDGE_PEDESTRIAN[1])
    if a>=0 : time.sleep(a)

def car(cid: int, direction: int, monitor: Monitor)  -> None:
    print(f"car {cid} heading {direction} wants to enter. {monitor}")
    monitor.wants_enter_car(cid, direction)
    print(f"car {cid} heading {direction} enters the bridge. {monitor}")
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    print(f"car {cid} heading {direction} leaving the bridge. {monitor}")
    monitor.leaves_car(direction)
    print(f"car {cid} heading {direction} out of the bridge. {monitor}")

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"pedestrian {pid} wants to enter. {monitor}")
    monitor.wants_enter_pedestrian(pid)
    print(f"pedestrian {pid} enters the bridge. {monitor}")
    delay_pedestrian()
    print(f"pedestrian {pid} leaving the bridge. {monitor}")
    monitor.leaves_pedestrian()
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
    print("Pedestrian generator has finished \n")

def gen_cars(direction: int, time_cars, monitor: Monitor) -> None:
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
    print(f'Car generator heading {direction} has finished \n')
    
def main():
    monitor = Monitor()
    gcars_north = Process(target=gen_cars, args=(NORTH, TIME_CARS_NORTH, monitor))
    gcars_south = Process(target=gen_cars, args=(SOUTH, TIME_CARS_SOUTH, monitor))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars_north.start()
    gcars_south.start()
    gped.start()
    gcars_north.join()
    gcars_south.join()
    gped.join()

if __name__ == '__main__':
    main()
