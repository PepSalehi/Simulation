# -*- coding: utf-8 -*-
"""
Created on Mon Jul 10 15:03:05 2017

@author: Peyman
"""
from config import *
class Garage(object):
    def __init__(self, trains, position, param, garage_name):
        self.queue = deque()
        self.Param = param
        self.garage_name = garage_name
        for train in trains:
            self.add_to_garage(train)
    def add_to_garage(self, train):
        self.queue.append(train)
        train.next_station_id = self.Param.stations[0]
        train.prev_station_id = None
        train.is_in_service = False
        train.direction = self.Param.direction
        train.Param = self.Param
        print 'train', str(train.car_id), 'joined the queue ', str(self.garage_name)
    def dispatch_train(self, t):
        dispatched_train = self.queue.popleft()
        dispatched_train.next_station_id = self.Param.stations[0]
        dispatched_train.prev_station_id = self.garage_name
        dispatched_train.is_in_service = True
        dispatched_train.time_to_next_station = self.Param.station_travel_times[self.garage_name][self.Param.stations[0]]
        
#==============================================================================
#         print 'dispatched train', str(dispatched_train.car_id) , ' at time ', str(t), " from queue ", str(self.garage_name)
#         print dispatched_train.is_in_service
#         print str(len(self.queue)) + ' trains in the garage' 
#==============================================================================
    
    