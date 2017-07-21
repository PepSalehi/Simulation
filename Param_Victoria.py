# -*- coding: utf-8 -*-
"""
Created on Mon Jul 10 17:06:41 2017

@author: Peyman
"""

from config import * 

class Param_Victoria(object):
    
    '''store all the parameters inside this class
        TODO: currently all travel times are fixed. They should be changed to be stochastic.
        TODO: assign a numeric value to each station; makes it easier to get next/previous stations
    '''
    
    # 18 hours
    SIMULATION_TIME = 18 * 60 * 60
    HEADWAY = 1 * 60 #3 minutes
    headways_dic = pd.read_pickle("C:\\Users\\Peyman.n\\Dropbox\\Research\\projects\\Crowding\\headways.p")
    route_nlcs = pickle.load(
        open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/victoria_route_nlcs.p", "rb"))



    stations = [(i) for i in route_nlcs]
    
    PRIMARY_DIRECTION = "SN"
   
    

    station_travel_times = pickle.load(
        open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/victoria_line_station_travel_times.p", "rb"))

    consecutive_speeds = pickle.load(
         open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/victoria_consecutive_speeds.p", "rb"))

    station_distances = pickle.load(
        open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/victoria_station_distances.p", "rb"))




    # assign station positions
    station_positions = pickle.load(
        open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/victoria_station_loopkup_geom_by_nlc.p", "rb"))

    line = pickle.load(
        open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/victoria_line.p" , "rb"))

    station_lookup_by_nlc = pickle.load(
        open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/victoria_station_lookup_by_nlc.p"))

    
    @classmethod 
    def should_dispatch(cls):
        '''
        it should be called, by its children, on e every time step to see a train must be dispatched 
        '''
        # time to change
        if cls.timer == 0 :
            hd = cls.headways.popleft()
            cls.timer = hd
            return(True)
        else:
            cls.timer -= 1 
            return(False)

class Param_Victoria_SN(Param_Victoria):
    suffix = " SN"
    garage_name = "garageS"
    last_garage_name = "garageN"
    direction = "SN"
    
    route_nlcs = Param_Victoria.route_nlcs    
    stations = [(i) for i in route_nlcs]
    
    # headways
    headways = np.array(Param_Victoria.headways_dic['Brixton-Stockwell']) * 1.5
    headways = headways.astype(int)
    headways = deque(headways)
    timer = 0 
    extra_headways_fro_empty_trains = list(np.repeat(300, 12 ))
    headways.extendleft(extra_headways_fro_empty_trains)
    
    # changing these attributes will change the original ones in Param_Victoria as well
    station_travel_times = Param_Victoria.station_travel_times
    consecutive_speeds = Param_Victoria.consecutive_speeds
    station_distances = Param_Victoria.station_distances
       
    
    station_distances[garage_name][route_nlcs[0]] = 1
    station_travel_times[garage_name][route_nlcs[0]]= 1
    consecutive_speeds[garage_name][route_nlcs[0]] = 9
    station_travel_times[route_nlcs[len(route_nlcs) - 1]][last_garage_name]= 1
    consecutive_speeds[route_nlcs[len(route_nlcs) - 1]][last_garage_name] = 9
    
    

    # create sufficient trains
    max_tt = max(station_travel_times[Param_Victoria.route_nlcs[0]].values())
    num_req_trains = int(np.ceil(max_tt / Param_Victoria.HEADWAY)) + 10 # safety measure
    train_ids = [str(alp) + str(random.randint(0,1000))  for alp in xrange(1,num_req_trains+1)]
    terminal_station = stations[len(stations)-1]
    
    
    @classmethod
    def get_stations_after_this(cls,station_id):
        current_index = cls.stations.index(station_id)
        return cls.stations[current_index:]
        
    
    

class Param_Victoria_NS(Param_Victoria):
    suffix = " NS"
    garage_name = "garageN" 
    last_garage_name = "garageS"
    direction = "NS"
    
    
    route_nlcs = Param_Victoria.route_nlcs[::-1]
    stations = ([(i) for i in route_nlcs])

    # headways
    extra_headways_fro_empty_trains = list(np.repeat(300, 12 ))
    headways = np.array(Param_Victoria.headways_dic['Walthamstow Central-Blackhorse Road'] ) * 1.5
    headways = headways.astype(int)
    headways = deque(headways)
    headways.extendleft(extra_headways_fro_empty_trains)
    timer = 0 

    consecutive_speeds = {k2:{k : v2} for k, v in Param_Victoria.consecutive_speeds.iteritems() for k2, v2 in v.iteritems()}

    station_distances  = defaultdict(dict)
    for k, v in Param_Victoria.station_distances.iteritems():
        for k2, v2 in v.iteritems():
            station_distances[k2][k] = v2

    station_travel_times  = defaultdict(dict)
    for k, v in Param_Victoria.station_travel_times.iteritems():
        for k2, v2 in v.iteritems():
            station_travel_times[k2][k] = v2

    station_distances[garage_name][route_nlcs[0]] = 1
    station_travel_times[garage_name][route_nlcs[0]]= 1
    consecutive_speeds[garage_name][route_nlcs[0]] = 9
    station_travel_times[route_nlcs[len(route_nlcs) - 1]][last_garage_name]= 1
    consecutive_speeds[route_nlcs[len(route_nlcs) - 1]][last_garage_name] = 9
    

    # create sufficient trains
    max_tt = max(station_travel_times[route_nlcs[0]].values())
    num_req_trains = int(np.ceil(max_tt / Param_Victoria.HEADWAY)) + 10 # safety measure
    train_ids = [str(alp) + str(random.randint(0,1000))  for alp in xrange(1,num_req_trains+1)]
    terminal_station = stations[len(stations)-1]
    
    line = pickle.load(
        open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/victoria_line_shifted.p" , "rb"))
    @classmethod
    def get_stations_after_this(cls,station_id):
        current_index = cls.stations.index(station_id)
        return cls.stations[current_index:]