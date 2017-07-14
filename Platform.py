# -*- coding: utf-8 -*-
"""
Created on Mon Jul 10 15:01:12 2017

@author: Peyman
"""
from config import * 
from Passenger import Passenger 
class Platform(object):
    def __init__(self, direction, station_id, line, param):
        self.demand = 0
        self.ids = station_id 
        self.direction = direction
        self.line = line
        self.param = param
        self.queue = defaultdict(deque)
        self.historical_queue = deque()
        self.observed_queue = deque()
        self.predicted_queue = deque()
        # secondary queue for pax who decide to not board the train
        self.secondary_queue = deque()
        # a way to enforce trains don't move head to end
        self.is_occupied = False
        self.time_since_occupied = 100000
        # bookkeeping
        self._load_histoty = 0
        # pax created
        self.pax_list = defaultdict(list)
        self.demand_rate = defaultdict(float)
        # 
        self.arriving_trains_loads = defaultdict(list)
        # Queue length at the time of train arrival
        self.hist_queue = defaultdict(list)
        # for visualiztion; we want every station to start with zero passengers
        self.hist_queue["do"].append(0)
        
        # keep track of approaching trains and their distance (or time)
        # {train_id : time_to_get}
        self.upcoming_trains = defaultdict(int)        
        
        
    def get_transfer_time(self, line1):
        ''' 
        interesting that I had coded this :)
        '''
        
        if self.line == line1:
            return 0 # no transfer time
        if line1 == "Central":
            return random.randint(15,60)
        if line1 == "Victoria":
            return random.randint(15,60)
                
    
    def _populate_demand(self, central_monitor_instance, demand_dict, t_offset, section, time_range = 15*60 ): 

        for destinations, demand_time in demand_dict[self.ids][self.direction].iteritems():
            # demand during time_period t_offset
            demand = demand_time[t_offset]
            # create passengers
            for _ in range(1, demand+1):
                # arrival time is now uniformly distributed during the 15 minutes interval 
                pax = Passenger(entry_station = self.ids, exit_stations = destinations, entry_time = int(random.uniform(t_offset, t_offset + time_range)))
                if section == "H":
                    central_monitor_instance.all_passengers_created_historical.append(pax) 
                    self.pax_list["H"].append(pax)
                elif section == "O":
                    central_monitor_instance.all_passengers_created_observed.append(pax)
                    self.pax_list["O"].append(pax)
                elif section == "P":
                    central_monitor_instance.all_passengers_created_predicted.append(pax) 
                    self.pax_list["P"].append(pax)
                
    def produce_passsengers(self, central_monitor_instance, t_offset, time_range = 15*60):
        # there should be no unproduced passengers from last interval
#         assert len(self.pax_list) == 0
#         self.pax_list = defaultdict(list)

        
        self._populate_demand(central_monitor_instance, central_monitor_instance.station_demands_observed, t_offset, "O" )
        self._populate_demand(central_monitor_instance, central_monitor_instance.station_demands_historical, t_offset, "H" )
        self._populate_demand(central_monitor_instance, central_monitor_instance.station_demands_predicted, t_offset, "P" )

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
                
                # for bookkeeping
                if k == "O":
                    self.observed_queue.append(pax)
                elif k == "H":
                    self.historical_queue.append(pax)
                elif k =="P":
                    self.predicted_queue.append(pax)
    
    
    def produce_passengers_per_t(self, t):
        
        all_matched_dict = self._return_matched_pax([t])
        
        for k, matches in all_matched_dict.iteritems():
            self._append_to_queue(k, matches)
        
                
    def get_waiting_passengers(self, k):
        return self.queue[k]
    def reset_time_since_boarding(self):
        self.time_since_occupied = 0
        
    def get_stations_after_this(self, station_id):
        current_index = self.param.stations.index(station_id)
        return self.param.stations[current_index:]
    
    def save_state(self, t, csv_writer):
        '''
        write attributes to csv file for visualization
        
        '''
        csv_writer.writerow((t, self.ids, self.direction ,len(self.queue["O"]), self.hist_queue["do"]))
        
        
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