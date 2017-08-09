# -*- coding: utf-8 -*-
"""
Created on Mon Aug 07 15:16:47 2017

@author: Peyman
"""

from config import *




class Save_Object(object):
    def __init__(self, god):
        self.god = god
        
        
        
        # {train_id : queue(color)}
        self.train_colors = defaultdict(lambda: deque())
        self.train_trajectories = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    
    
    
    def save_state(god):
         for name in god.monitors.keys():
             
             this_run_stations = god.monitors[name].stations
             for this_station in this_run_stations: 
                for plat_name, this_plat in this_station.platforms.iteritems():
                    
                    prev_plat = prev_station.platforms[plat_name]
                    assert (prev_plat.ids == this_plat.ids)
                    assert (prev_plat.direction == this_plat.direction)
                    # import train colors 
                    this_plat.imported_train_colors = this_plat.train_colors
 
        