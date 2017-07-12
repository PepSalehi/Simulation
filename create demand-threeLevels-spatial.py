
# coding: utf-8

# In[1]:
from __future__ import division
import numpy as np
import random 
from collections import deque, defaultdict
from string import ascii_lowercase, letters 
import pandas as pd
import matplotlib.pyplot as plt
import time
import cPickle as pickle
from collections import namedtuple
from os import listdir
from os.path import isfile, join
import logging
import seaborn as sns
from functools import partial

random.seed(123)

# In[2]:

import shapely
from pyproj import Proj, transform


# In[3]:

class Param(object):
    
    '''store all the parameters inside this class
        TODO: currently all travel times are fixed. They should be changed to be stochastic.
        TODO: assign a numeric value to each station; makes it easier to get next/previous stations
    '''
    
    station_travel_times = pickle.load(
        open("E:/Research/projects/Crowding/central_line_station_travel_times.p", "rb"))
    
    station_distances = pickle.load(
        open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/station_distances.p", "rb"))
    
    route_nlcs = pickle.load(
        open("E:/Research/projects/Crowding/route_nlcs.p", "rb"))
    # 18 hours
    SIMULATION_TIME = 18 * 60 * 60
    HEADWAY = 3 * 60 #3 minutes
    stations = [(i) for i in route_nlcs]
        
        
   
    # add Garage to 1 travel time (0)
    station_travel_times["garage"][560]= 1

    # create sufficient trains
    max_tt = max(station_travel_times[560].values())

    num_req_trains = int(np.ceil(max_tt / HEADWAY)) + 1 # safety measure
    train_ids = [alp for alp in letters[0:num_req_trains]]
    terminal_station = stations[len(stations)-1]
    
    # assign station positions
    station_positions = pickle.load(
        open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/station_loopkup_geom_by_nlc.p", "rb"))
    
    
    central_line = pickle.load(
     open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/central_line.p", "rb"))



# In[4]:

Param.station_positions


# In[5]:

Param.num_req_trains


# In[6]:

Param.stations


# In[7]:

# from distance_functions_on_shapely import distance_btw_two_points_on_a_line


# In[8]:

# # so that there is no need to input line every time
# distance_btw_two_points_on_a_line = partial(distance_btw_two_points_on_a_line, Param.central_line)

# find_stations_after_train = partial(find_stations_after_train, Param.central_line)


# In[78]:

# find_trains_before_station = partial(find_trains_before_station, Param.central_line)


# In[73]:

# find_travel_time_btw_two_pts_FIXEDSPEED = partial( find_travel_time_btw_two_pts_FIXEDSPEED, speed = Train.SPEED)


# In[ ]:




# In[9]:

Param.central_line


# In[74]:

# distance_btw_two_points_on_a_line(Param.station_positions[633], Param.station_positions[513])


# In[10]:

(Param.station_positions)


# In[ ]:




# In[11]:

Param.HEADWAY


# In[12]:

data_path =  "E:\\Research\\projects\\Short_term_forcast\\R code\\data\\"


# In[13]:

route_nlcs = pickle.load(
        open("E:/Research/projects/Crowding/route_nlcs.p", "rb"))


# In[14]:

Param.max_tt


# In[27]:

class Station(object):
    
    def __init__(self, ids, demand=0):
        self.ids = ids
        self.demand = 0
        
        self.queue = defaultdict(deque)
        self.historical_queue = deque()
        self.observed_queue = deque()
        self.predicted_queue = deque()
        
        self.next_stations = Param.station_travel_times[ids].keys()
        self.arrival_times = []
        # a way to enforce trains don't move head to end
        self.is_occupied = False
        self.time_since_occupied = 100000
        # bookkeeping
        self._load_histoty = 0
        # pax created
        self.pax_list = defaultdict(list)
        self.demand_rate = defaultdict(float)
        # 
        self.position = None
        self.arriving_trains_loads = defaultdict(list)
        # Queue length at the time of train arrival
        self.hist_queue = defaultdict(list)

     
    
    def _populate_demand(self, demand_dict, t_offset, section, time_range = 15*60 ): 
        
        for destination, demands in demand_dict[self].iteritems():
            # demand during time_period t_offset
            demand = demands[t_offset]
            
            for _ in range(1, demand+1):
                # arrival time is now uniformly distributed during the 15 minutes interval 
                pax = Passenger(entry_station = self.ids, exit_station = destination.ids, entry_time = int(random.uniform(t_offset, t_offset + time_range)))
                if section == "H":
                    CentralMonitor.all_passengers_created_historical.append(pax) 
                    self.pax_list["H"].append(pax)
                elif section == "O":
                    CentralMonitor.all_passengers_created_observed.append(pax)
                    self.pax_list["O"].append(pax)
                elif section == "P":
                    CentralMonitor.all_passengers_created_predicted.append(pax) 
                    self.pax_list["P"].append(pax)
                
    def produce_passsengers(self, t_offset, time_range = 15*60):
        # there should be no unproduced passengers from last interval
#         assert len(self.pax_list) == 0
        self.pax_list = defaultdict(list)

        
        self._populate_demand(CentralMonitor.station_demands_observed, t_offset, "O" )
        self._populate_demand(CentralMonitor.station_demands_historical, t_offset, "H" )
        self._populate_demand(CentralMonitor.station_demands_predicted, t_offset, "P" )

        self.demand_rate["O"] = len(self.pax_list["O"]) / time_range
        self.demand_rate["H"] = len(self.pax_list["H"]) / time_range
        self.demand_rate["P"] = len(self.pax_list["P"]) / time_range
        
        
    def _return_matched_pax(self, ts):
        
        matched_observed = [pax for pax in self.pax_list["O"] if pax.entry_time in ts ]
        matched_historical = [pax for pax in self.pax_list["H"] if pax.entry_time in ts ]
        matched_predicted = [pax for pax in self.pax_list["P"] if pax.entry_time in ts ]
        
        results = {"O": matched_observed, "H":matched_historical, "P":matched_predicted}
        return results
        
    def _append_to_queue(self, k, matched):
        
        if len(matched) > 0:
            for pax in matched:
                self.queue[k].append(pax)
    
    
    def produce_passengers_per_t(self, t):
        
        all_matched_dict = self._return_matched_pax([t])
        
        for k, matches in all_matched_dict.iteritems():
            self._append_to_queue(k, matches)
        
                
    def get_waiting_passengers(self, k):
        return self.queue[k]
    def reset_time_since_boarding(self):
        self.time_since_occupied = 0
        
    def get_general_train_info(self, t):
        '''
        TODO: document its functionality
        '''
        
        trains_in_service = [train for train in CentralMonitor.trains if train.is_in_service]
        upcoming_trains = find_trains_before_station(self.position, trains_in_service)
        upcoming_trains_arrival_time = []
        for train in upcoming_trains:
            upcoming_trains_arrival_time.append([train, find_travel_time_btw_two_pts_FIXEDSPEED (self.position, train.position, Train.SPEED)])
            
#         upcoming = []
#         for train in CentralMonitor.trains:
            
#             if train.is_in_service:
#                 # train has not passed it
#                 dist = distance_btw_two_points_on_a_line(train.position, self.location) 
#                 if dist < 1e-5:
# #                 if train.position - self.location < 0 : # THIS NEEDS TO CHANGE TO DISTANCE ON A NETWORK
# #                     upcoming.append([train, abs(train.position - self.location)]) # THIS NEEDS TO CHANGE TO DISTANCE ON A NETWORK
#                     upcoming.append([train, dist]) # THIS NEEDS TO CHANGE TO DISTANCE ON A NETWORK

#     #         print upcoming

        upcoming.sort(key= lambda x:x[1])
        
        if upcoming is not None:
            relevant = upcoming[0:2]
            for tr_item in relevant:
                # THIS NEEDS TO CHANGE, TIME SHOULD BE CALCULATED
                print "time: " + str(t) + " train " + str(tr_item[0].car_id) + " is arriving in " + str(tr_item[1]) + " secs at station " + str(self.ids)
            
        print "at time "+ str(t) + " there are "+ str(len(self.get_waiting_passengers('O'))) + " waiting in queue" 
    
    def request_next_train_info(self, t): # MASSIVE REWRITE
        '''
        TODO: what is the functionality of this?
        '''
        upcoming = defaultdict(dict)
        for train in CentralMonitor.trains:
            if train.next_station_id == self.ids and train.is_in_service :
                
                # this is not correct. need to get predicted load, i.e. considering the offloadings
                # SEEMS TO BE FIXED, RIGHT?
                upcoming[train] = train.get_adjusted_load_at_next_station()
                
                
        
        for train, l in upcoming.iteritems():
            
            for level, load in l.iteritems():
                
                time_till_arrival = train.time_to_next_station
                # number of ppl that will arrive at station btw now and the time the train arrives
                new_arriving_pax = self._return_matched_pax(range(t, t + time_till_arrival))
                new_arriving_pax = new_arriving_pax[level]
                
#                 new_arriving_pax = self.demand_rate[level] * time_till_arrival
                
                
#                 print "new_arriving_pax: " + str(len(new_arriving_pax)) + " self.queue " + str(len(self.queue)) + " all "+ str(len(self.pax_list[level]))
                
                total_waiting_on_platform = len(self.queue[level]) + len(new_arriving_pax) + 1 # no time for division by zero
        
#                 print "len(self.queue[level]): " + str(len(self.queue[level]))
#                 print "total_waiting_on_platform: " + str(total_waiting_on_platform)

                # current train capacity
                available_capacity = train.CAPACITY - load + 1 # no time for division by zero
                ratio = (available_capacity / total_waiting_on_platform) 
                diff = total_waiting_on_platform - available_capacity
                prob_of_boarding = 1 if ratio >= 1 else ratio
                
                if prob_of_boarding < 1:
                    print("At t = " + str(t) + " Train " + str(train.car_id)+ " is arriving in " +
                           str(train.time_to_next_station/60)+ "minutes at station "+ str(self.ids)+" and will be "+ str(load/train.CAPACITY * 100)+ " % full, " +
                          "probability of boarding is "+ str(prob_of_boarding * 100)+ "%"+
                          " and " + str(diff)+ " passengers will be denied boarding"+" at level "+ level + " available_capacity: " + str(available_capacity)+
                         " total_waiting_on_platform: "+ str(total_waiting_on_platform) )
            
#     def add_to_station_queue(self, t, list_of_passengers):
#         for pax in list_of_passengers:
#             self.queue.append(pax)
            
#     def remove_from_station_queue(self, t, list_of_passengers):
        
#         for pax in list_of_passengers:
#             self.queue.remove(pax)
            
#             self._load_history -=1
        
            
            
    def update(self, t):
        # update Station for every epoch
        self.produce_passengers_per_t(t)
        # check if a train is there at the station
        if not self.is_occupied:
            self.time_since_occupied += 1
        
        # update status every 30 seconds
        if t % (1*30) == 0:
#             self.request_next_train_info(t)
            pass
#         if 'demand' in kw_args:
#             # new rate has been passed
#             self.demand = kw_args['demand']
            
        
            


# In[ ]:




# In[28]:

class Train(object):
    # https://tfl.gov.uk/corporate/about-tfl/what-we-do/london-underground/rolling-stock
    CAPACITY = 892 
    # https://tfl.gov.uk/corporate/about-tfl/what-we-do/london-underground/facts-and-figures
    SPEED = 9 # meters/sec


    def __init__(self, car_id, position = None, distance_to_next_station = None, next_station_id=None, prev_station_id=None, time_to_next_station = 1000000):
        self.car_id = car_id
        self.current_station_id = None # to be set when it arrives at a station 
        self.prev_station_id = prev_station_id
        self.next_station_id = next_station_id # KEEP
        self.has_arrived_at_station = False
        
        self.passengers = defaultdict(list)
        
        self.time_to_next_station = time_to_next_station # KEEP
        self.initial_departure_time = 1000000 
        self.is_in_service = False
        ## bookkeeping; will need them for realtime updates
        self.just_boarded = []
        self.just_offloaded = []
        self._load_history = defaultdict(list)
        ## updates in realtime
        self.updated_next_station = None
        self.updated_prev_station = None
        self.position = position
        self.distance_to_next_station = distance_to_next_station
        ##
        self.waiting = False
        self.time_started_waiting = None
        self.waiting_to_enter_station = False
        self.waiting_to_leave_station = False
        self.dwell = False
        self.dwell_time_spent = 10000
        self.DWELL = 15 # seconds
        
    
    def load_passenger(self, t, station):
#         print 'boarding at time ', t
        # don't keep track of those who were previously boarded 
        self.just_boarded = []
        #
        station.is_occupied = True
        denied = False
        i = 0
        for level in ["H", "O", "P"]:
            if len(self.passengers[level]) < self.CAPACITY:
                
                if self.CAPACITY - len(self.passengers[level]) < len(station.queue[level]): 
                    print "DENIED BOARDING for train "+ self.car_id + " at level " + level
                    denied = True
                    
                while len(self.passengers[level]) < self.CAPACITY and len(station.queue[level]) > 0:
                    pax = station.queue[level].pop()
                    pax.boarding_time = t
                    self.passengers[level].append(pax)
                    i += 1
                    self.just_boarded.append(pax)

                    CentralMonitor.all_passengers_boarded.append(pax)
                if denied :
                    j=0
                    for pax in station.queue[level]:
                        CentralMonitor.passenger_denied_boarding[level].append([pax, t, station])
                        j+=1
                    print str(j)+ " people couldn't board the train at level " + level
            else:
                denied = True
                for pax in station.queue[level]:
                        CentralMonitor.passenger_denied_boarding[level].append([pax, t, station])
                print "train is full"
                print str(len(station.queue[level]))+ " people couldn't board the train"
            
#             print "boarded ", str(i), "passengers at level ", level
#             print "train load is ", str(self.get_load(level))
            
            
#         # add dwell time
#         self.dwell = True
#         self.dwell_time_spent = 0
        
        
        
        station.time_since_occupied = 0
        station.is_occupied = False
        
    def should_wait_for_dwell_time(self,t):
        
        if self.dwell == True:
            self.dwell_time_spent += 1
            if self.dwell_time_spent <= self.DWELL:
                return True
            else :
                self.dwell = False
                return False
        else:
            return False
            
            
    def should_it_enter_the_station(self, station, min_buffer_time=60):
        # to unload and board pax
        # check when was the last time a train had left the station
        if station.time_since_occupied >= min_buffer_time:
            return True
        return False


    def get_load(self, level):
        return len(self.passengers[level])
    
    def offload_passengers(self, station_id, offload_time):
        # reset the list
        self.just_offloaded = []
        #
        for level in ["H", "O", "P"]:
            i = 0
#             print "before", len(self.passengers[level])
            # THIS IS EXTREMELY IMPORTANT http://stackoverflow.com/a/1207427/2005352
            for pax in self.passengers[level][:]:
                if pax.exit_station == station_id:
                    self.passengers[level].remove(pax)
                    # bookkeeping
                    pax.exit_time = offload_time
                    CentralMonitor.all_passengers_offloaded[level].append(pax)
                    i += 1
                    self.just_offloaded.append(pax)

#             print "offloaded ", str(i), "passengers", " ", level
#             print "after", len(self.passengers[level]), " ", level
        
    def empty_load(self, t):
        # for the last stop, so that it starts fresh at the beginnig of the line again
        # should set pax exit time and station
        for level in ["H", "O", "P"]:
            for pax in self.passengers[level]:
                pax.exit_time = t
                pax.exit_station = Param.stations[len(Param.stations)-1]

                CentralMonitor.all_passengers_offloaded.append(pax)

                CentralMonitor.all_passengers_emptied_at_last.append(pax)

            self.passengers = defaultdict(list)
        
    def get_next_station_id(self):
        if self.current_station_id != Param.terminal_station:
            # if this is not the last stop
            current_index = Param.stations.index(self.current_station_id)
            next_station_id = Param.stations[current_index + 1]
            return next_station_id 
        else:
            # terminal station
            return 'garage'
        

            
    def get_travel_time_to_next_station(self):
        # make it stochastic
        base = Param.station_travel_times[self.current_station_id][self.next_station_id]
#         variable = int(random.normalvariate(200,300))
#         while 0.5 * base < abs(variable) :
#             variable = int(random.normalvariate(200,300))
            
        tt = base #+ variable 
        assert(tt > 0)
        return tt 
    
    def start_waiting (self):
        self.waiting = True
        self.time_started_waiting = 0
        
    def keep_waiting (self):
        self.time_started_waiting += 1
        
    def should_it_keep_waiting(self, waiting_time = 1 * 60):
        # returns True if t <= waiting time, proxy for inaction for a while
        if self.time_started_waiting <= waiting_time :
            assert (self.waiting == True)
            return True
        else:
            self.waiting = False
            self.time_started_waiting = 0
            return False
    
    def get_adjusted_load_at_next_station(self):
        exiting = defaultdict(list)
        adj = defaultdict(int)
        # basically, subtract the number of pax who will offload the train at the next station from current load
        for level in ["H", "O", "P"]:
            exiting[level] = [pax  for pax in self.passengers[level] if pax.exit_station == self.next_station_id]
            adj[level] = int(self.get_load(level) - len(exiting[level]))
        return(adj)
    
    def start_over(self, t, garage = CentralMonitor.garage):
        # after offloading pax at the last stop
        self.empty_load(t)
        # go back at the origin
        self.position = 0 # CHANGE
        garage.add_to_garage(self)
        # it should wait for a while before coming back into the system
        # another approach could be to kill this and replace it with a new one at the origin,
        # this delegates matters into the setup process
    
#     def update_position_load(self, t, new_position):
#         ''' TODO: there is a whole lot of index playing going on, here and in the rest of the code, only because of the 
#             initial decision to work with relative time to stations rather than positions (x, y=0). I'm not sure if  going forward
#             this was a good decision to stand by, so might have to change structure of the code a bit.
        
#         '''
        
#         if self.is_in_service:
#             # it should infer the new next and prev station
#             def find_min_dist(target):
#                 target = target
#                 minimum = 10000
#                 key = None
#                 for k,v in Param.station_positions.iteritems():
#                     if v - target >= 0:
#                         if v - target < minimum:
#                             key = k
#                             minimum = v-target
#                 return key, minimum

#             new_next_station_id, time_to_next_station = find_min_dist(new_position)
#             # debug
#             print "new_next_station_id", new_next_station_id
#             if new_next_station_id == None : print new_position
#             # end debug
#             new_prev_station_id = CentralMonitor.get_prev_station_id(new_next_station_id)


#             # TODO: fix pax boarding/exit times

#             # is it yet to board passengers but we predicted that it already had done it?
#             if self.prev_station_id == new_next_station_id:
#                 # it has to de-board passengers, add them to the station queue, and load passengers who were offloaded
#                 print " it is yet to board passengers but we predicted that it already had done it"

#                 # de-board
#                 prev_station = CentralMonitor.return_station_by_id(self.prev_station_id)
#                 pax_to_deboard = [pax for pax in self.just_boarded]
#                 prev_station.add_to_station_queue(t, pax_to_deboard)
#                 # de-load
#                 for pax in self.just_boarded:
#                     self.passengers.remove(pax)
#                 # re-load
#                 for pax in self.just_offloaded:
#                     self.passengers.append(pax)

#             # has it already passed the station which we thought it's yet to reach?
#             elif self.next_station_id == new_prev_station_id:
#                 # it has to board passengers, remove them from the station queue, and offload passengers for that station
#                 print "it had already passed the station which we thought it's yet to reach"

#                 passed_station = CentralMonitor.return_station_by_id(self.next_station_id)
#                 pax_to_load = [pax for pax in passed_station.queue if pax.exit_station == passed_station.ids]
#                 # board
#                 boarded = []
#                 for pax in pax_to_load:
#                     if len(self.passengers) < self.CAPACITY:
#                         self.passengers.append(pax)
#                         boarded.append(pax)
#                 #  remove from station
#                 for pax in boarded:
#                     passed_station.queue.remove(pax)
#                 #  offload
#                 self.offload_passengers(passed_station, t)

#             # update position anyway
#             self.time_to_next_station = time_to_next_station
#             self.next_station_id = new_next_station_id
#             self.prev_station_id = new_prev_station_id
#             #
#             self.position = new_position
#             print "updated position"
    ###############################################################################################################
#     def _move_train_one_dist(self, pt, distance = Train.SPEED, line = Param.central_line):
    
#         if line.geom_type == 'LineString':
#             coords = line.coords[:] 
#         else:
#             coords = [geo.coords[:] for geo in line.geoms]
#             coords = [item for sublist in coords for item in sublist]


#         # Add the coords from the points
#         coords += pt.coords

#         # Calculate the distance along the line for each point
#         dists = [line.project(Point(p)) for p in coords]
#         # sort the coordinates
#         coords = [p for (d, p) in sorted(zip(dists, coords))]


#         break_pt = find_index_of_point_w_min_distance(coords, pt.coords[:][0])

#         if break_pt == 0:
#             # it is the first point on the line, "line_before" is meaningless
#             line_before = None
#         else:
#             line_before = LineString(coords[:break_pt+1])

#         if break_pt == len(coords)-1:
#             # it is the last point on the line, "line_after" is meaningless
#             line_after = None
#         else:
#             line_after = LineString(coords[break_pt+1:]) # so that it does not capture the point it's already on. deliberately done 
#             # for this function


#         if line_after != None:
#             # have checks for the end on line
#             np = line_after.interpolate(distance)
#             return np

#         return "Line is None, this is the end point"
    ###############################################################################################################        
    
    ################################################Another approach to move##############################################
    def _move_train_one_dist(self, pt, distance = Train.SPEED, line_all = Param.central_line):
        
        print pt
        
#         if line_all.intersects(pt):
#             line = [line for line in line_all if line.intersects(pt)][0]
#         else:
#             pt = line_all.interpolate(line_all.project(pt))
#             line = [line for line in line_all if line.intersects(pt)][0]
            
        line = [line for line in line_all if line.distance(pt) < 1e-8][0]
        
        dist_from_start_node = line.project(pt)
        #
        if line.length > distance:
            end_point = line.interpolate(distance + dist_from_start_node)
            return (end_point)
        # if
        else:
            print " moved passed the end of line, should've catched it before calling this function! "
            
    
    
    
    def move(self, distance=Train.SPEED):
        
#         # arriving and passing the station, and it's not the terminal station
#         if self.distance_to_next_station <= distance and self.next_station_id != Param.terminal_station:
#             # move it just enough
#             self.position = self._move_train_one_dist(self.position, distance = self.distance_to_next_station)
#             self.arrived_at_station()
            
#             # handle end of line situation here as well (move to garage, etc.)
#         elif self.distance_to_next_station <= distance and self.next_station_id ==  Param.terminal_station :
#             # update the status that has reached a station, and will be there for a few seconds
# #             self.has_arrived_at_station = True
#             # exiting pax?
#             # start over
#             self.start_over(t)
#         else:

        # check whether or not it has reached the station, or will reach and pass it if it moves, before calling this function
        print self.position
        self.position = self._move_train_one_dist(self.position, distance=distance)
        self.distance_to_next_station -= distance
        self.time_to_next_station -= self.distance_to_next_station / self.SPEED 
            
        CentralMonitor.train_trajectories[self.car_id].append(self.position)
        for level in ["H", "O", "P"]:
            self._load_history[level].append(self.get_load(level))
            
    def has_it_reached_a_station(self):
        # arriving and passing the station
        if self.distance_to_next_station <= self.SPEED:
#         or (self.distance_to_next_station <= self._move_train_one_dist(self.position, distance = self.distance_to_next_station)):
            return True
        return False
        
            
    def arrive_at_station(self, line_all = Param.central_line): 
        # set current station id
        self.current_station_id = self.next_station_id # since it has arrived at the station
        station = CentralMonitor.return_station_by_id(self.current_station_id)
#         self.position  = station.position
        self.position = line_all.interpolate(line_all.project(self.position) + self.distance_to_next_station)
        # update the status that has reached a station, and will be there for a few seconds
#         self.has_arrived_at_station = True
        
        
    def unload_passengers(self, t):
        self.offload_passengers(self.current_station_id, t)
    
    def board_passengers(self, t):
        # remember to first call unload passengers
        
        current_station = CentralMonitor.return_station_by_id(self.current_station_id)

        # check if this is the last station. 
        if self.current_station_id != Param.terminal_station:
            # board pax
            self.load_passenger(t, current_station)
            

            current_station.hist_queue["dh"].append(len(current_station.queue['H']))
            current_station.hist_queue["dp"].append(len(current_station.queue['P']))
            current_station.hist_queue["do"].append(len(current_station.queue['O']))
            current_station.hist_queue["t"].append(t)

        else:
            # if it is the last station
#             self.start_over(t=t)
            pass
    
    def depart_station(self, t):
        self.waiting = False
        
        
        if self.current_station_id == Param.terminal_station:
            # if it is the last station
            self.start_over(t=t)
        else:
            # get the next station id
            self.next_station_id = self.get_next_station_id()
            # get distance to next station
            self.distance_to_next_station = Param.station_distances[self.current_station_id][self.next_station_id]
            # get time to next station
            self.time_to_next_station = self.get_travel_time_to_next_station()
#             self.move(t=t)
            
            
            
        
    def update(self, t):
        # if it has been dispatched (i.e. is not in the garage)
        if self.is_in_service:
#             print "distance_to_next_station: ", self.distance_to_next_station, " at time: ", t
            if self.has_it_reached_a_station():
#                 print "reached station ", self.car_id, "at time ", t
                if not self.waiting: # if this is the first moment it has reached the staiton
                    station = CentralMonitor.return_station_by_id(self.next_station_id)
                    if self.should_it_enter_the_station(station): # TODO: get this station first
                        self.arrive_at_station()
                        self.unload_passengers(t)
                        self.board_passengers(t)
                        self.start_waiting()
                    else:
                        # wait for other train to leave the station
                        self.start_waiting()
                # it has been waiting here        
                else:
                    if self.should_it_keep_waiting():
                        self.keep_waiting()
                    else:
#                         print "left station ", self.car_id
                        self.depart_station(t)
#                         print "position: ", self.position

            else:
                # if it has not reached a station yet
#                 print "moving ", self.car_id
                self.move()


        else:
            CentralMonitor.train_trajectories[self.car_id].append(self.position)
       
           
        
        


# In[ ]:

class Passenger(object):
    
    def __init__(self, entry_station, exit_station, entry_time):
        
        self.entry_station = entry_station
        self.exit_station = exit_station
        self.entry_time = entry_time 
        self.boarding_time = 0
        self.exit_time = 0
    def get_travel_time(self):
        return self.exit_time - self.boarding_time
    def get_waiting_time(self):
        return self.boarding_time - self.entry_time
    def update():
        pass
        


# In[22]:

class Garage(object):
    def __init__(self, trains, position):
        self.queue = deque()
        for train in trains:
            self.add_to_garage(train)
    def add_to_garage(self, train):
        self.queue.append(train)
        train.next_station_id = Param.stations[0]
        train.prev_station_id = None
        train.is_in_service = False
        print 'train', str(train.car_id), 'joined the queue'
    def dispatch_train(self, t):
        dispatched_train = self.queue.popleft()
        dispatched_train.next_station_id = Param.stations[0]
        dispatched_train.prev_station_id = "garage" # hard coded, not good 
        dispatched_train.is_in_service = True
        dispatched_train.time_to_next_station = 1
        
        print 'dispatched train', str(dispatched_train.car_id) , ' at time ', str(t)
        print str(len(self.queue)) + ' trains in the garage' 
    
    


# In[26]:

class CentralMonitor(object):
    
    
    ''' A repo'''
    all_passengers_created_predicted = []
    all_passengers_created_observed = [] 
    all_passengers_created_historical = []
    
    all_passengers_offloaded = defaultdict(list)
    passenger_denied_boarding = defaultdict(list)
    
    
    all_passengers_boarded = []
    all_passengers_emptied_at_last = []
    # create trains
    trains = [Train(car_id=car_id, next_station_id=Param.stations[0], 
                    prev_station_id="garage", 
                    time_to_next_station= Param.station_travel_times["garage"][560],
                    distance_to_next_station = Param.station_distances["garage"],
                    position = Param.station_positions["garage"]) 
                    for car_id in Param.train_ids]
    # create stations
    stations = [Station(ids) for ids in Param.stations]
    for station in stations:
        station.position = Param.station_positions[station.ids]
        
        
    garage = Garage(trains, position = Param.station_positions['garage'])
    data_path =  "E:\\Research\\projects\\Short_term_forcast\\R code\\data\\"
    onlyfiles = [f for f in listdir(data_path) if isfile(join(data_path, f))]
    
    #
    @classmethod
    def get_next_station_id(self, station_id):
        
        if station_id != 'garage':
            current_index = Param.stations.index(station_id)
            if current_index != len(Param.stations) - 1:
                # if this is not the last stop
                next_station_id = Param.stations[current_index + 1]
                return next_station_id 
            else:
                # it is the terminal station
                return "garage"
        else:
            return 560
    @classmethod
    def get_prev_station_id(self, station_id):
        
        if station_id != 'garage':
            current_index = Param.stations.index(station_id)
            if current_index != 0:
                # if it's not the first station
                prev_station_id = Param.stations[current_index - 1]
                return prev_station_id 
            else:
                # it is  the garage
                return "garage"
        else:
            return "garage"
    
    def read_od_from_file( origin_id, dest_id, list_of_files=onlyfiles , data_path = data_path):
        
        Data = namedtuple("DATA", "observed predicted historical")

        broken = map( lambda x:x.split("_"), list_of_files)
        target = [i for i in broken if i[0] == str(origin_id) and i[1] == str(dest_id)]
        observed_file = "_".join([i for i in target if "observed" in i[2] ][0])
        predicted_file = "_".join([i for i in target if "prediction" in i[2] ][0])
        historical_file = "_".join([i for i in target if "historical" in i[2] ][0])

        temp = pd.read_csv(data_path+observed_file)
        observed_data = temp[temp.columns[1]].values

        temp = pd.read_csv(data_path+predicted_file)
        predicted_data = temp[temp.columns[1]].values

        temp = pd.read_csv(data_path+historical_file)
        historical_data = temp[temp.columns[1]].values

        data = Data (observed_data, predicted_data, historical_data)

        return data


    
    station_demands_observed = defaultdict(lambda : defaultdict(dict))
    station_demands_historical = defaultdict(lambda : defaultdict(dict))
    station_demands_predicted = defaultdict(lambda : defaultdict(dict))

    for idx, station in enumerate(stations[0:len(stations)-1]):
        origin_id =  station.ids
        for dest in stations[(idx+1):len(stations)]:
            dest_id = dest.ids
            demand = read_od_from_file(origin_id, dest_id)
            for ind, t in enumerate(range(0, Param.SIMULATION_TIME, 15*60)):
                station_demands_observed[station][dest][t] = demand.observed[ind]
                ####
#                 sugg = int(np.random.normal(0, (demand.historical[ind])/4+.1 ))
#                 while sugg < 0:
#                     sugg = int(np.random.normal(0, 2))
                ####
                station_demands_predicted[station][dest][t] = demand.predicted[ind] #demand.observed[ind] + sugg 
                station_demands_historical[station][dest][t] = demand.historical[ind]
    
    ####
    # the first train to arrive at this station takes 7000 seconds to get there, there is one passenger arriving in the first
    # time period that sufferes excessive waiting time. remove it. 
    a =[st for st in stations if st.ids == 725][0]
    station_demands_historical[a].values()[0][0]=0      
    ####    
            
            
            
    @classmethod
    def return_station_by_id(self, station_id):
        # so that other classes can have access to the original object
        for station in self.stations:
            if station.ids == station_id:
                return station
    
    
    # want to keep track of a train's trajectory
    train_trajectories = defaultdict(list)


# In[ ]:




# In[ ]:

Param.SIMULATION_TIME


# In[ ]:

[st.ids for st in CentralMonitor.stations].index(640)


# In[ ]:

import time
start_time = time.time()
simulation_time = Param.SIMULATION_TIME
MAX_POSITION = max(Param.station_positions.values())
for t in range(0, simulation_time):

    # produce passengers every 15 minutes. Needed to update demand as new obs. come in every 15 minutes
    if t % (15*60) == 0:
        [station.produce_passsengers(t_offset=t) 
                             for station in CentralMonitor.stations[0:len(CentralMonitor.stations)-1]]
    #

    # dispatch trains from garage every HEADWAY minutes
    if t % (Param.HEADWAY ) == 0:
        CentralMonitor.garage.dispatch_train(t)   
    #

    # update train positions every minute
#     if t % (60) == 0 and t > 0:
#         for train in CentralMonitor.trains:
#             old = train.position
#             new_pos = old + int(random.normalvariate(1*30,30))
#             while new_pos <= 0 or new_pos > MAX_POSITION:
#                 new_pos = old + int(random.normalvariate(1*30,30))
#             train.update_position_load(t, new_pos)

#     if (t% 1001) == 0 :
#         if t != 0:
#             print t
#             break
    if t % (30 ) == 0:
#         for station in CentralMonitor.stations:
#         CentralMonitor.stations[30].get_general_train_info(t)
        pass

    for station in CentralMonitor.stations:
        station.update(t)
        

    for train in CentralMonitor.trains:
        train.update(t)
        
end_time = time.time()    
# finish_up()


# In[372]:

a = Point (517952.0585772707, 180907.3754776951) 


# In[373]:

Param.central_line.intersects(a)


# In[458]:

a = CentralMonitor.trains[0]


# In[459]:

a.next_station_id


# In[460]:

a.should_it_enter_the_station(CentralMonitor.return_station_by_id(560))


# In[461]:

a.position.coords[:]


# In[324]:

a.move()


# In[462]:

b1 = CentralMonitor.trains[2].position


# In[464]:

Param.central_line.intersects(b1)


# In[326]:

CentralMonitor.trains[2].move()


# In[327]:

b2 = CentralMonitor.trains[2].position


# In[328]:

distance_btw_two_points_on_a_line(b1,b2)


# In[251]:

distance_btw_two_points_on_a_line(Point((532230.0818090158, 181219.24697168564)),(Point((532201.1211603704, 181229.4924406343))))


# In[309]:

a = Param.central_line


# In[310]:

a.length


# In[312]:

b1 = a.interpolate(100)


# In[313]:

b2 = a.interpolate(200)


# In[314]:

distance_btw_two_points_on_a_line(b1,b2)


# In[321]:

a


# In[320]:

a[1].intersects(a[10])


# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[22]:

def plot_trajectorty(train_id = 'a'):
    train_x = CentralMonitor.train_trajectories[train_id]
    y = [-i for i in range(len(train_x))]
    plt.plot(train_x, y)
    for station, x in Param.station_positions.iteritems():
        plt.axvline(x = x, color='r')


# In[23]:

plt.figure(figsize=(18,50))
plot_trajectorty('a')
plot_trajectorty('b')
plot_trajectorty('c')
plot_trajectorty('d')
plot_trajectorty('e')
plot_trajectorty('f')
plot_trajectorty('g')
plot_trajectorty('h')
plot_trajectorty('i')
plot_trajectorty('j')
plot_trajectorty('k')
plot_trajectorty('l')
plot_trajectorty('m')
plot_trajectorty('n')
plot_trajectorty('o')
plot_trajectorty('p')
plot_trajectorty('r')


# In[24]:

O = [pax.get_waiting_time()/60 for pax in CentralMonitor.all_passengers_offloaded["O"]]
print np.mean(O)
plt.hist(O)


# In[25]:

H = [pax.get_waiting_time()/60 for pax in CentralMonitor.all_passengers_offloaded["H"]]
print np.mean(H)
plt.hist(H)


# In[26]:

P = [pax.get_waiting_time()/60 for pax in CentralMonitor.all_passengers_offloaded["P"]]
print np.mean(P)
plt.hist(P)


# In[27]:

np.mean(np.array(O)), np.max(np.array(O)), np.min(np.array(O)), np.median(np.array(O))


# In[28]:

np.mean(np.array(P)), np.max(np.array(P)), np.min(np.array(P)), np.median(np.array(P))


# In[29]:

np.mean(np.array(H)), np.max(np.array(H)), np.min(np.array(H)), np.median(np.array(H))


# In[30]:

Param.max_tt


# In[428]:

fig = plt.figure(figsize=(18,120))

number_of_subplots = len(CentralMonitor.trains)

for i,v in enumerate(xrange(number_of_subplots)):
    tr = CentralMonitor.trains[i]
    v = v+1
    ax1 = plt.subplot(number_of_subplots,1,v)
    
    path_h = np.array(tr._load_history['H'])
    path_O = np.array(tr._load_history['O'])
    path_p = np.array(tr._load_history['P'])
    ax1.plot(path_p, color = "red")
    ax1.plot(path_O, color = "blue"  )
    ax1.plot(path_h, color = "green")
    ax1.set_xlim([0, 51000])
    ax1.set_ylim([0, 950])
    
    #http://stackoverflow.com/questions/4325733/save-a-subplot-in-matplotlib
#     extent = ax1.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
#     fig.savefig('foo'+str(i) + '.pdf', bbox_inches=extent.expanded(1.1, 1.2))

    


#     ax1.plot(x,y)


# In[ ]:




# In[ ]:




# In[431]:

fig = plt.figure(figsize=(18,120))

number_of_subplots = len(CentralMonitor.stations)

for i,v in enumerate(xrange(number_of_subplots)):
    cl = "red"
    if i == 10 : cl= "blue"
    tr = CentralMonitor.stations[i]
    v = v+1
    ax1 = plt.subplot(number_of_subplots,1,v)
    
    path_h = np.array([i  for v in tr.arriving_trains_loads.values() for i in v])
#     path_O = np.array(tr._load_history['O'])
#     path_p = np.array(tr._load_history['P'])
#     ax1.scatter(range(0, len(path_h)),path_h, color = cl)
    ax1.plot(path_h, color = cl)

    #     ax1.plot(path_O, color = "blue"  )
#     ax1.plot(path_h, color = "green")
    ax1.set_xlim([0, 200])
#     ax1.set_ylim([0, 950])
    


# In[429]:

fig = plt.figure(figsize=(18,120))

number_of_subplots = len(CentralMonitor.stations)

for i,v in enumerate(xrange(number_of_subplots)):
    cl = "red"
#     if i == 10 : cl= "blue"
    tr = CentralMonitor.stations[i]
    v = v+1
    ax1 = plt.subplot(number_of_subplots,1,v)
    
    path_h = np.array(tr.hist_queue["dh"])
    x = np.array(tr.hist_queue["t"])
    path_O = np.array(tr.hist_queue['do'])
    path_p = np.array(tr.hist_queue['dp'])
    ax1.scatter(x,path_p, color = cl)
    ax1.scatter(x, path_O, color = "blue"  )
    ax1.scatter(x, path_h, color = "green")
#     ax1.set_xlim([0, 200])
#     ax1.set_ylim([0, 950])


# In[430]:

fig = plt.figure(figsize=(18,120))

number_of_subplots = len(CentralMonitor.stations)

for i,v in enumerate(xrange(number_of_subplots)):
    cl = "red"
#     if i == 10 : cl= "blue"
    tr = CentralMonitor.stations[i]
    v = v+1
    ax1 = plt.subplot(number_of_subplots,1,v)
    
    path_h = np.array(tr.hist_queue["dh"])
    x = np.array(tr.hist_queue["t"])
    path_O = np.array(tr.hist_queue['do'])
    path_p = np.array(tr.hist_queue['dp'])
    dd = path_O - path_p
    ddd = path_O - path_h
    ax1.scatter(x,dd, color = cl)
    ax1.scatter(x, ddd, color = "blue"  )
#     ax1.scatter(x, path_h, color = "green")
#     ax1.set_xlim([0, 200])


# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[337]:

plt.plot([i  for v in tr.arriving_trains_loads.values() for i in v])


# In[ ]:




# In[ ]:




# In[733]:

plt.figure(figsize=(18,20))
acc = []
for tr in CentralMonitor.trains:
    path = np.array(tr._load_history['H'])
    path_O = np.array(tr._load_history['O'])
    plt.plot(path_O - path, label = tr.car_id)
    acc.append( RMSE(y=path_O, y_pred = path))
    axes = plt.gca()
    axes.set_ylim([-300, 300])
np.mean(acc)


# In[734]:

plt.figure(figsize=(18,20))
acc = []
for tr in CentralMonitor.trains:
    path = np.array(tr._load_history['P'])
    path_O = np.array(tr._load_history['O'])
    plt.plot(path_O - path)
    acc.append( RMSE(y=path_O, y_pred = path))
    axes = plt.gca()
    axes.set_ylim([-300, 300])
np.mean(acc)


# In[996]:

plt.figure(figsize=(18,20))

for tr in CentralMonitor.trains:
    path = np.array(tr._load_history['P'])
    path_O = np.array(tr._load_history['H'])
    plt.plot(path_O - path)
    axes = plt.gca()
    axes.set_ylim([-300, 300])


# In[736]:

tr = CentralMonitor.trains[10]


# In[737]:

plt.hist(tr._load_history['H'])


# In[738]:

plt.plot(tr._load_history['H'])


# In[739]:

plt.plot(tr._load_history['P'])


# In[740]:

plt.plot(tr._load_history['O'])


# In[741]:

c = [pax.get_travel_time()/60 for pax in CentralMonitor.all_passengers_offloaded]
print len(c)
plt.hist(c)


# In[ ]:

Param.max_tt/60


# In[ ]:

c = [pax.entry_station for pax in CentralMonitor.all_passengers_boarded]
print len(c)
plt.hist(c)


# In[ ]:

c = [pax.exit_station for pax in CentralMonitor.all_passengers_emptied_at_last]
# print c
print len(c)
plt.hist(c)


# should check that demand was created correctly

# In[146]:

c = [CentralMonitor.return_station_by_id(pax.entry_station) for pax in CentralMonitor.all_passengers_emptied_at_last]
d = [CentralMonitor.return_station_by_id(pax.exit_station) for pax in CentralMonitor.all_passengers_emptied_at_last]

for origin, destination in zip(c,d):
    if destination not in CentralMonitor.station_demands[origin].keys():
        print "logical error"
        print origin, destination
        break



# so no logical error here. They are not being offloaded properly

# In[147]:

b = [pax.get_waiting_time()/60 for pax in CentralMonitor.all_passengers_emptied_at_last]
print len(b)
plt.hist(b)


# In[ ]:




# In[296]:

d = CentralMonitor.passenger_denied_boarding


# In[297]:

len(d['O']), len(d['H']), len(d['P'])


# In[48]:

sts =[st[2].ids for st in d["O"]]
plt.hist(sts)
axes = plt.gca()
axes.set_ylim([0, 2000])


# In[151]:

p_sts =[st[2].ids for st in d["P"]]
plt.hist(p_sts)
axes = plt.gca()
axes.set_ylim([0, 2000])


# In[152]:

h_sts =[st[2].ids for st in d["H"]]
plt.hist(h_sts)
axes = plt.gca()
axes.set_ylim([0, 2000])


# In[ ]:




# In[153]:

h_sts =[st[1] for st in d["H"]]
plt.hist(h_sts)
axes = plt.gca()
axes.set_ylim([0, 600])
axes.set_xlim([9000, 16000])


# In[154]:

p_sts =[st[1] for st in d["P"]]
plt.hist(p_sts)
axes = plt.gca()
axes.set_ylim([0, 600])
axes.set_xlim([9000, 16000])


# In[155]:

sts =[st[1] for st in d["O"]]
plt.hist(sts)
axes = plt.gca()
axes.set_ylim([0, 600])
axes.set_xlim([9000, 16000])


# In[156]:

import seaborn as sns

plt.hist([sts, p_sts, h_sts], color=['r','b', 'g'], alpha=0.5)


# In[ ]:




# In[439]:

2*2


# In[ ]:




# In[443]:




# In[440]:

wts = defaultdict(list)
for station in Param.stations:
    pax = [pax for pax in CentralMonitor.all_passengers_offloaded["O"] if pax.entry_station == station]
    wts[station].append(np.mean([p.get_waiting_time() for p in pax]))
    
    pax = [pax for pax in CentralMonitor.all_passengers_offloaded["H"] if pax.entry_station == station]
    wts[station].append( np.mean([p.get_waiting_time() for p in pax]))
    


# In[441]:

(wts[513])


# In[442]:

sorted(wts.items(), key=lambda x: abs(np.diff(x[1])))


# In[160]:

temp = []
for k, v in wts.iteritems():
    if  v[0] - v[1] > 0:
        temp.append(v[0] - v[1])
print np.max(temp)
print np.mean(temp)


# In[163]:

temp_o = [pax[0].get_waiting_time() for pax in d['O']]
plt.hist(temp_o)
print np.mean(temp_o)/60
axes = plt.gca()
axes.set_ylim([0, 1800])
axes.set_xlim([100, 5000])


# In[164]:

temp_p = [pax[0].get_waiting_time() for pax in d['P']]
plt.hist(temp_p)
print np.mean(temp_p)/60

axes = plt.gca()
axes.set_ylim([0, 1800])
axes.set_xlim([100, 5000])


# In[165]:

temp_h = [pax[0].get_waiting_time() for pax in d['H']]
plt.hist(temp_h)
print np.mean(temp_h)/60
axes = plt.gca()

axes.set_ylim([0, 1800])
axes.set_xlim([100, 5000])


# In[166]:

fig = plt.figure(figsize=(18,12))
plt.hist([temp_o, temp_p, temp_h], color=['r','b', 'g'], alpha=0.5, )

# fig.savefig('foo'+str(i) + '.tiff')


# In[ ]:




# In[167]:

excessive_delays =  [pax[0] for pax in d['H'] if pax[0].get_waiting_time() > 4000]


# In[168]:

len(excessive_delays)


# In[169]:

plt.hist([pax.entry_station for pax in excessive_delays])


# In[171]:

plt.hist([pax.entry_time for pax in excessive_delays])


# In[172]:

plt.hist([pax.boarding_time for pax in excessive_delays])


# In[118]:

plt.hist([pax.exit_station for pax in excessive_delays])


# In[432]:

import seaborn as sns


# In[433]:


def compare_wt_by_station():
    all_df =pd.DataFrame()
    for level in ["O", "H", "P"]:
        O = [pax for pax in CentralMonitor.all_passengers_offloaded[level]]
        O_wait = [pax.get_waiting_time()/60 for pax in O]
        df = pd.DataFrame(np.transpose(np.array([O, O_wait])))
        df.columns = ["pax", "wt"]
        df["entry_station"] = df["pax"].apply(lambda x: x.entry_station)
        df["wt"] = pd.to_numeric(df.wt)
        gb = df[["entry_station", "wt"]].groupby("entry_station")
        all_df = pd.concat([all_df, gb.aggregate(np.mean)], axis = 1)
    return all_df


# In[434]:

df_wt = compare_wt_by_station()


# In[435]:

df_wt.columns = [ "O", "H", "P"]


# In[436]:

df_wt.reset_index(inplace=True)


# In[437]:

import matplotlib.ticker as ticker
# http://stackoverflow.com/a/36229671/2005352


# In[438]:

fb = df_wt.groupby('entry_station').mean()
ax = fb.plot(kind="bar", figsize=(18,18),  color=['b','g', 'r'], alpha = .5)
ax.set_xlabel("Station",fontsize=12)
ax.set_ylabel("Average waiting time",fontsize=12)
tick_spacing = 2
ax.yaxis.set_major_locator(ticker.MultipleLocator(tick_spacing))


# df_wt[[ "O", "H", "P"]].plot(kind="bar", figsize=(18,12),  color=['b','g'a, 'r'])


# In[185]:

fb = df_wt.groupby('entry_station').mean()
fb.plot.bar()


# In[182]:

df_wt.tail()


# In[304]:

a =[st for st in CentralMonitor.stations if st.ids == 703][0]
a


# In[ ]:




# In[310]:

p = df[df.entry_station==703].pax.values[0]


# In[311]:

p.entry_time, p.boarding_time, p.exit_time


# In[229]:

CentralMonitor.stations.index(a)


# In[233]:

[st.ids for st in (CentralMonitor.stations)]


# In[306]:

O = [pax for pax in CentralMonitor.all_passengers_offloaded["P"]]
O_wait = [pax.get_waiting_time() for pax in O]



# In[307]:

df = pd.DataFrame(np.transpose(np.array([O, O_wait])))
df.columns = ["pax", "wt"]


# In[308]:

df["entry_station"] = df["pax"].apply(lambda x: x.entry_station)


# In[309]:

df["wt"] = pd.to_numeric(df.wt)


# In[224]:

gb = df[["entry_station", "wt"]].groupby("entry_station")


# In[134]:

(gb.aggregate(np.mean))


# In[131]:

gb.aggregate(np.mean).plot(kind="bar")


# In[ ]:




# In[ ]:




# In[ ]:




# In[ ]:




# In[120]:

train_id = 'a'
train_x = CentralMonitor.train_trajectories[train_id]
t = [-i for i in range(len(train_x))]

x = np.repeat(range(0, Param.max_tt) ,np.ceil(len(train_x) / Param.max_tt))
plt.plot(x[:len(t)], train_x)

for station, x in Param.station_positions.iteritems():
    plt.axvline(x = x, color='r')


# In[121]:

max(train_x),


# In[ ]:




# In[14]:

stations = [Station(ids) for ids in Param.stations]


# In[28]:

station_demands = defaultdict(lambda : defaultdict(dict))
for idx, station in enumerate(stations[0:len(stations)-1]):
    origin_id =  station.ids
    for dest in stations[(idx+1):len(stations)]:
        dest_id = dest.ids
        demand = read_od_from_file(origin_id, dest_id)
        for ind, t in enumerate(range(0, Param.SIMULATION_TIME, 15*60)):
            station_demands[station][dest][t] = demand[ind]


# In[80]:

for ind, t in enumerate(range(0, Param.SIMULATION_TIME, 15*60)):
       print ind
       


# In[29]:

station_demands[stations[1]]


# In[26]:

station_demands = defaultdict(lambda : defaultdict(dict))


# In[30]:

dest_id


# In[31]:

origin_id


# In[6]:

mypath = "C:\\Users\\Peyman.n\\Dropbox\\Research\\projects\\Short_term_forcast\\R code\\data\\"
from os import listdir
from os.path import isfile, join
onlyfiles = [f for f in listdir(mypath) if isfile(join(mypath, f))]


# In[7]:

onlyfiles


# In[41]:

a = onlyfiles[1].split("_")
a


# In[73]:

def read_od_from_file(origin_id, dest_id, list_of_files = onlyfiles, data_path = data_path):
    Data = namedtuple("DATA", "oberved predicted historical")
    
    broken = map( lambda x:x.split("_"), onlyfiles)
    target = [i for i in broken if i[0] == str(origin_id) and i[1] == str(dest_id)]
    observed_file = "_".join([i for i in target if "observed" in i[2] ][0])
    predicted_file = "_".join([i for i in target if "prediction" in i[2] ][0])
    historical_file = "_".join([i for i in target if "historical" in i[2] ][0])
    
    temp = pd.read_csv(data_path+observed_file)
    observed_data = temp[temp.columns[1]].values
    
    temp = pd.read_csv(data_path+predicted_file)
    predicted_data = temp[temp.columns[1]].values
    
    temp = pd.read_csv(data_path+historical_file)
    historical_data = temp[temp.columns[1]].values
    
    data = Data (observed_data, predicted_data, historical_data)
    
    return data
    
    


# In[74]:

d = read_od_from_file(origin_id, dest_id)


# In[42]:

broken = map( lambda x:x.split("_"), onlyfiles)


# In[46]:

a = [i for i in broken if (i[0] == str(origin_id) and i[1] == str(dest_id))]
a


# In[58]:

a = [i for i in a if "observed" in i[2] ][0]


# In[59]:

a


# In[61]:

b= "_".join(a)
b


# In[64]:

c = pd.read_csv(data_path+b)
c


# In[68]:

c[c.columns[1]].values


# In[71]:

total = 0
for origin, v in CentralMonitor.station_demands_historical.iteritems():
    for k, j in v.iteritems():
        total += np.sum(j.values())
        


# In[72]:

total


# In[37]:

total


# In[39]:

total


# In[40]:

Param.stations[len(Param.stations)-1]


# In[75]:

O = set([pax for pax in CentralMonitor.all_passengers_offloaded["O"]])


# In[76]:

len(O)


# In[77]:

def find_trains_before_station(line, pt, trains):
    # this needs to be tested in the main code
    yet_to_arrive = []
    if line.geom_type == 'LineString':
        coords = line.coords[:] 
    else:
        coords = [geo.coords[:] for geo in line.geoms]
        coords = [item for sublist in coords for item in sublist]


    # Add the coords from the points
    coords += pt.coords
    
    # Calculate the distance along the line for each point
    dists = [line.project(Point(p)) for p in coords]
    # sort the coordinates
    coords = [p for (d, p) in sorted(zip(dists, coords))]
#     # get their orders
#     first_pt = coords.index(pt1.coords[:][0])
#     second_pt = coords.index(pt2.coords[:][0])
#     if first_pt > second_pt :
#         pt1, pt2 = pt2, pt1
    
    break_pt = find_index_of_point_w_min_distance(coords, pt.coords[:][0])

#     break_pt = coords.index(pt.coords[:][0])
    if break_pt == 0:
        # it is the first point on the line, "line_before" is meaningless
        line_before = None
    else:
        line_before = LineString(coords[:break_pt+1])
        
    if break_pt == len(coords)-1:
        # it is the last point on the line, "line_after" is meaningless
        line_after = None
    else:
        line_after = LineString(coords[break_pt+1:]) # so that it does not capture the point it's already on. deliberately done 
        # for this function
    
    
    if line_before != None:
        for train in trains:
            if line_before.distance(train.position) < 1e-10 :
                yet_to_arrive.append(train)
        
        return yet_to_arrive
    
    return "Line is None, this is the end point"
            
    
    


# In[63]:

def find_stations_after_train(line, stations, pt):
    yet_to_be_visited = {}
    if line.geom_type == 'LineString':
        coords = line.coords[:] 
    else:
        coords = [geo.coords[:] for geo in line.geoms]
        coords = [item for sublist in coords for item in sublist]


    # Add the coords from the points
    coords += pt.coords
    
    # Calculate the distance along the line for each point
    dists = [line.project(Point(p)) for p in coords]
    # sort the coordinates
    coords = [p for (d, p) in sorted(zip(dists, coords))]
#     # get their orders
#     first_pt = coords.index(pt1.coords[:][0])
#     second_pt = coords.index(pt2.coords[:][0])
#     if first_pt > second_pt :
#         pt1, pt2 = pt2, pt1
    
    break_pt = find_index_of_point_w_min_distance(coords, pt.coords[:][0])

#     break_pt = coords.index(pt.coords[:][0])
    if break_pt == 0:
        # it is the first point on the line, "line_before" is meaningless
        line_before = None
    else:
        line_before = LineString(coords[:break_pt+1])
        
    if break_pt == len(coords)-1:
        # it is the last point on the line, "line_after" is meaningless
        line_after = None
    else:
        line_after = LineString(coords[break_pt+1:]) # so that it does not capture the point it's already on. deliberately done 
        # for this function
    
    
    if line_after != None:
        for station, pos in stations.iteritems():
            if line_after.distance(pos) < 1e-10 and pos.distance(pt) > 1 : # so that it's not the same point
                yet_to_be_visited[station] = pos
        return yet_to_be_visited
    
    return "Line is None, this is the end point"
            
    
    


# In[67]:

def find_travel_time_btw_two_pts_FIXEDSPEED (pt1, pt2, speed):
    return distance_btw_two_points_on_a_line(pt1, pt2) / speed


# In[80]:

def move_train_one_dist(pt, distance = Train.SPEED, line = Param.central_line):
    
    if line.geom_type == 'LineString':
        coords = line.coords[:] 
    else:
        coords = [geo.coords[:] for geo in line.geoms]
        coords = [item for sublist in coords for item in sublist]


    # Add the coords from the points
    coords += pt.coords
    
    # Calculate the distance along the line for each point
    dists = [line.project(Point(p)) for p in coords]
    # sort the coordinates
    coords = [p for (d, p) in sorted(zip(dists, coords))]
#     # get their orders
#     first_pt = coords.index(pt1.coords[:][0])
#     second_pt = coords.index(pt2.coords[:][0])
#     if first_pt > second_pt :
#         pt1, pt2 = pt2, pt1
    
    break_pt = find_index_of_point_w_min_distance(coords, pt.coords[:][0])

#     break_pt = coords.index(pt.coords[:][0])
    if break_pt == 0:
        # it is the first point on the line, "line_before" is meaningless
        line_before = None
    else:
        line_before = LineString(coords[:break_pt+1])
        
    if break_pt == len(coords)-1:
        # it is the last point on the line, "line_after" is meaningless
        line_after = None
    else:
        line_after = LineString(coords[break_pt+1:]) # so that it does not capture the point it's already on. deliberately done 
        # for this function
    
    
    if line_after != None:
        # have checks for the end on line
        np = line_after.interpolate(distance)
        
        
        return np
    
    return "Line is None, this is the end point"
            
    
    


# In[ ]:



