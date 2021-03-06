# -*- coding: utf-8 -*-
"""
Created on Mon Jul 10 15:02:10 2017

@author: Peyman
"""
from __future__ import division 
from config import *
from Param_Central import Param_Central, Param_Central_WE, Param_Central_EW
from Param_Victoria import Param_Victoria, Param_Victoria_NS, Param_Victoria_SN

import gc

class Train(object):
    # https://tfl.gov.uk/corporate/about-tfl/what-we-do/london-underground/rolling-stock
    CAPACITY = 892 
    NUM_SEATS = 324
    NUM_DOORS = 24
    # https://tfl.gov.uk/corporate/about-tfl/what-we-do/london-underground/facts-and-figures
    SPEED = 9 # meters/sec
    
    
    inv_project = partial(
                    pyproj.transform,
                    pyproj.Proj(init='epsg:27700'), #  source coordinate system
                    pyproj.Proj(init='epsg:4326')) # destination coordinate system

    def __init__(self, car_id, direction, line, position = None, distance_to_next_station = None, next_station_id=None, prev_station_id=None, time_to_next_station = 1000000):
        
        ####
        
        # These should all be updated when they reach a garage at the other end
        
        self.direction = direction
        self.line = line
        self._number_dispached = None
        self._number_of_times_added_to_garage = 0
#        self.is_in_garage = True
        
        if self.line == "Central":
            if self.direction == "EW":
                self.Param = Param_Central_EW()
            elif self.direction == "WE":
                self.Param = Param_Central_WE()
                
        elif self.line == "Victoria":
            if self.direction == "NS":
                self.Param = Param_Victoria_NS()
            elif self.direction == "SN":
                self.Param = Param_Victoria_SN()
        ####
        self.car_id = car_id
        self.current_station_id = None # to be set when it arrives at a station 
        self.prev_station_id = prev_station_id
        self.next_station_id = next_station_id # KEEP
        self.has_arrived_at_station = False
        self.next_NEXT_station_id = None
        self.time_to_next_NEXT_station = None
        ###
        self.train_in_front = None # train object
        self.train_in_back = None
        self.distance_to_train_in_back = None # each train only tracks its distance to the trailing train. That other train will
        # call this trains distance when it needs to adjust it 
        self.MINIMUM_DIST_BTW_TRAINS = 300 # meters 
        ###
        self.next_platform = None
        self.next_next_platform = None        
        self.DEMAND_LEVEL = None # in list, cause it reduces the code change
        ###
        self.passengers = defaultdict(list)
        self.time_to_next_station = time_to_next_station # KEEP
        self.initial_departure_time = 1000000 
        self.is_in_service = False
        self.it_has_reached_a_station = False 
        ## bookkeeping; will need them for realtime updates
        self.just_boarded = []
        self.just_offloaded = []
        self._load_history = defaultdict(list)
        ## updates in realtime
        self.updated_next_station = None
        self.updated_prev_station = None
        self.position = position
        self.distance_to_next_station = distance_to_next_station
        self.distance_to_the_next_NEXT_station = None
        ##
        self.waiting = False
        self.current_speed = None
        self.time_started_waiting = None
        self.waiting_to_enter_station = False
        self.waiting_to_leave_station = False
        self.dwell = False
        self.dwell_time_spent = 10000
        self.DWELL = 15 # seconds
        self._dispatch_times = []
        ## 
        self.stations_visited = {}
        self._saved_states = {}
        # for other iterations
        self._save_detailed_state_for_later = None
        # for debug purposes, remove 
        self._dist_to_front = []
        self._dist_to_back = []
        self._next_stations_debugging = []
        self._speeds_debugging = []
#         self.log_file = open((self.car_id)  + ' workfile.txt', 'w') # + str(random.randint(0,100000))
        
    def set_demand_level(self, level):
        if level in ["O", "P", "H"]:
            self.DEMAND_LEVEL = [level] 
        else:
            raise "DEMAND LEVEL IS NOT IN ONE OF PREDEFINED CATEGORIES"
            
    def _compute_train_prob_color(self, prob):
        if prob <= 0.3 :
            return "red"
        elif prob <= 0.8:
            return "yellow"
        else:
            return "green"
            
            
    def _compute_boading_probability(self, pax_queue, pax_onboard_queue):
        
        remaining_cap = self.CAPACITY - len(pax_onboard_queue)
        
        if remaining_cap > len(pax_queue) or len(pax_queue) == 0  :
            return 1
        else: 
            prob_of_boarding = remaining_cap / len(pax_queue)   
            #
#==============================================================================
#             if prob_of_boarding < 1 :
#                 print "remaining_cap ", remaining_cap
#                 print "len(pax_queue)", len(pax_queue)
#                 print "division ",  remaining_cap / len(pax_queue) 
#==============================================================================
            #
            return prob_of_boarding
        
    def load_passenger(self, central_monitor_instance,  t, station):
        
#        print 'boarding at time ', t
        # don't keep track of those who were previously boarded 
        self.just_boarded = []
        #
#        station.is_occupied = True
        denied = False
        i = 0
        for level in self.DEMAND_LEVEL:
            if len(self.passengers[level]) < self.CAPACITY:
                # add functionality for calculating the TRUE probability of boarding the train
                prob_of_boarding = self._compute_boading_probability(station.queue[level], self.passengers[level])
                self.boarding_prob_color = self._compute_train_prob_color(prob_of_boarding)
                
                
                if prob_of_boarding < 1:
                   print("prob_of_boarding " + str( prob_of_boarding)) 
                   print "station name ", station.ids, station.direction, station.line
                #==============================================================================

                info = {'car_id' : self.car_id, 
                        'boarding_prob_color' : self.boarding_prob_color, 
                        'prob_of_boarding' : prob_of_boarding}
                        
                station.train_colors[self.car_id].append(info)
     
   
                #==============================================================================
                
                # read other upcoming trains colors 
                
                if self.CAPACITY - len(self.passengers[level]) < len(station.queue[level]): 
                    print "DENIED BOARDING for train "+ self.car_id + " at level " + level + " for station " + str(station.ids)
                    print prob_of_boarding
                    denied = True
                    
                    
                while len(self.passengers[level]) < self.CAPACITY and len(station.queue[level]) > 0:
                    pax = station.queue[level].pop()
               
                    # must add the color for the other upcoming trains as well
                    if pax.should_it_try_to_board(station.upcoming_trains, info): 
                    
                        pax.boarding_time = t
                        pax.boarding_train_direction = self.direction
                        self.passengers[level].append(pax)
                        i += 1
                        self.just_boarded.append(pax)
    
                        central_monitor_instance.all_passengers_boarded.append(pax)
                    else:
                        # decided to wait (not board this train)
                        # go back to station queue
#                        print "DECIDED TO NOT BOARD THE TRAIN "
                        station.secondary_queue[level].append(pax)
                        pax.number_of_denied_boardings_out_of_choice[level] += 1
                        central_monitor_instance.passenger_denied_boarding_out_of_choice[level].append([pax, t, station])                        
                
                # now pax who decided to wait, and entered the secondary queue, have to be re-inserted
#==============================================================================
#                 print station.secondary_queue[level]
#                 print station.queue[level]
#==============================================================================
                station.queue[level].extendleft(station.secondary_queue[level])
                # empty the secondary queue
                station.secondary_queue[level].clear()
                
                
                if denied :
                    # some pax waiting on the platform will be denied boarding
                    j=0
                    for pax in station.queue[level]:
                        pax.number_of_denied_boardings[level] += 1
                        central_monitor_instance.passenger_denied_boarding[level].append([pax, t, station])
                        j+=1
#                     print str(j)+ " people couldn't board the train at level " + level
            else:
                # if after unloading the passengers, there is still no room for new pax to board
                denied = True
                info = {'car_id' : self.car_id, 
                        'boarding_prob_color' : 'red', 
                        'prob_of_boarding' : 0}
                        
                station.train_colors[self.car_id].append(info)
                
                for pax in station.queue[level]:
                        pax.number_of_denied_boardings[level] += 1
                        central_monitor_instance.passenger_denied_boarding[level].append([pax, t, station])
#                 print "train is full"
#                 print str(len(station.queue[level]))+ " people couldn't board the train"
            
#            print "boarded ", str(i), "passengers at level ", level
#            print "train load is ", str(self.get_load(level))
            
            
#         # add dwell time
#         self.dwell = True
#         self.dwell_time_spent = 0
        
        
        
        station.time_since_occupied = 0
        return(i)
#        station.is_occupied = False
        
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
#        if station.time_since_occupied >= min_buffer_time:
        if station.is_occupied :
            return False
        return True


    def get_load(self, level):
        return len(self.passengers[level])
    
    def offload_passengers(self, central_monitor_instance, station_id, offload_time, god):
        # reset the list
        self.just_offloaded = []
        #
        for level in self.DEMAND_LEVEL:
            i = 0
#             print "before", len(self.passengers[level])
            # THIS IS EXTREMELY IMPORTANT http://stackoverflow.com/a/1207427/2005352
            for pax in self.passengers[level][:]:
                if pax.next_destination == station_id:
                    self.passengers[level].remove(pax)
                    # possible transfer
                    pax.update(offload_time)
                    if pax.next_destination is not None:
                        # it needs to access central monitor of the other line....
#                         print "train direction", self.direction
#                         print "next_dest", pax.next_destination
                        intersecting_line_name =  central_monitor_instance.return_name_of_intersecting_line(self.line)
#                         print "intersecting_line_name", intersecting_line_name
                        other_central_monitor = god.monitors[intersecting_line_name]
                        
                        station = other_central_monitor.return_station_by_id(station_id)
#                         if station.line == "Victoria":
                    
#                             print "train direction", self.direction
#                             print "next_dest", pax.next_destination
#                             print "intersecting_line_name", intersecting_line_name
#                             print "station name", station.ids
#                             print "staion line", station.line
                
                        ## need access to station object, the only guys that has it is centralmonitor


                        # set entry time of this pax as a function of transfer time at this specific station
                        # needs to know which platform to join 
                        platform = station.get_platform_id_matching_target_destination(pax.next_destination, station.ids)
#                         print "platform", platform
                        transfer_time = station.platforms[platform].get_transfer_time(self.line)
                        pax.reassign_info(station_id, offload_time + transfer_time)
#                         print "joining platform ", platform, " of station ", station.ids, " transferring from station ", station_id, " direction ", self.direction
#                         print "before joining queue ", len(station.platforms[platform].pax_list[level]) 
                        station.platforms[platform].pax_list[level].append(pax)
#                         print "after joining queue ", len(station.platforms[platform].pax_list[level]) 
                        
                        
                     # VERY ad-hoc, just trying to see the effect on memory 
                    else:                       
#                       del pax
                       pass
                    # how to keep track of this 

                    central_monitor_instance.all_passengers_offloaded[level].append(pax)                    
#                    self.just_offloaded.append(pax)
                    i += 1
#            gc.collect()   
            return(i)
#             print "offloaded ", str(i), "passengers", " ", level
#             print "after", len(self.passengers[level]), " ", level
        
    def empty_load(self, central_monitor_instance, t):
        # for the last stop, so that it starts fresh at the beginnig of the line again
        # should set pax exit time and station
        for level in self.DEMAND_LEVEL:
            for pax in self.passengers[level]:
                pax.exit_time = t
                pax.exit_station = self.Param.stations[len(self.Param.stations)-1]

                central_monitor_instance.all_passengers_offloaded[level].append(pax)

                central_monitor_instance.all_passengers_emptied_at_last[level].append(pax)

            self.passengers = defaultdict(list)
        
    def get_next_station_id(self):
        # if this is not the last stop
        if self.current_station_id != self.Param.terminal_station:
            
            current_index = self.Param.stations.index(self.current_station_id)
            next_station_id = self.Param.stations[current_index + 1]
            return next_station_id 
        else:
            # terminal station
            return None
            
    def get_next_NEXT_station_id(self):
        # MUST CALL get_next_station_id() BEFORE THIS
        # if the next stop is not the last stop
        if self.next_station_id != self.Param.terminal_station:
            
            current_index = self.Param.stations.index(self.current_station_id)
            next_next_station_id = self.Param.stations[current_index + 2]
            return next_next_station_id 
        else:
            # terminal station
            return None 

            
    def get_travel_time_to_next_station(self):
        # make it stochastic
        base = self.Param.station_travel_times[self.current_station_id][self.next_station_id]
#         variable = int(random.normalvariate(200,300))
#         while 0.5 * base < abs(variable) :
#             variable = int(random.normalvariate(200,300))
            
        tt = base #+ variable 
        assert(tt > 0)
        return tt 
    
    def start_waiting (self, central_monitor_instance, number_of_boarding, number_of_alighting):
        self.waiting = True
        self.DWELL = self._compute_dwell_time(number_of_boarding, number_of_alighting)
        self.time_started_waiting = 0
        
        current_platform = central_monitor_instance.return_station_by_id(self.current_station_id).platforms[self.direction]
        current_platform._dwell_times.append(self.DWELL)
        
    def keep_waiting (self):
        self.time_started_waiting += 1
        
    def _compute_dwell_time(self, number_of_boarding, number_of_alighting):
        F = 1.05
        T = self.get_load(self.DEMAND_LEVEL[0])
        D = self.NUM_DOORS
        S = self.NUM_SEATS      
        B = number_of_boarding
        A = number_of_alighting
        assert A is not None
        assert B is not None
        block_1 = 1 + (F/35) * ((T-S)/D)
        block_3 = 0.027 * (F*B/D) * (F*A/D)
        block_2 = np.power((F*B/D), 0.7) + np.power((F*A/D), 0.7) + block_3
        
        SS = 15 + 1.4 * block_1 * block_2
        return SS
                
        
        
    def should_it_keep_waiting(self, waiting_time = 90):
        # returns True if t <= waiting time, proxy for inaction for a while
        if self.time_started_waiting <= self.DWELL :
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
        for level in self.DEMAND_LEVEL:
            exiting[level] = [pax  for pax in self.passengers[level] if pax.exit_station == self.next_station_id]
            adj[level] = int(self.get_load(level) - len(exiting[level]))
        return(adj)
    
    def start_over(self, central_monitor_instance, t, garage):
        # after offloading pax at the last stop
        self.empty_load(central_monitor_instance, t)
        # go to the last garage
        self.position = self.Param.station_positions[self.Param.last_garage_name] # CHANGE
        garage.add_to_garage(self, t=t )
        # it should wait for a while before coming back into the system
        # another approach could be to kill this and replace it with a new one at the origin,
        # this delegates matters into the setup process
    



    def _move_train_one_dist(self, pt, distance, line_all = None):
        if line_all is None:
            line_all = self.Param.line
        line = line_all
        
        if self.direction == self.Param.PRIMARY_DIRECTION:
            dist_from_start_node = line.project(pt)
            if line.length > distance:
                end_point = line.interpolate(distance + dist_from_start_node)
                return (end_point)
            else:
                print " moved passed the end of line, should've caught it before calling this function! "
                
        elif self.direction != self.Param.PRIMARY_DIRECTION:
            dist_from_end_node = line.project(pt)
            if line.length > distance:
                end_point = line.interpolate(dist_from_end_node - distance)
                return (end_point)
            else:
                print " moved passed the end of line, should've caught it before calling this function! "

    
    def _get_distance_to_front_train(self):
        # if there is a train in front of it 
        if self.train_in_front:
            
#==============================================================================
#             print self.car_id
#             print self.train_in_front.car_id
#             print self.train_in_front.distance_to_train_in_back
#             print self.MINIMUM_DIST_BTW_TRAINS
#==============================================================================
            
            # get the distance to it
            current_dist = self.train_in_front.distance_to_train_in_back
            if current_dist < self.MINIMUM_DIST_BTW_TRAINS:
                pass 
#==============================================================================
#                 print "####################"
#                 print "minimum distance violated "
#                 print "car id ", self.car_id
#                 print "front car id ", self.train_in_front.car_id
#                 print "current dist ", current_dist 
#==============================================================================
#==============================================================================
#             assert(current_dist >= self.MINIMUM_DIST_BTW_TRAINS)
#==============================================================================
            return current_dist
        else:
            # large number! 
            return 10000000
    
    
    def move(self, t, distance = None):
        
        assert self.is_in_service == True
        
        if distance == None: 
            try :
                distance = self.current_speed
            except AttributeError :
                print "ERROR"
                print self.car_id
                print self.prev_station_id
                print self.current_station_id
                print self.next_station_id
                distance = self.current_speed
                
        assert distance is not None
        assert distance > 0 
        
        # check whether or not it has reached the station, or will reach and pass it if it moves, before calling this function
        current_dist_to_front_train = self._get_distance_to_front_train()
        # if there is NOT enough space btw this and the train in front once the train is moved
        if current_dist_to_front_train :
            if current_dist_to_front_train - distance < self.MINIMUM_DIST_BTW_TRAINS:
                 # adjust speed (i.e. distance varaible)
    #==============================================================================
    #             print "####################"
    #             print "car_id ", self.car_id
    #             print "current distance to front train ", current_dist_to_front_train
    #             print "self speed ", distance
    #             print "is the front car waiting? ", self.train_in_front.waiting
    #             print "front train id ", self.train_in_front.car_id
    #             print "fron train distance to the trailing train ", self.train_in_front.distance_to_train_in_back
    #==============================================================================
                
                # THEN JUST STOP
                return 
            
                # WELL, THIS SORT OF HIDES THE PROBLEM, NO?????
                distance =  current_dist_to_front_train - self.MINIMUM_DIST_BTW_TRAINS
                if distance < 0 : distance = 0
                print "adjusted distance ", distance
        assert(distance >= 0)
                
#         print self.position
        
        # distance = speed in what follows
        # it has not arrived yet
        if self.distance_to_next_station > distance:
            self.distance_to_next_station -= distance
            # assign time from a new
            time_to =  self.distance_to_next_station / distance 
            self.time_to_next_station = time_to
            #==============================================================================
            # update platform's board 
#            try:
            self.next_platform.upcoming_trains[self.car_id][0] = self.time_to_next_station
#==============================================================================
#             except AttributeError:
#                 print "Error"
#                 print "car id ", self.car_id
#                 print "distance from garage", self.distance_from_garage
#                 print "distance_to_next_station", self.distance_to_next_station
#                 print "speed", self.current_speed
#                 print "time to next stations ", self.time_to_next_station
#                 print "next_station_id", self.next_station_id
#                 print "prev_station_id", self.prev_station_id
#==============================================================================
            #==============================================================================
            if self.distance_to_the_next_NEXT_station : # so if the next next station is garage, and therefore distance is None
                self.distance_to_the_next_NEXT_station -= distance
                self.time_to_next_NEXT_station -= 1 # this is second based, so it should workd this 
                #==============================================================================
                self.next_next_platform.upcoming_trains[self.car_id][0] = self.time_to_next_NEXT_station
            #==============================================================================
                
                
                
            self.position = self._move_train_one_dist(pt = self.position, distance=distance)
            # keep track of how far it has come from the garage
            self.distance_from_garage += distance
            #==============================================================================
            if self.train_in_back : 
                # update distance to the trailing train 
    #==============================================================================
    #             print "distance to the trailing train Before: ", self.distance_to_train_in_back
    #             print "distance ", distance
    #==============================================================================
                self.distance_to_train_in_back += distance
    #==============================================================================
    #             print "distance to the trailing train After : ", self.distance_to_train_in_back
    #==============================================================================
            if self.train_in_front :
                self.train_in_front.distance_to_train_in_back -= distance 
            #==============================================================================
            
        else:
            # think it is redundant, since has_it_reached_a_station has this logic as well
            self.it_has_reached_a_station = True 
            the_dist = self.distance_to_next_station 
            self.distance_from_garage += the_dist
            self.position = self._move_train_one_dist(pt = self.position, distance=the_dist)
#            print "it has reached a station ", self.current_speed, self.current_station_id
#==============================================================================
#             self.distance_to_next_station = 0 
#             self.time_to_next_station = 0 
#==============================================================================
        
        
#==============================================================================
#             print "car id ", self.car_id
#             print "time to next NEXT platfrom ", self.time_to_next_NEXT_station
#==============================================================================
            
           
        
            
#==============================================================================
#     def has_it_reached_a_station(self, distance=None):
#         if distance == None: distance = self.current_speed
#         # arriving and passing the station
#         if self.distance_to_next_station <= self.current_speed:
# #         or (self.distance_to_next_station <= self._move_train_one_dist(self.position, distance = self.distance_to_next_station)):
#             return True
#         return False
#==============================================================================
        
            
    def arrive_at_station(self, t, central_monitor_instance, line_all = None):
        

        if line_all is None:
            line_all = self.Param.line
        # set current station id
        self.current_station_id = self.next_station_id #  it has arrived at the next station
      
#         self.position  = station.position
        self.position = line_all.interpolate(line_all.project(self.position) + self.distance_to_next_station)
#         self.position = self.Param.station_positions[self.current_station_id]
        # update the status that has reached a station, and will be there for a few seconds
#         self.has_arrived_at_station = True
        self.stations_visited[t] = self.current_station_id
        
        # upon arrival at the platform, remove it from the upcoming list
        # exception is the first station, since it was not added to the upcoming trains list upon dispatching from the garage
        if self.prev_station_id != self.Param.garage_name:
            self._remove_train_from_platform_upcoming(central_monitor_instance, self.current_station_id, t)
        
        
        
    def unload_passengers(self, central_monitor_instance, t, god):
        number_of_alights = self.offload_passengers(central_monitor_instance, self.current_station_id, t, god)
        return number_of_alights
        
    def board_passengers(self,central_monitor_instance,  t):
        # remember to first call unload passengers
        # station = platform here 
        current_station = central_monitor_instance.return_station_by_id(self.current_station_id).platforms[self.direction]

        # check if this is the last station. 
        if self.current_station_id != self.Param.terminal_station:

            current_station.hist_queue["dh"].append(len(current_station.queue['H']))
            current_station.hist_queue["dp"].append(len(current_station.queue['P']))
            current_station.hist_queue["do"].append(len(current_station.queue['O']))
            current_station.hist_queue["t"].append(t)
            
            # add functionality for calculating the true probability of boarding the train
                        
            
            # board pax
            number_of_boardings = self.load_passenger(central_monitor_instance, t, current_station)
            return number_of_boardings
        else:
            # if it is the last station
#             self.start_over(t=t)
            return 0 
    
    def _add_train_to_platform_upcoming(self, central_monitor_instance, station_id, time_to_station, t= None):
        # add this train to the appropriate platform's upcoming trains 
        next_station_instance = central_monitor_instance.return_station_by_id(station_id)
        next_platform_instance = next_station_instance.platforms[self.direction]  
        # read the train's color
        # if this is NOT the first run, and hence the colors had been recorded previously
        if next_platform_instance.imported_train_colors:
            if self.car_id not in next_platform_instance.upcoming_trains.keys() : # this is the first time  (i.e. never been next_next)
                try :
                    train_info = next_platform_instance.imported_train_colors[self.car_id].popleft()
#==============================================================================
#                     print "#############################################"
#                     print "nex_platform_instance_id" , next_platform_instance.ids
#                     print " next_platform_instance.upcoming_trains, before  ", next_platform_instance.upcoming_trains  
#                     print "#############################################"
#==============================================================================
                except: 
                    # now that I know that this works properly, let's change it so that it assumes green light 
                    # for the trains not seen yet. It won't ever be used, as trains will not get there in real world
                    train_info = {'car_id' : self.car_id, 
                        'boarding_prob_color' : 'green', 
                        'prob_of_boarding' : 1}
                        
#==============================================================================
#                     print "sth went wrong reading train info"
#                     print "current station id ", self.current_station_id
#                     print " next station id ", station_id
#                     print "time to station " , time_to_station
#                     print "platform ", next_platform_instance.ids, next_platform_instance.direction
#                     print "car id ", self.car_id
#                     print "next_platform_instance.imported_train_colors keys", next_platform_instance.imported_train_colors.keys()
#                     print "next_platform_instance.imported_train_colors", next_platform_instance.imported_train_colors
#                     print "upcoming next ", next_platform_instance.upcoming_trains      
#                     if t :
#                         print " t is ", t
#                     next_platform_instance.imported_train_colors[self.car_id].popleft()                
#==============================================================================
                    
                next_platform_instance.upcoming_trains[self.car_id] = [time_to_station, train_info]
#==============================================================================
#                 print "#############################################"
#                 print "nex_platform_instance_id" , next_platform_instance.ids
#                 print " next_platform_instance.upcoming_trains, after  ", next_platform_instance.upcoming_trains  
#                 print "#############################################"
#==============================================================================

        else :
            # This is the first run, and hence the train colors do not yet exist 
            next_platform_instance.upcoming_trains[self.car_id] = [time_to_station, None]

        
        
    def _remove_train_from_platform_upcoming(self, central_monitor_instance, station_id, t):
        # upon arrival at the platform, remove it from the upcoming list 
        current_station_instance = central_monitor_instance.return_station_by_id(station_id)
        current_platform_instance = current_station_instance.platforms[self.direction]
        
#==============================================================================
#         print (current_platform_instance.upcoming_trains)
#         print(current_platform_instance.direction)
#         print "car ID : ", self.car_id
#         if self.train_in_front :
#             print "next car ID : ", self.train_in_front.car_id
#         if self.train_in_back :
#             print "trailing car ID :", self.train_in_back.car_id
#             print "distance to the trailing train : ", self.distance_to_train_in_back
#         
#         print self.current_station_id
#         print (self.prev_station_id )
#==============================================================================
        try:
            del current_platform_instance.upcoming_trains[self.car_id]
        except:
            print "ERROR"
            print "car id ", self.car_id
            print "ids", current_platform_instance.ids
#            print "imported_train_colors", current_platform_instance.imported_train_colors
#            print "upcoming_trains", current_platform_instance.upcoming_trains
            print "next_station_id", self.next_station_id
            print "current station id", self.current_station_id
            print "next_NEXT_station_id", self.next_NEXT_station_id
            print "prev_station_id", self.prev_station_id
            print central_monitor_instance.line
            print "direction", self.direction
            print "Param", self.Param
#            print "upcoming_trains", current_platform_instance.upcoming_trains
            print "it_has_reached_a_station ", self.it_has_reached_a_station   
            print "t is ", t
            
            
            del current_platform_instance.upcoming_trains[self.car_id]
        
    def depart_station(self, central_monitor_instance, t):
        self.waiting = False
        #
        self.it_has_reached_a_station = False 
        
        #        
        
#==============================================================================
#         station = central_monitor_instance.return_station_by_id(self.current_station_id).platforms[self.direction]
#         station.is_occupied = False
#==============================================================================
        
#        central_monitor_instance.train_trajectories[self.car_id].append(self.distance_from_garage)
        
        for level in self.DEMAND_LEVEL:
            
            self._load_history[level].append(self.get_load(level))
            
        if self.current_station_id == self.Param.terminal_station:
            # if it is the last station
            self.start_over(central_monitor_instance,  garage=      central_monitor_instance.return_garage_of_opposite_direction(self.direction), t=t)  
            
        else:
            
            
            # get the next station id
            self.next_station_id = self.get_next_station_id()
            
            self._next_stations_debugging.append(self.next_station_id )
            # get the next next station id 
            self.next_NEXT_station_id = self.get_next_NEXT_station_id()
            # get distance to next station
            self.distance_to_next_station = self.Param.station_distances[self.current_station_id][self.next_station_id]
            # get time to next station
            self.time_to_next_station = self.get_travel_time_to_next_station()
            assert(self.time_to_next_station > 0)
            #==============================================================================

            # draw a random speed 
#            print self.current_station_id, self.next_station_id
            speed_dist = self.Param.consecutive_speeds[self.current_station_id][self.next_station_id][0]
            
            if type(speed_dist) == float : 
                self.current_speed = speed_dist
                print "float speed ", speed_dist, self.current_station_id, self.next_station_id
            else:
                if self.direction in ["SN", "NS"]:
                    self.current_speed = np.mean(speed_dist.rvs(5))
                else:
                    self.current_speed = np.mean(speed_dist.rvs(3))
                while self.current_speed  < 4 :
                    print "low speed"
                    self.current_speed = np.mean(speed_dist.rvs(3))
                    
            self._speeds_debugging.append(self.current_speed)
            #==============================================================================

            # add this train to the appropriate platform's upcoming trains 
            self._add_train_to_platform_upcoming(central_monitor_instance, self.next_station_id, self.time_to_next_station,t )
            #==============================================================================
            # save a reference to this platform 
            _next_station_instance = central_monitor_instance.return_station_by_id(self.next_station_id)
            _next_platform_instance = _next_station_instance.platforms[self.direction]
            self.next_platform = _next_platform_instance
            #==============================================================================
            
            # get distance and time to the next NEXT station
            if self.next_NEXT_station_id != None:
                
                self.distance_to_the_next_NEXT_station = self.distance_to_next_station + self.Param.station_distances[self.next_station_id][self.next_NEXT_station_id]     
                
                self.time_to_next_NEXT_station = self.time_to_next_station + self.Param.station_travel_times[self.next_station_id][self.next_NEXT_station_id]
                
                # add this train to the appropriate platform's upcoming trains 
                self._add_train_to_platform_upcoming(central_monitor_instance, 
                                                     self.next_NEXT_station_id, self.time_to_next_NEXT_station, t )
                #==============================================================================
                # save a reference to this platform 
                _next_next_station_instance = central_monitor_instance.return_station_by_id(self.next_NEXT_station_id)
                _next_next_platform_instance = _next_next_station_instance.platforms[self.direction]
                self.next_next_platform = _next_next_platform_instance
                #==============================================================================
            else : 
                self.distance_to_the_next_NEXT_station = None # since the next next station is the garage, so no point is keeping this
                self.time_to_next_NEXT_station = None
            
                        
            self.prev_station_id = self.current_station_id
            
    def save_state_for_other_iterations(self):
        
        ''' 
        SHOULD NOT PASS OBJECTS, SINCE THEY ARE DIFFERENT AND EVERYTHING WILL BREAK
        
        '''
        # append to end of the queue
        info = {'position': self.position,
                'current_station_id': self.current_station_id,
                'prev_station_id' : self.prev_station_id,
                'next_station_id': self.next_station_id,
                'next_NEXT_station_id' : self.next_NEXT_station_id, 
                'time_to_next_station' : self.time_to_next_station, 
                'time_to_next_NEXT_station' : self.time_to_next_NEXT_station, 
                'waiting' : self.waiting ,
                'time_started_waiting': self.time_started_waiting,
                'distance_to_next_station' : self.distance_to_next_station,
                'distance_to_the_next_NEXT_station': self.distance_to_the_next_NEXT_station,
#                'next_next_platform' : self.next_next_platform,
#                'next_platform' : self.next_platform,
                'train_in_front' : self.train_in_front,
                'train_in_back' : self.train_in_back,
                'distance_to_train_in_back': self.distance_to_train_in_back,
                'is_in_service': self.is_in_service,
                'it_has_reached_a_station': self.it_has_reached_a_station,
                'Param' : self.Param,
                "direction": self.direction,
                "current_speed" : self.current_speed,
                "distance_from_garage" : self.distance_from_garage,
                "DWELL": self.DWELL,
                "dwell": self.dwell,
                "dwell_time_spent": self.dwell_time_spent,
                "line" : self.line,
                "is_in_garage" : self.is_in_garage,
                "_number_dispached" : self._number_dispached
                
                
                
                }
                
        self._save_detailed_state_for_later = info
        
    def read_state_from_other_iterations(self, info, central_monitor_instance) : 
        self.position = info['position']
        self.current_station_id = info['current_station_id']
        self.next_station_id = info['next_station_id']
        self.next_NEXT_station_id = info['next_NEXT_station_id']
        self.time_to_next_station = info['time_to_next_station']
        self.time_to_next_NEXT_station = info['time_to_next_NEXT_station']
        self.waiting = info['waiting']
        self.time_started_waiting = info['time_started_waiting']
        self.distance_to_next_station = info['distance_to_next_station']
#        self.next_platform = info['next_platform']
#        self.next_next_platform = info['next_next_platform']
        self.distance_to_the_next_NEXT_station = info['distance_to_the_next_NEXT_station']
        self.it_has_reached_a_station = info['it_has_reached_a_station']
        self.prev_station_id = info['prev_station_id']
        self.distance_to_train_in_back = info['distance_to_train_in_back']
        self.is_in_service = info['is_in_service']
        self.Param = info["Param"]
        self.direction = info["direction"]
        self.current_speed = info["current_speed"]
        self.distance_from_garage = info["distance_from_garage"]
        self.DWELL = info["DWELL"]
        self.dwell = info["dwell"]
        self.dwell_time_spent = info["dwell_time_spent"]
        self.line = info["line"]
        self.is_in_garage = info["is_in_garage"]
        self._number_dispached = info["_number_dispached"]
               
        if info['train_in_back'] is None : 
            self.train_in_back = None
        else:
            tr = central_monitor_instance.train_lookup_by_id[info['train_in_back'].car_id]
            assert tr is not None 
            self.train_in_back = tr
            
            
        if info['train_in_front'] is None : 
            self.train_in_front = None
        else:
            tr = central_monitor_instance.train_lookup_by_id[ info['train_in_front'].car_id]
            assert tr is not None 
            self.train_in_front = tr    
            
        if self.is_in_garage == True:
             # , and it's not in the garage 
            if self not in central_monitor_instance.garages[self.direction].queue :
                 central_monitor_instance.garages[self.direction].queue.append(self)
                 
             
            
            
#==============================================================================
#         self._saved_positions =          
#==============================================================================
    def _record_state_for_plotting(self, t, central_monitor_instance):
        '''
        Always record this. Want to use it for plotting positions        
        '''
        central_monitor_instance.train_trajectories[self.car_id][self.direction][t] = self.distance_from_garage

        
    def save_state(self, t, csv_writer):
        '''
        write attributes to csv file for visualization
        
        '''
        pos_convert = transform(Train.inv_project, self.position).coords[:]
        csv_writer.writerow((t, self.car_id, pos_convert, self.get_load(level='O'), self._load_history['O'], 
                            self.next_station_id))
        self._saved_states[t] = [self.car_id, self.position, self.get_load(level='O'), self._load_history['O'], 
                            self.next_station_id]
        
            
    def update_next_platform_info(self, central_monitor_instance):
        ''' to be called in the next timestep after UPDATE with RW '''
        _next_station_instance = central_monitor_instance.return_station_by_id(self.next_station_id)
        _next_platform_instance = _next_station_instance.platforms[self.direction]
        self.next_platform = _next_platform_instance
        
        if self.next_NEXT_station_id != None:
            _next_next_station_instance = central_monitor_instance.return_station_by_id(self.next_NEXT_station_id)
            _next_next_platform_instance = _next_next_station_instance.platforms[self.direction]
            self.next_next_platform = _next_next_platform_instance
        
        
    def update(self, central_monitor_instance, t, god, t_start):
        

#==============================================================================
#         # DEBUGGING
#         if self.distance_to_train_in_back is None:
#                 self._dist_to_back.append(0)
#         else :
#             self._dist_to_back.append(self.distance_to_train_in_back)
#==============================================================================
            
                
        if self.is_in_service:
            
           
            
            self._dist_to_front.append(self._get_distance_to_front_train())
            
            #only record states for the first 15 minutes of each run. 
#            if t  <= t_start + 30 *60: 
            self._record_state_for_plotting(t, central_monitor_instance)
            
#             print "distance_to_next_station: ", self.distance_to_next_station, " at time: ", t
            if self.it_has_reached_a_station:
#==============================================================================
#             if self.has_it_reached_a_station(self.Param.consecutive_speeds[self.prev_station_id][self.next_station_id]):
#==============================================================================
#                 print "reached station ", self.car_id, "at time ", t
#                 self.log_file.write("train "+ (self.car_id) + " reached station "+ "at time "+ str(t)+'\n')
                if not self.waiting: # if this is the first moment it has reached the staiton
                    station = central_monitor_instance.return_station_by_id(self.next_station_id).platforms[self.direction]
                    if self.should_it_enter_the_station(station): # TODO: get this station first
#                         self.log_file.write("train "+ (self.car_id) + " entered station "+ "at time "+ str(t)+'\n')
#                        print "enter station, time: ", str(t)
                        self.arrive_at_station(t, central_monitor_instance)
                        number_of_alights = self.unload_passengers(central_monitor_instance, t, god)
                        number_of_boardings = self.board_passengers(central_monitor_instance, t)
                        self.start_waiting(central_monitor_instance, number_of_boardings, number_of_alights )
                    else:
                        # wait for other train to leave the station
#                         print "wait for other train to leave the station, time: ", str(t)
#                         self.log_file.write("train "+ (self.car_id) +  " wait for other train to leave the station, time: "
#                                        +str(t)+'\n')
#                        self.start_waiting()
                        pass
                # it has been waiting here        
                else:
                    if self.should_it_keep_waiting():
#                         print "still waiting, time: ", str(t)
#                         self.log_file.write("train "+ (self.car_id) +  " still waiting, time: "+ str(t)+'\n')
                        self.keep_waiting()
                    else:
                        
#                         print "left station ", station.ids, " ", self.car_id  
#                         self.log_file.write("train "+ (self.car_id) +  " left station "+ str(station.ids) + " at time "+str(t)+'\n')
                        self.depart_station(central_monitor_instance, t)
#                         print "position: ", self.position

            else:
                # if it has not reached a station yet
                
#==============================================================================
#==============================================================================
#                  print "t ", t
#                  print "moving car id", self.car_id
#                  print "time to next ", self.time_to_next_station
#                  print "dist to next ", self.distance_to_next_station
#                  print "current station id ", self.current_station_id
#                  print "next station id ", self.next_station_id
#==============================================================================
#==============================================================================
                 self.move(t)
#==============================================================================
#                 print "t ", t
#                 print "moving ", self.car_id
#                 print "time to next ", self.time_to_next_station
#                 print "dist to next ", self.distance_to_next_station
#                 print "current station id ", self.current_station_id
#                 print "next station id ", self.next_station_id                
#==============================================================================
                 assert(self.time_to_next_station >= 0)
                    
                    


        else:
            pass
#            central_monitor_instance.train_trajectories[self.car_id].append(self.distance_from_garage)
       
           
        
        