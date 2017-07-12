# -*- coding: utf-8 -*-
"""
Created on Mon Jul 10 15:01:43 2017

@author: Peyman
"""
from config import * 
from Platform import Platform 
from Param_Central import Param_Central, Param_Central_WE, Param_Central_EW
from Param_Victoria import Param_Victoria, Param_Victoria_NS, Param_Victoria_SN

class Station(object):
    
    def __init__(self, ids, line ,demand=0, platforms=None):
        self.ids = ids
        self.demand = 0
        self.line = line
                
        ####### Platforms #######
        if self.line == "Central":
            if platforms is None:
                self.platforms = {"WE" : Platform("WE", ids, self.line, Param_Central_WE ), "EW" : Platform("EW", ids, self.line, Param_Central_EW)}
                self.params = {"WE": Param_Central_WE, "EW": Param_Central_EW}
        elif self.line == "Victoria":
            if platforms is None:
                self.platforms = {"SN" : Platform("SN", ids, self.line, Param_Victoria_SN), "NS" : Platform("NS", ids, self.line, Param_Victoria_NS)}
                self.params = {"SN": Param_Victoria_SN, "NS" : Param_Victoria_NS}

            
    def save_state(self, t, csv_writer):
        '''
        write attributes to csv file for visualization
        
        '''
        for platform in self.platforms.values():
            platform.save_state(t, csv_writer)
        
    def produce_passsengers(self, central_monitor_instance, t_offset, time_range = 15*60):
        for platform in self.platforms.values():
            platform.produce_passsengers(central_monitor_instance, t_offset, time_range = 15*60)
    def get_platform_id_matching_target_destination(self, dest_id, transfer_station_id):
        for name, platform in self.platforms.iteritems():
            if dest_id in platform.get_stations_after_this(transfer_station_id):
                return name
            
    def update(self, t):
        for platform in self.platforms.values():
            platform.update(t)

            
