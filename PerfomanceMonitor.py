# -*- coding: utf-8 -*-
"""
Created on Mon Jul 10 14:07:25 2017

@author: Peyman
"""
from collections import defaultdict
class PerformanceMonitor(object):
    '''
    A place to keep all the performance measures
    
    '''
    def __init__(self):
        '''
        These should be time-based dictionaries, so that later on statistics can be 
        computed for specific time periods
        
        '''
        self.all_passengers_created_predicted = []
        self.all_passengers_created_observed = []
        self.all_passengers_created_historical = []
    
        self.all_passengers_offloaded = defaultdict(lambda : defaultdict(list))
        self.passenger_denied_boarding = defaultdict(lambda : defaultdict(list))
        
        
#==============================================================================
#         self.all_passengers_offloaded = defaultdict(list)
#         self.passenger_denied_boarding = defaultdict(list)
#         
#     
#==============================================================================
        self.all_passengers_boarded = []
        self.all_passengers_emptied_at_last = []
        
        
    