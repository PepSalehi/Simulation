# -*- coding: utf-8 -*-
"""
Created on Mon Jul 10 15:02:39 2017

@author: Peyman
"""
from config import * 
from Param_Central import Param_Central, Param_Central_WE, Param_Central_EW
from Param_Victoria import Param_Victoria, Param_Victoria_NS, Param_Victoria_SN
from Train import Train 
from Station import Station
from Garage import Garage 

class CentralMonitor(object):
    
    def __init__(self, line):
        
        ''' A repo'''
        self.line = line

        self.all_passengers_created_predicted = []
        self.all_passengers_created_observed = [] 
        self.all_passengers_created_historical = []

        self.all_passengers_offloaded = defaultdict(list)
        self.passenger_denied_boarding = defaultdict(list)
        # 
        self.passenger_denied_boarding_out_of_choice = defaultdict(list)
        
        self.all_passengers_boarded = []
        self.all_passengers_emptied_at_last = defaultdict(list)

        if self.line == "Central":
            self.directions = ["WE","EW"]
            self.params = [Param_Central_WE, Param_Central_EW]
            self.main_param = Param_Central
        elif self.line == "Victoria":
            self.directions = ["SN", "NS"]
            self.params = [Param_Victoria_SN, Param_Victoria_NS]
            self.main_param = Param_Victoria
            
               
        # create trains
        
        primary_param = self.params[0]
        self.trains_primary = [Train(car_id=car_id, next_station_id=primary_param.stations[0], 
                        prev_station_id=primary_param.garage_name, 
                        time_to_next_station= primary_param.station_travel_times[primary_param.garage_name][primary_param.route_nlcs[0]],
                        distance_to_next_station = primary_param.station_distances[primary_param.garage_name][primary_param.route_nlcs[0]],
                        position = primary_param.station_positions[primary_param.garage_name],
                        direction = self.directions[0],
                        line = self.line) 
                        for car_id in primary_param.train_ids]

        secondary_param = self.params[1]
        self.trains_secondary = [Train(car_id=car_id, next_station_id=secondary_param.stations[0], 
                        prev_station_id=secondary_param.garage_name, 
                        time_to_next_station= secondary_param.station_travel_times[secondary_param.garage_name][secondary_param.route_nlcs[0]],
                        distance_to_next_station = secondary_param.station_distances[secondary_param.garage_name][secondary_param.route_nlcs[0]],
                        position = secondary_param.station_positions[secondary_param.garage_name],
                        direction = self.directions[1],
                        line = self.line) 
                        for car_id in secondary_param.train_ids]

                
        
        self._trains = {}
        self._trains[self.directions[0]] = self.trains_primary
        self._trains[self.directions[1]] = self.trains_secondary
        
        # this is problematic
#         self.trains = deepcopy(self.trains_WE); self.trains.extend(self.trains_EW)

#         # create stations
        self.stations = [Station(ids, self.line) for ids in self.main_param.stations]
        for station in self.stations[:]:
            station.position = self.main_param.station_positions[station.ids]
        
        self.garages = {}

        for idx, name in enumerate(self.directions):
           
            self.garages[name] = (Garage(self._trains[name], position = self.main_param.station_positions[self.params[idx].garage_name],
                                      param = self.params[idx], garage_name = self.params[idx].garage_name))
              
            
        
        
        if self.line == "Central":
            self.data_path =  "C:/Users/Peyman.n/Dropbox/Research\\projects\\Short_term_forcast\\R code\\data\\"
            self.other_lines = ["Victoria"]
            self.other_data_paths = ["C:/Users/Peyman.n/Dropbox/Research\\projects\\Short_term_forcast\\R code\\data\\victoria\\"]
            self.transfer_stations = [[669]]
#             self.other_params = [Param_Victoria]
            
        elif self.line == "Victoria":
            self.data_path =  "C:/Users/Peyman.n/Dropbox/Research\\projects\\Short_term_forcast\\R code\\data\\victoria\\"
            self.other_lines = ["Central"]
            self.other_data_paths = ["C:/Users/Peyman.n/Dropbox/Research\\projects\\Short_term_forcast\\R code\\data\\"]
            self.transfer_stations = [[669]]
#             self.other_params = [Param_Central]
            
        self.onlyfiles = [f for f in listdir(self.data_path) if isfile(join(self.data_path, f))]
        
        # [origin_id][platform_id][dest_id][time] = demand
        self.station_demands_observed = defaultdict(lambda : defaultdict(lambda : defaultdict(dict)))
        self.station_demands_historical = defaultdict(lambda : defaultdict(lambda : defaultdict(dict)))
        self.station_demands_predicted = defaultdict(lambda : defaultdict(lambda : defaultdict(dict)))
        

        # WE 
        # platform = "WE"
        # param = Param_Central_WE
        for platform, param in zip(self.directions, self.params):
            for idx, station_id in enumerate(param.stations[0:len(param.stations)-1]):
                origin_id =  station_id
                for dest_id in param.stations[(idx+1):len(param.stations)]:
                    dest_id = dest_id
                    demand = self.read_od_from_file(origin_id, dest_id)
                    for ind, t in enumerate(range(0, self.main_param.SIMULATION_TIME, 15*60)):
                        self.station_demands_observed[origin_id][platform][tuple([dest_id])][t] = demand.observed[ind]
                        self.station_demands_predicted[origin_id][platform][tuple([dest_id])][t] = demand.predicted[ind] #demand.observed[ind] + sugg 
                        self.station_demands_historical[origin_id][platform][tuple([dest_id])][t] = demand.historical[ind]
                        
            # Transfers 
                origin_id =  station_id
                
                max_station_index = param.stations.index(self.transfer_stations[0][0]) # get stations up to and including transfer stations
                current_index = param.stations.index(origin_id)
                if current_index < max_station_index: # it's vital for it to not be equal to transfer station 
                    
                    for idx, other_line in enumerate(self.other_lines):
                        other_params = self.return_params_and_stuff(other_line)['params']

                        # NS, SN
                        for other_param in other_params:

                            for dest_id in other_param.stations:
                                if origin_id != dest_id: # no oxford to oxford, for example
                                    demand = self.read_od_from_file(origin_id, dest_id )
                                    # get transfer stations
                                    transfer_stations = self.transfer_stations[idx][:]
                                    # if oxford, the transfer station, is it self the final destination
                                    if transfer_stations[0] == dest_id or transfer_stations[0] == origin_id :
                                        transfer_stations = [dest_id]
                                    else:
                                        transfer_stations.append(dest_id)
                                    for ind, t in enumerate(range(0, self.main_param.SIMULATION_TIME, 15*60)):
                                        self.station_demands_observed[origin_id][platform][tuple(transfer_stations)][t] = demand.observed[ind]
                                        self.station_demands_predicted[origin_id][platform][tuple(transfer_stations)][t] = demand.predicted[ind] #demand.observed[ind] + sugg 
                                        self.station_demands_historical[origin_id][platform][tuple(transfer_stations)][t] = demand.historical[ind]

        

        
        
        
#         for idx, station in enumerate(self.stations[0:len(self.stations)-1]):
#             origin_id =  station.ids
#             for dest in self.stations[(idx+1):len(self.stations)]:
#                 dest_id = dest.ids
#                 demand = self.read_od_from_file(origin_id, dest_id)
#                 for ind, t in enumerate(range(0, Param.SIMULATION_TIME, 15*60)):
#                     self.station_demands_observed[station][dest][t] = demand.observed[ind]
#                     self.station_demands_predicted[station][dest][t] = demand.predicted[ind] #demand.observed[ind] + sugg 
#                     self.station_demands_historical[station][dest][t] = demand.historical[ind]

#         ####
#         # the first train to arrive at this station takes 7000 seconds to get there, there is one passenger arriving in the first
#         # time period that sufferes excessive waiting time. remove it. 
#         a =[st for st in self.stations if st.ids == 725][0]
#         self.station_demands_historical[a].values()[0][0]=0      
#         ####    
        
#         # want to keep track of a train's trajectory
        # {train : {direction : {dist_from_origin : destination}}}
        self.train_trajectories = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
        
    
    def _initiate_train_at_specific_station(self, train, station_id, param):
        station = self.return_station_by_id(station_id)
        train.next_station_id = param.stations[param.stations.index(station_id) + 1  ]
        train.prev_station_id = param.stations[param.stations.index(station_id)    ]
        train.is_in_service = True
        train.time_to_next_station = param.station_travel_times[station_id][train.next_station_id]
        train.position = station.position
        return train
        #
    
    
    def distribute_trains(self):
        i = 0
        for param, direction in zip(self.params, self.directions):
            for station_index in range(2,len(param.stations),4): # 5,6
                station_id = param.stations[station_index]
                tr = self.garages[direction].queue.popleft()
    #             tr = self.trains[i]
                self._trains[direction][i] = self._initiate_train_at_specific_station(tr, station_id, param)
    #             tr = self._initiate_train_at_specific_station(tr, station_id)
                i += 1
                print "train_id: ", tr.car_id
        print('number of re-distributed trains are : ' + str(i))
    
#     @classmethod
#     def get_next_station_id(self, station_id, param):
#         if station_id != 'garageE' and station_id != 'garageW':
#             current_index = param.stations.index(station_id)
#             if current_index != len(param.stations) - 1:
#                 # if this is not the last stop
#                 next_station_id = param.stations[current_index + 1]
#                 return next_station_id 
#             else:
#                 # it is the terminal station
#                 return param.terminal_
#         else:
#             return 560
#     @classmethod
#     def get_prev_station_id(self, station_id):
        
#         if station_id != 'garage':
#             current_index = Param.stations.index(station_id)
#             if current_index != 0:
#                 # if it's not the first station
#                 prev_station_id = Param.stations[current_index - 1]
#                 return prev_station_id 
#             else:
#                 # it is  the garage
#                 return "garage"
#         else:
#             return "garage"
    
    def read_od_from_file(self, origin_id, dest_id, list_of_files=None , data_path = None):
        if list_of_files == None: list_of_files=self.onlyfiles
        if data_path == None: data_path = self.data_path
        
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


    def return_params_and_stuff(self, line=None, just_my_oppsite=True):
            '''
            line is supposed to be other lines, not self.line
            just_my_oppsite is a convenience flag to return the other line's params
            '''
            if just_my_oppsite: 
                line = self.line
                # return central if current line is victoria. Not good really but hey...
                if line == "Victoria":
                    return ({"params": [Param_Central_WE, Param_Central_EW],
                            "directions": ["WE","EW"], 
                            "main_param" : Param_Central})

                elif line == "Central":
                    return ({"params": [Param_Victoria_SN, Param_Victoria_NS],
                            "directions": ["SN", "NS"], 
                            "main_param" : Param_Victoria})

  
            
    def return_garage_of_opposite_direction(self, current_direction):
        for direction in self.directions:
            if direction != current_direction:
                return self.garages[direction]  
            
    def return_name_of_intersecting_line(self, current_line):
        if current_line == "Central":
            return "Victoria"
        elif current_line == "Victoria":
            return "Central"        
    
    def return_station_by_id(self, station_id):
        # so that other classes can have access to the original object
        for idx, station in enumerate(self.stations):
            if station.ids == station_id:
                return self.stations[idx]
    
    
    