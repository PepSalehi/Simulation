# -*- coding: utf-8 -*-
"""
Created on Mon Jul 10 15:02:40 2017

@author: Peyman
"""
from config import * 
class Passenger(object):
    
    def __init__(self, entry_station, exit_stations, entry_time, act_dumb):
        
        self.entry_station = entry_station
        self.exit_stations = deque(list(exit_stations))
        
        if len(self.exit_stations) > 1 :
            self.DOES_TRANSFER = True
        else:
            self.DOES_TRANSFER = False
            
        self._exit_stations = exit_stations
        self.next_destination = self.exit_stations.popleft()
        self.entry_time = entry_time 
        self.boarding_time = 0
        self.exit_time = 0
        self._entry_stations = []; self._entry_stations.append(self.entry_station)
        self._entry_times = [] ; self._entry_times.append(self.entry_time)
        self._exit_times = []
        self.trips = defaultdict(lambda : defaultdict(list))
        self.number_of_denied_boardings = defaultdict(int)
        # for when they refuse to board because of their convivnience level
        self.number_of_denied_boardings_out_of_choice = defaultdict(int)
        
        self.act_dumb = act_dumb        
        
    def get_travel_time(self):
        return self.exit_time - self.boarding_time
    def get_waiting_time(self):
        return self.boarding_time - self.entry_time
    def update(self, exit_time):
        self.exit_time = exit_time
        self.trips[self.entry_station][self.next_destination] = [self.get_travel_time(), self.get_waiting_time()] # make this named tuple
        self._exit_times.append(exit_time)
        
        if len(self.exit_stations) != 0:
            self.next_destination = self.exit_stations.popleft()
        else:
            self.next_destination = None
            
    def trip_infos(self):
        waiting_times = []
        travel_times = []
        for origin, rest in self.trips.iteritems():
            for dest, _ in rest.iteritems():
                waiting_times.append(_[1])
                travel_times.append(_[0])
        return {"waiting_times": waiting_times, "travel_times":travel_times}
    
    def reassign_info(self, entry_station, entry_time):
        self._entry_stations.append(self.entry_station)
        self._entry_times.append(self.entry_time)
        self.entry_time = entry_time
        self.boarding_time = None
        self.exit_time = None
    
    def should_it_try_to_board(self, upcoming_trains_info, the_one_arrived_at_now_info):
        if self.act_dumb : 
            return True
        else :
            if the_one_arrived_at_now_info['boarding_prob_color']== 'green':
                return True
            # if he actually has an option
        
            if len(upcoming_trains_info) >= 1:
                # sort by the arrival times                 
                sorted_x = sorted(upcoming_trains_info.items(), key=lambda item : item[1][0] )
                # board if the earliest train is green
                earliest = sorted_x[0]
                
#                print "sorted_x", sorted_x
#                print "earlies", earliest
#                earlies ('8332', [1, {'car_id': '8332', 'boarding_prob_color': 'green', 'prob_of_boarding': 1}])
                
#                if the_one_arrived_at_now_info['boarding_prob_color'] != 'green': 
#                    print "TRAIN NOT GREEN "
#                    print earliest[1][1]
                    
                
                if (the_one_arrived_at_now_info['boarding_prob_color'] != 'green'): # and earliest[1][1]['boarding_prob_color'] == 'green':
                    # draw a random number, and board if p > threshold(.2)
                    if  np.random.random_sample() > 0.2:
                        return False
                
                return True
            else:
                return True 
    
        
        