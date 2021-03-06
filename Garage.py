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
            self.add_to_garage(train, t=0)
        # need it to retrieve the order trains were dispatched
        self._dispatched_train_ids = []
        self._number_dispached = 0
    def add_to_garage(self, train, t=None, to_left=False):
        added = False 
        if to_left:
            self.queue.appendleft(train)
            added = True 
        else:
            if train not in self.queue: # cautionary. hoping it fixes dispatching process when updates happen late in the simulation
                self.queue.append(train)
                added = True 
        if added : 
            train.next_station_id = self.Param.stations[0]
            train.prev_station_id = None
            train.is_in_service = False
            train.is_in_garage = True
            train.last_garage_name = self.garage_name
            train.direction = self.Param.direction
            train.Param = self.Param
            train.next_platform = None
            train.next_next_platform = None
    #==============================================================================
    #        print 'train', str(train.car_id), 'joined the queue ', str(self.garage_name)
    #==============================================================================
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
            train._number_of_times_added_to_garage += 1 
        else:
            print "TRAIN WAS ALREADY IN THE QUEUE"
            print self.garage_name
            print "car_id", train.car_id
            print "queue", [tr.car_id for tr in self.queue]
            
            train.next_station_id = self.Param.stations[0]
            train.prev_station_id = None
            train.is_in_service = False
            train.is_in_garage = True
            train.last_garage_name = self.garage_name
            train.direction = self.Param.direction
            train.Param = self.Param
            train.next_platform = None
            train.next_next_platform = None
            train.distance_from_garage = 0
            if train.train_in_back:
                if train.train_in_back.train_in_front:
                    train.train_in_back.train_in_front = None
            train.train_in_back = None
            train.train_in_front = None
            train.distance_to_train_in_back = None
            train.it_has_reached_a_station = False 
            
        # 
        
    def dispatch_train(self, t, central_monitor_instance):
        dispatched_train = self.queue.popleft()
        dispatched_train.is_in_garage = False
        dispatched_train._number_dispached = self._number_dispached
        self._number_dispached += 1
        
        dispatched_train.next_station_id = self.Param.stations[0]
        dispatched_train.prev_station_id = self.garage_name
        dispatched_train.is_in_service = True
        dispatched_train.time_to_next_station = self.Param.station_travel_times[self.garage_name][self.Param.stations[0]]
#        dispatched_train.distance_from_garage = 0
        
        dispatched_train._dispatch_times.append(t)
        #
        dispatched_train.distance_to_next_station = 1
        dispatched_train._add_train_to_platform_upcoming(central_monitor_instance, dispatched_train.next_station_id, 1, t )
        # 
        dispatched_train.current_speed = self.Param.consecutive_speeds[self.garage_name][dispatched_train.next_station_id][0]
        assert dispatched_train.current_speed > 0 
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
        #
        self._dispatched_train_ids.append(dispatched_train.car_id)        
        
#==============================================================================
#         print 'dispatched train', str(dispatched_train.car_id) , ' at time ', str(t), " from queue ", str(self.garage_name)
# #        print dispatched_train.is_in_service
#         print str(len(self.queue)) + ' trains in the garage' 
#     
#     
#==============================================================================
