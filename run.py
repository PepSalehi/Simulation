from config import * 
import time
from Param_Central import Param_Central, Param_Central_EW, Param_Central_WE
from Param_Victoria import Param_Victoria, Param_Victoria_NS, Param_Victoria_SN
from CentralMonitor import CentralMonitor
from God import God 
import csv
from copy import deepcopy
from start import run_DS, run_RW, update_god_of_15
import gc

#def run(simulation_time =  2 * 3600):

simulation_time = int(18000)
update_interval = 15 * 60 # 15 minutes 

the_god = God()
the_god.make_central_monitor("Central")
the_god.make_central_monitor("Victoria")   


start_time = time.time() 

god_story_15 = []
god_story_30 = []
history = []

for t in range(0, simulation_time , 15 * 60 ):
    start_t = t
    t_DS_end = t + 30 * 60 - 1 #  BE VERY CAREFUL ABOUT THESE TIMINGS. CAN MESS UP DEMAND PRODUCTION (15 MINS), AND HENCE THE WHOLE SIMULATION
    t_RW_end = t + 15 * 60 - 1
    
    print "t : ", t, start_t
    
    if start_t == 0 :
        
        
        DS_god, god_of_15, param_victoria_NS_15, param_victoria_SN_15, param_central_EW_15, param_central_WE_15 = run_DS(start_t, t_DS_end, the_god, update_interval)
        
        RW_god, param_victoria_NS_rw, param_victoria_SN_rw, param_central_EW_rw, param_central_WE_rw = run_RW(start_t, t_RW_end, the_god, update_interval, prev_god = DS_god)
        
    else :
        
#        assert param_central_EW_rw is not None
        
        DS_god, god_of_15, param_victoria_NS_15, param_victoria_SN_15, param_central_EW_15, param_central_WE_15 = run_DS(start_t, t_DS_end, god_of_15, update_interval, param_central_EW = param_central_EW_15, param_central_WE = param_central_WE_15, param_victoria_NS = param_victoria_NS_15, param_victoria_SN = param_victoria_SN_15)
                                                 
        
        RW_god, param_victoria_NS_rw, param_victoria_SN_rw, param_central_EW_rw, param_central_WE_rw  = run_RW (start_t, t_RW_end, RW_god, update_interval, prev_god = DS_god, param_central_EW = param_central_EW_rw, param_central_WE = param_central_WE_rw, param_victoria_NS = param_victoria_NS_rw, param_victoria_SN =  param_victoria_SN_rw)
        
        
#==============================================================================
#         RW_god, param_victoria_NS_rw, param_victoria_SN_rw, param_central_EW_rw, param_central_WE_rw = run_RW (start_t, t_RW_end, prev_RW_god, update_interval, prev_god = DS_god, param_central_EW = param_central_EW_rw, param_central_WE = param_central_WE_rw, param_victoria_NS = param_victoria_NS_rw, param_victoria_SN =  param_victoria_SN_rw)
#==============================================================================
    

#=======================================================================DONE=======
    # update god_of_fifteen based on RW_god
    print "UPDATING at time ", t_RW_end
    history = update_god_of_15(god_of_15, RW_god, history)
               
#    
#    prev_RW_god = RW_god 
#    prev_DS_god = god_of_15
    
#    gc.collect()
    print "Finished start_t = ", start_t, "till DS_end_t", t_DS_end, "and rw t", t_RW_end 
    
#    time.sleep(60)
#    break
end_time = time.time()   
print (end_time - start_time)/60

              


























