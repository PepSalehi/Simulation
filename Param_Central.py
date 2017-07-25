# -*- coding: utf-8 -*-
"""
Created on Mon Jul 10 14:59:12 2017

@author: Peyman
"""

from config import *
class Param_Central(object):
    
    '''store all the parameters inside this class
        TODO: currently all travel times are fixed. They should be changed to be stochastic.
        TODO: assign a numeric value to each station; makes it easier to get next/previous stations
    '''
    
    # 18 hours
    SIMULATION_TIME = 18 * 60 * 60
    HEADWAY = 2 * 60 #3 minutes
    headways_dic = pd.read_pickle("C:\\Users\\Peyman.n\\Dropbox\\Research\\projects\\Crowding\\headways.p")

    route_nlcs = pickle.load(
        open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/route_nlcs.p", "rb"))



    stations = [(i) for i in route_nlcs]
    
    PRIMARY_DIRECTION = "WE"
   
    

    station_travel_times = pickle.load(
        open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/central_line_station_travel_times.p", "rb"))

    consecutive_speeds = pickle.load(
         open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/consecutive_speeds.p", "rb"))

    station_distances = pickle.load(
        open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/station_distances.p", "rb"))




    # assign station positions
    station_positions = pickle.load(
        open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/station_loopkup_geom_by_nlc.p", "rb"))

    line = pickle.load(
#      open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/central_line.p", "rb"))
        open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/central_line.p" , "rb"))

    central_station_lookup_by_nlc = pickle.load(
        open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/central_station_lookup_by_nlc.p"))

#==============================================================================
#     @classmethod    
#     def should_dispatch(cls):
#         '''
#         it should be called, by its children, on e every time step to see a train must be dispatched 
#         '''
#         # time to change
#         if cls.timer == 0 :
#             hd = cls.headways.popleft()
#             cls.timer = hd
#             return(True)
#         else:
#             cls.timer -= 1 
#             return(False)
#==============================================================================
     
    def should_dispatch(self):
        '''
        it should be called, by its children, on e every time step to see a train must be dispatched 
        '''
        # time to change
        if self.timer == 0 :
            hd = self.headways.popleft()
            self.timer = hd
            return(True)
        else:
            self.timer -= 1 
            return(False)      
            
class Param_Central_WE(Param_Central):
    suffix = " WE"
    garage_name = "garageW"
    last_garage_name = "garageE"
    direction = "WE"
    
    route_nlcs = Param_Central.route_nlcs    
    stations = [(i) for i in route_nlcs]
    
    def __init__(self):
        # headways
        headways = np.array(Param_Central.headways_dic['Ealing Broadway-West Acton']) * 0.5
        headways = headways.astype(int)
        self.headways = deque(headways)
        self.timer = 0   
        extra_headways_fro_empty_trains = list(np.repeat(300, 12 ))
        self.headways.extendleft(extra_headways_fro_empty_trains)
    
    # changing these attributes will change the original ones in Param_Central as well
    station_travel_times = Param_Central.station_travel_times
    consecutive_speeds = Param_Central.consecutive_speeds
    station_distances = Param_Central.station_distances
       
    
    station_distances[garage_name][route_nlcs[0]] = 1
    station_travel_times[garage_name][route_nlcs[0]]= 1
    consecutive_speeds[garage_name][route_nlcs[0]] = 9
    station_travel_times[route_nlcs[len(route_nlcs) - 1]][last_garage_name]= 1
    consecutive_speeds[route_nlcs[len(route_nlcs) - 1]][last_garage_name] = 9

    # create sufficient trains
    max_tt = max(station_travel_times[Param_Central.route_nlcs[0]].values())
    num_req_trains = int(np.ceil(max_tt / Param_Central.HEADWAY)) + 10 # safety measure
    train_ids = [str(alp) + str(random.randint(0,1000))  for alp in xrange(1,num_req_trains+1)]
    terminal_station = stations[len(stations)-1]
    
#     http://stackoverflow.com/questions/18431313/how-can-static-method-access-class-variable-in-python
    @classmethod
    def get_stations_after_this(cls,station_id):
        current_index = cls.stations.index(station_id)
        return cls.stations[current_index:]
    

class Param_Central_EW(Param_Central):
    suffix = " EW"
    garage_name = "garageE" 
    last_garage_name = "garageW"
    direction = "EW"
    
    
    route_nlcs = Param_Central.route_nlcs[::-1]
    stations = ([(i) for i in route_nlcs])
    
    def __init__(self):
        # headways
        self.timer = 0  
        headways = np.array(Param_Central.headways_dic['Epping-Theydon Bois'])* 0.7
        headways = headways.astype(int)
        self.headways = deque(headways)
        extra_headways_for_empty_trains = list(np.repeat(300, 12 ))
        self.headways.extendleft(extra_headways_for_empty_trains)
     

    consecutive_speeds = {k2:{k : v2} for k, v in Param_Central.consecutive_speeds.iteritems() for k2, v2 in v.iteritems()}

    station_distances  = defaultdict(dict)
    for k, v in Param_Central.station_distances.iteritems():
        for k2, v2 in v.iteritems():
            station_distances[k2][k] = v2

    station_travel_times  = defaultdict(dict)
    for k, v in Param_Central.station_travel_times.iteritems():
        for k2, v2 in v.iteritems():
            station_travel_times[k2][k] = v2

    station_distances[garage_name][route_nlcs[0]] = 1
    station_travel_times[garage_name][route_nlcs[0]]= 1
    consecutive_speeds[garage_name][route_nlcs[0]] = 9
    station_travel_times[route_nlcs[len(route_nlcs) - 1]][last_garage_name]= 1
    consecutive_speeds[route_nlcs[len(route_nlcs) - 1]][last_garage_name] = 9
    

    # create sufficient trains
    max_tt = max(station_travel_times[route_nlcs[0]].values())
    num_req_trains = int(np.ceil(max_tt / Param_Central.HEADWAY)) + 10 # safety measure
    train_ids = [str(alp) + str(random.randint(0,1000))  for alp in xrange(1,num_req_trains+1)]
    terminal_station = stations[len(stations)-1]
    
    line = pickle.load(
     open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/central_line_shifted.p", "rb"))
    
    @classmethod
    def get_stations_after_this(cls,station_id):
        current_index = cls.stations.index(station_id)
        return cls.stations[current_index:]


