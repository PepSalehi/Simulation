# -*- coding: utf-8 -*-
"""
Created on Mon Jul 10 15:02:10 2017

@author: Peyman
"""
from config import *
from Param_Central import Param_Central, Param_Central_WE, Param_Central_EW
from Param_Victoria import Param_Victoria, Param_Victoria_NS, Param_Victoria_SN

class Train(object):
    # https://tfl.gov.uk/corporate/about-tfl/what-we-do/london-underground/rolling-stock
    CAPACITY = 892 
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
        ## 
        self.stations_visited = {}
        self._saved_states = {}
#         self.log_file = open((self.car_id)  + ' workfile.txt', 'w') # + str(random.randint(0,100000))
        
    
    def load_passenger(self, central_monitor_instance,  t, station):
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
#                     print "DENIED BOARDING for train "+ self.car_id + " at level " + level
                    denied = True
                    
                while len(self.passengers[level]) < self.CAPACITY and len(station.queue[level]) > 0:
                    pax = station.queue[level].pop()
                    pax.boarding_time = t
                    pax.boarding_train_direction = self.direction
                    self.passengers[level].append(pax)
                    i += 1
                    self.just_boarded.append(pax)

                    central_monitor_instance.all_passengers_boarded.append(pax)
                if denied :
                    j=0
                    for pax in station.queue[level]:
                        pax.number_of_denied_boardings[level] += 1
                        central_monitor_instance.passenger_denied_boarding[level].append([pax, t, station])
                        j+=1
#                     print str(j)+ " people couldn't board the train at level " + level
            else:
                denied = True
                for pax in station.queue[level]:
                        pax.number_of_denied_boardings[level] += 1
                        central_monitor_instance.passenger_denied_boarding[level].append([pax, t, station])
#                 print "train is full"
#                 print str(len(station.queue[level]))+ " people couldn't board the train"
            
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
    
    def offload_passengers(self, central_monitor_instance, station_id, offload_time, god):
        # reset the list
        self.just_offloaded = []
        #
        for level in ["H", "O", "P"]:
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
                        
                    # how to keep track of this 
                    central_monitor_instance.all_passengers_offloaded[level].append(pax)
                    i += 1
                    self.just_offloaded.append(pax)

#             print "offloaded ", str(i), "passengers", " ", level
#             print "after", len(self.passengers[level]), " ", level
        
    def empty_load(self, central_monitor_instance, t):
        # for the last stop, so that it starts fresh at the beginnig of the line again
        # should set pax exit time and station
        for level in ["H", "O", "P"]:
            for pax in self.passengers[level]:
                pax.exit_time = t
                pax.exit_station = self.Param.stations[len(self.Param.stations)-1]

                central_monitor_instance.all_passengers_offloaded[level].append(pax)

                central_monitor_instance.all_passengers_emptied_at_last[level].append(pax)

            self.passengers = defaultdict(list)
        
    def get_next_station_id(self):
        if self.current_station_id != self.Param.terminal_station:
            # if this is not the last stop
            current_index = self.Param.stations.index(self.current_station_id)
            next_station_id = self.Param.stations[current_index + 1]
            return next_station_id 
        else:
            # terminal station
            return 'garage'
        

            
    def get_travel_time_to_next_station(self):
        # make it stochastic
        base = self.Param.station_travel_times[self.current_station_id][self.next_station_id]
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
        
    def should_it_keep_waiting(self, waiting_time = 90):
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
    
    def start_over(self, central_monitor_instance, t, garage):
        # after offloading pax at the last stop
        self.empty_load(central_monitor_instance, t)
        # go to the last garage
        self.position = self.Param.station_positions[self.Param.last_garage_name] # CHANGE
        garage.add_to_garage(self)
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
                print " moved passed the end of line, should've catched it before calling this function! "
                
        elif self.direction != self.Param.PRIMARY_DIRECTION:
            dist_from_end_node = line.project(pt)
            if line.length > distance:
                end_point = line.interpolate(dist_from_end_node - distance)
                return (end_point)
            else:
                print " moved passed the end of line, should've catched it before calling this function! "

    
    
    
    def move(self, distance=None):
        if distance == None: distance = Train.SPEED
        
        # check whether or not it has reached the station, or will reach and pass it if it moves, before calling this function
#         print self.position
        self.position = self._move_train_one_dist(pt = self.position, distance=distance)
        self.distance_to_next_station -= distance
        self.time_to_next_station -= self.distance_to_next_station / distance 
            
        
            
    def has_it_reached_a_station(self, distance=None):
        if distance == None: distance = self.SPEED
        # arriving and passing the station
        if self.distance_to_next_station <= self.SPEED:
#         or (self.distance_to_next_station <= self._move_train_one_dist(self.position, distance = self.distance_to_next_station)):
            return True
        return False
        
            
    def arrive_at_station(self, t, central_monitor_instance, line_all = None):
        if line_all is None:
            line_all = self.Param.line
        # set current station id
        self.current_station_id = self.next_station_id #  it has arrived at the next station
        station = central_monitor_instance.return_station_by_id(self.current_station_id)
#         self.position  = station.position
        self.position = line_all.interpolate(line_all.project(self.position) + self.distance_to_next_station)
#         self.position = self.Param.station_positions[self.current_station_id]
        # update the status that has reached a station, and will be there for a few seconds
#         self.has_arrived_at_station = True
        self.stations_visited[t] = (self.current_station_id)
        
        
        
    def unload_passengers(self, central_monitor_instance, t, god):
        self.offload_passengers(central_monitor_instance, self.current_station_id, t, god)
    
    def board_passengers(self,central_monitor_instance,  t):
        # remember to first call unload passengers
        
        current_station = central_monitor_instance.return_station_by_id(self.current_station_id).platforms[self.direction]

        # check if this is the last station. 
        if self.current_station_id != self.Param.terminal_station:

            current_station.hist_queue["dh"].append(len(current_station.queue['H']))
            current_station.hist_queue["dp"].append(len(current_station.queue['P']))
            current_station.hist_queue["do"].append(len(current_station.queue['O']))
            current_station.hist_queue["t"].append(t)
            
            # board pax
            self.load_passenger(central_monitor_instance, t, current_station)

        else:
            # if it is the last station
#             self.start_over(t=t)
            pass
    
    def depart_station(self, central_monitor_instance, t):
        self.waiting = False
        
        central_monitor_instance.train_trajectories[self.car_id].append(self.position)
        for level in ["H", "O", "P"]:
            self._load_history[level].append(self.get_load(level))
            
        if self.current_station_id == self.Param.terminal_station:
            # if it is the last station
            self.start_over(central_monitor_instance,  garage= central_monitor_instance.return_garage_of_opposite_direction(self.direction), t=t)
        else:
            # get the next station id
            self.next_station_id = self.get_next_station_id()
            # get distance to next station
            self.distance_to_next_station = self.Param.station_distances[self.current_station_id][self.next_station_id]
            # get time to next station
            self.time_to_next_station = self.get_travel_time_to_next_station()
            
            self.prev_station_id = self.current_station_id
            
            
            
        
    def save_state(self, t, csv_writer):
        '''
        write attributes to csv file for visualization
        
        '''
        pos_convert = transform(Train.inv_project, self.position).coords[:]
        csv_writer.writerow((t, self.car_id, pos_convert, self.get_load(level='O'), self._load_history['O'], 
                            self.next_station_id))
        self._saved_states[t] = [self.car_id, self.position, self.get_load(level='O'), self._load_history['O'], 
                            self.next_station_id]
        
            
        
    def update(self, central_monitor_instance, t, god):
        # if it has been dispatched (i.e. is not in the garage)
        if self.is_in_service:
#             print "distance_to_next_station: ", self.distance_to_next_station, " at time: ", t
            if self.has_it_reached_a_station(self.Param.consecutive_speeds[self.prev_station_id][self.next_station_id]):
#                 print "reached station ", self.car_id, "at time ", t
#                 self.log_file.write("train "+ (self.car_id) + " reached station "+ "at time "+ str(t)+'\n')
                if not self.waiting: # if this is the first moment it has reached the staiton
                    station = central_monitor_instance.return_station_by_id(self.next_station_id).platforms[self.direction]
                    if self.should_it_enter_the_station(station): # TODO: get this station first
#                         self.log_file.write("train "+ (self.car_id) + " entered station "+ "at time "+ str(t)+'\n')
#                         print "enter station, time: ", str(t)
                        self.arrive_at_station(t, central_monitor_instance)
                        self.unload_passengers(central_monitor_instance, t, god)
                        self.board_passengers(central_monitor_instance, t)
                        self.start_waiting()
                    else:
                        # wait for other train to leave the station
#                         print "wait for other train to leave the station, time: ", str(t)
#                         self.log_file.write("train "+ (self.car_id) +  " wait for other train to leave the station, time: "
#                                        +str(t)+'\n')
                        self.start_waiting()
                # it has been waiting here        
                else:
                    if self.should_it_keep_waiting():
#                         print "still waiting, time: ", str(t)
#                         self.log_file.write("train "+ (self.car_id) +  " still waiting, time: "+ str(t)+'\n')

                        self.keep_waiting()
                    else:
                        station = central_monitor_instance.return_station_by_id(self.next_station_id)
#                         print "left station ", station.ids, " ", self.car_id  
#                         self.log_file.write("train "+ (self.car_id) +  " left station "+ str(station.ids) + " at time "+str(t)+'\n')
                        self.depart_station(central_monitor_instance, t)
#                         print "position: ", self.position

            else:
                # if it has not reached a station yet
#                 print "moving ", self.car_id
                self.move(self.Param.consecutive_speeds[self.prev_station_id][self.next_station_id])


        else:
            central_monitor_instance.train_trajectories[self.car_id].append(self.position)
       
           
        
        