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
        self.last_dispatched_train = None
        for train in trains:
            self.add_to_garage(train)
    def add_to_garage(self, train):
        self.queue.append(train)
        train.next_station_id = self.Param.stations[0]
        train.prev_station_id = None
        train.is_in_service = False
        train.direction = self.Param.direction
        train.Param = self.Param
        train.next_platform = None
        train.next_next_platform = None
        print 'train', str(train.car_id), 'joined the queue ', str(self.garage_name)
        # 
        train.distance_from_garage = 0
        # make sure the trailing train knows that there is no train in front of it 
        if train.train_in_back:
            if train.train_in_back.train_in_front:
                train.train_in_back.train_in_front = None
        train.train_in_back = None
        train.train_in_front = None
        train.distance_to_train_in_back = None
        train.it_has_reached_a_station = False 
        # 
        
    def dispatch_train(self, t):
        dispatched_train = self.queue.popleft()
 
        dispatched_train.next_station_id = self.Param.stations[0]
        dispatched_train.prev_station_id = self.garage_name
        dispatched_train.is_in_service = True
        dispatched_train.time_to_next_station = self.Param.station_travel_times[self.garage_name][self.Param.stations[0]]
        dispatched_train.distance_from_garage = 0
            
        # in case a train was previously dispatched, i.e. this is NOT the first time it is running 
        if self.last_dispatched_train :
            self.last_dispatched_train.train_in_back = dispatched_train
            self.last_dispatched_train.distance_to_train_in_back = self.last_dispatched_train.distance_from_garage
            dispatched_train.train_in_front = self.last_dispatched_train
            
            
#==============================================================================
#             dist_from_g = self.last_dispatched_train.distance_from_garage
#             dispatched_train.distance_from_train_infront = dist_from_g
#             self.last_dispatched_train.distance_to_train_inback = dist_from_g
#==============================================================================
            
        self.last_dispatched_train = dispatched_train
        

        
#==============================================================================
#         print 'dispatched train', str(dispatched_train.car_id) , ' at time ', str(t), " from queue ", str(self.garage_name)
#         print dispatched_train.is_in_service
#         print str(len(self.queue)) + ' trains in the garage' 
#==============================================================================
    
    