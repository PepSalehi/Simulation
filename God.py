# -*- coding: utf-8 -*-
"""
Created on Mon Jul 10 15:04:14 2017

@author: Peyman
"""
from CentralMonitor import CentralMonitor

class God(object):
    ''' 
    '''
    def __init__(self):
        self.monitors = {}
    def make_central_monitor(self, name):
        self.monitors[name] = CentralMonitor(name)
    def distribute_trains(self, name):
        self.monitors[name].distribute_trains()
#         return self.monitors[name]
#     def return_central_monitor_by_name(self, name):
#         return self.monitors[name]
        
        
        
        
        
        
        
        
        