from config import * 
import time
from Param_Central import Param_Central, Param_Central_EW, Param_Central_WE
from Param_Victoria import Param_Victoria, Param_Victoria_NS, Param_Victoria_SN
from CentralMonitor import CentralMonitor
from God import God 
import csv
from copy import deepcopy


#def run():



simulation_time = Param_Central.SIMULATION_TIME #
simulation_time = 10000
MAX_POSITION = max(Param_Central.station_positions.values())
update_interval = 15 * 60 # 15 minutes 
btw_simulation_gap = 1000 # 20 mins shorter simulation time for the second iteration
first_iterations_simulation_time = simulation_time + 2 * btw_simulation_gap
second_iterations_simulation_time = simulation_time + 1 * btw_simulation_gap
third_iterations_simulation_time = simulation_time
#==============================================================================
# This part must be shared between real-life and the decision support simulations
#     
#==============================================================================

#==============================================================================
# the_god = God()
# the_god.make_central_monitor("Central")
# the_god.make_central_monitor("Victoria")   
#==============================================================================


#==============================================================================
# god.distribute_trains("Central")
# god.distribute_trains("Victoria")
#==============================================================================

# central_monitor_instance.distribute_trains()


#==============================================================================
# Simulation specific
#==============================================================================

def run_simulation(t_start, t_end, god_template, update_interval, prev_god = None, act_dumb= True, DEMAND_LEVEL="O",
                   param_central_EW= None, param_central_WE= None, param_victoria_NS= None, param_victoria_SN = None, record_state=False, save_fifteen = True):
                       
                       
    
  
    god_of_fifteen = None
    # initialize timers/headways
    if param_central_EW is None:
        print "############################################"
        print "initialize timers/headways"
        param_central_EW = Param_Central_EW()                       
        param_central_WE = Param_Central_WE()  
        param_victoria_NS = Param_Victoria_NS() 
        param_victoria_SN = Param_Victoria_SN()                   
        print "############################################"
    else :
        param_central_EW = deepcopy(param_central_EW)
        param_central_WE = deepcopy(param_central_WE)
        param_victoria_NS = deepcopy(param_victoria_NS)
        param_victoria_SN = deepcopy(param_victoria_SN)
        
    start_time = time.time()
    # since we need to keep the original god intact, as the other simulation should use the same one for initialization
    god = deepcopy(god_template)
    
    # set demand level i.e. historical, predicted, observed
    for name in god.monitors.keys():
        for n2, train_list in god.monitors[name]._trains.iteritems(): 
            for train in train_list :
                train.set_demand_level(DEMAND_LEVEL)
               
    
    def read_train_colors_from_god(this_god, some_god):
        
        
        for name in some_god.monitors.keys():
            
            for n, train_list in this_god.monitors[name]._trains.iteritems():    
                this_god_trains = [train.car_id for train in train_list ]
                tr_list = some_god.monitors[name]._trains[n] 
                prev_god_trains = [train.car_id for train in tr_list ]
                
            assert (this_god_trains == prev_god_trains )
            print "trains are the same " 
            
            this_run_stations = this_god.monitors[name].stations
            prev_run_stations = some_god.monitors[name].stations
            
            for this_station, prev_station in zip(this_run_stations, prev_run_stations ): 
                for plat_name, this_plat in this_station.platforms.iteritems():
                    prev_plat = prev_station.platforms[plat_name]
                    assert (prev_plat.ids == this_plat.ids)
                    assert (prev_plat.direction == this_plat.direction)
                    # import train colors 
                    this_plat.imported_train_colors = prev_plat.train_colors
                        
    if prev_god:
        # assert trains are the same
        
        # read train colors 
        read_train_colors_from_god(god, prev_god)
        
        
        
#==============================================================================
#     the_file = open('train_log.txt', 'wb') 
#     the_file_writer = csv.writer(the_file)
#==============================================================================
    for t in range(int(t_start), int(t_end)):
    
        # produce passengers every 15 minutes. Needed to update demand as new obs. come in every 15 minutes
    #    if t % (15*60) == 0:
        if t >= (60 * 60) and t % (15*60) == 0: # give an hour warm up
    #        t = t - (60*60)
            [station.produce_passsengers(god.monitors["Central"], act_dumb = act_dumb, t_offset=t ) 
                                 for station in god.monitors["Central"].stations[0:len(god.monitors["Central"].stations)-1]]
            [station.produce_passsengers(god.monitors["Victoria"], act_dumb=act_dumb, t_offset=t ) 
                                 for station in god.monitors["Victoria"].stations[0:len(god.monitors["Victoria"].stations)-1]]
    
        # dispatch trains from garage every HEADWAY minutes
        for param in [param_victoria_NS, param_victoria_SN]:
            if param.should_dispatch():
                direction = param.direction
                god.monitors["Victoria"].garages[direction].dispatch_train(t) 
                
        for param in [param_central_EW, param_central_WE]:
            if param.should_dispatch():
                direction = param.direction
                god.monitors["Central"].garages[direction].dispatch_train(t)
                        
        # Central
        for station in god.monitors["Central"].stations:
            station.update(t)
        # Victoria  
        for station in god.monitors["Victoria"].stations:
            station.update(t)
        # Central
        for _, train_list in god.monitors["Central"]._trains.iteritems():
            for train in train_list:
                train.update(god.monitors["Central"], t, god)
        # Victoria
        for _, train_list in god.monitors["Victoria"]._trains.iteritems():
            for train in train_list:
                train.update(god.monitors["Victoria"], t, god)
        
        
           
                    
       # save god every 15 minutes 
        if save_fifteen :
#            if t % ((15 * 60) -1)== 0 and t != int(t_start) and t != int(t_end):
            if t == t_start + int((t_end - t_start)/2) -1:
                print "#############################################"
                print "#############################################"
                print "#############################################"
                print "t is ", t
                print int((t_end - t_start)/2) -1
                print "#############################################"
                print "#############################################"
                print "#############################################"
                god_of_fifteen = deepcopy(god)
                param_central_EW_15 =  deepcopy(param_central_EW)
                param_central_WE_15 = deepcopy(param_central_WE)
                param_victoria_NS_15 = deepcopy(param_victoria_NS)
                param_victoria_SN_15 = deepcopy(param_victoria_SN)            
                
                
                
                # Central
                for _, train_list in god_of_fifteen.monitors["Central"]._trains.iteritems():
                    for train in train_list:
                        train.save_state_for_other_iterations()
                        
                # Victoria
                for _, train_list in god_of_fifteen.monitors["Victoria"]._trains.iteritems():
                    for train in train_list:
                        train.save_state_for_other_iterations()

            
#==============================================================================
#         if record_state : 
#             csv_file =  open("C:\\Users\\Peyman.n\\Documents\\Viz_of_simulation-victoriaAndcentral\\static\\csv/trains_states.csv", 'wb') 
#             csv_writer = csv.writer(csv_file)  
#             csv_writer.writerow(('t', 'car_id', 'position', 'load', 'load_history_array', "next_station_id"))
#             
#             st_csv_file =  open("C:\\Users\\Peyman.n\\Documents\\Viz_of_simulation-victoriaAndcentral\\static\\csv\\stations_states.csv", 'wb') 
#             st_csv_writer = csv.writer(st_csv_file)  
#             st_csv_writer.writerow(('t', 'station_id', 'platform', 'queue', 'hist_queue_array'))
#             
#             victoria_csv_file =  open("C:\\Users\\Peyman.n\\Documents\\Viz_of_simulation-victoriaAndcentral\\static\\csv/trains_states_victoria.csv", 'wb') 
#             victoria_csv_writer = csv.writer(victoria_csv_file)  
#             victoria_csv_writer.writerow(('t', 'car_id', 'position', 'load', 'load_history_array', "next_station_id"))
#             
#             victoria_st_csv_file =  open("C:\\Users\\Peyman.n\\Documents\\Viz_of_simulation-victoriaAndcentral\\static\\csv\\stations_states_victoria.csv", 'wb') 
#             victoria_st_csv_writer = csv.writer(victoria_st_csv_file)  
#             victoria_st_csv_writer.writerow(('t', 'station_id', 'platform', 'queue', 'hist_queue_array'))
#     
#             if t % (60 ) == 0:
#                 # write state to file
#                 # Central
#                 for _, train_list in god.monitors["Central"]._trains.iteritems():
#                     for train in train_list:
#                         train.save_state(t, csv_writer)
#                 for station in god.monitors["Central"].stations:
#                     station.save_state(t, st_csv_writer)
#                     
#                 # write state to file
#                 # Victoria 
#                 for _, train_list in god.monitors["Victoria"]._trains.iteritems():
#                     for train in train_list:
#                         train.save_state(t, victoria_csv_writer)
#                 for station in god.monitors["Victoria"].stations:
#                     station.save_state(t, victoria_st_csv_writer)
#                     
#                     
#             csv_file.close()
#             st_csv_file.close()
#             victoria_csv_file.close()
#             victoria_st_csv_file.close()
#==============================================================================
    
    print "DONE"
    # clean_up 
    # Very important, otherwise dispatching is gonna be messed up for the other simulation
    # but this is not the correct approach in general, because when this wants to continue, it
    # has to remember where it was
#    for param in [Param_Victoria_NS, Param_Victoria_SN, Param_Central_EW, Param_Central_WE]:
#        param.timer = 0
        
    end_time = time.time()    
    
    
    # save updates
    # Central
    for _, train_list in god.monitors["Central"]._trains.iteritems():
        for train in train_list:
            train.save_state_for_other_iterations()
    # Victoria
    for _, train_list in god.monitors["Victoria"]._trains.iteritems():
        for train in train_list:
            train.save_state_for_other_iterations()
    
    print (end_time - start_time)/60
    
    if save_fifteen: 
        return(god, param_victoria_NS, param_victoria_SN, param_central_EW, param_central_WE, god_of_fifteen,
               param_victoria_NS_15, param_victoria_SN_15, param_central_EW_15, param_central_WE_15)
    else : 
        return(god, param_victoria_NS, param_victoria_SN, param_central_EW, param_central_WE, god_of_fifteen)
#==============================================================================
# 
#==============================================================================
    
def run_DS(t_start, t_end, god_template, update_interval, prev_god = None, DEMAND_LEVEL="P",
                   param_central_EW= None, param_central_WE= None, param_victoria_NS= None, param_victoria_SN = None):
                       
    DS_god, _, _, _, _, _, _, _, _, _ = run_simulation(t_start, t_end, god_template, update_interval, DEMAND_LEVEL = DEMAND_LEVEL, param_central_EW = param_central_EW, param_central_WE = param_central_WE,
                                                 param_victoria_NS = param_victoria_NS, param_victoria_SN = 
                                                 param_victoria_SN, act_dumb= True)
    print "############################################"
    print "Finished 1st round of DS"
    DS_god_second_iterations, param_victoria_NS2, param_victoria_SN2, param_central_EW2, param_central_WE2, _, _, _, _, _ = run_simulation(t_start, t_end, god_template, update_interval, DEMAND_LEVEL = DEMAND_LEVEL, param_central_EW = param_central_EW, param_central_WE = param_central_WE,
                                                 param_victoria_NS = param_victoria_NS, param_victoria_SN = 
                                                 param_victoria_SN, act_dumb = False, prev_god = DS_god )
    print "############################################"        
    print "Finished 2nd round of DS"
    DS_god_third_iterations, param_victoria_NS3, param_victoria_SN3, param_central_EW3, param_central_WE3, god_of_fifteen, \
    param_victoria_NS_15, param_victoria_SN_15, param_central_EW_15, param_central_WE_15 = run_simulation(t_start, t_end, god_template, update_interval, DEMAND_LEVEL = DEMAND_LEVEL, param_central_EW = param_central_EW, param_central_WE = param_central_WE,
                                                 param_victoria_NS = param_victoria_NS, param_victoria_SN = 
                                                 param_victoria_SN, act_dumb = False, prev_god = DS_god_second_iterations )
    print "############################################"
    print "Finished 3rd round of DS"
    return DS_god_third_iterations,  god_of_fifteen, param_victoria_NS_15, param_victoria_SN_15, param_central_EW_15, param_central_WE_15
    


#==============================================================================
# 
#==============================================================================



def run_RW(t_start, t_end, god_template, update_interval, prev_god,  DEMAND_LEVEL="O",
                   param_central_EW= None, param_central_WE= None, param_victoria_NS= None, param_victoria_SN = None):
    
    RW_god, param_victoria_NS, param_victoria_SN, param_central_EW, param_central_WE, _ = run_simulation(t_start, t_end, god_template, update_interval, prev_god = prev_god, DEMAND_LEVEL = DEMAND_LEVEL, param_central_EW = param_central_EW, param_central_WE = param_central_WE,
                                                 param_victoria_NS = param_victoria_NS, param_victoria_SN = 
                                                 param_victoria_SN, act_dumb = False, record_state = True, save_fifteen = False)
     
    print "FINISHED RW"
    print "############################################"    
    return RW_god, param_victoria_NS, param_victoria_SN, param_central_EW, param_central_WE

    


def update_god_of_15 (go15, rw):
    
#    go15 = deepcopy(go15)
    for m_name in go15.monitors.keys(): # line ex. Central
        for (n1, train_list_go15), (n2, train_list_rw) in zip(go15.monitors[m_name]._trains.iteritems(), rw.monitors[m_name]._trains.iteritems()): 
            for tr1, tr2 in zip(train_list_go15, train_list_rw):
                assert tr1.car_id == tr2.car_id
                tr1.read_state_from_other_iterations(tr2._save_detailed_state_for_later)
                
        
        for station_gop15, station_rw in zip(go15.monitors[m_name].stations, rw.monitors[m_name].stations):
            assert station_gop15.ids == station_rw.ids 
            for direction in go15.monitors[m_name].directions: # ex. EW
                plt_gop15 = station_gop15.platforms[direction]
                plt_rw = station_rw.platforms[direction]                
                plt_gop15.upcoming_trains = plt_rw.upcoming_trains
                
    return go15
            
            
        

the_god = God()
the_god.make_central_monitor("Central")
the_god.make_central_monitor("Victoria")   


start_time = time.time() 

god_story = []

simulation_time = 120*60
for t in range(0, simulation_time , 15 * 60):
    start_t = t
    t_DS_end = t + 30 * 60 -1
    t_RW_end = t + 15 * 60 -1
    
    print "t : ", t, start_t
    
    if start_t == 0 :
        
        DS_god, god_of_fifteen, param_victoria_NS_15, param_victoria_SN_15, param_central_EW_15, param_central_WE_15 = run_DS(start_t, t_DS_end, the_god, update_interval)
        
        RW_god, param_victoria_NS, param_victoria_SN, param_central_EW, param_central_WE = run_RW(start_t, t_RW_end, the_god, update_interval, prev_god = DS_god)
        
    else :
        
        assert param_central_EW is not None
        
        DS_god, god_of_fifteen, param_victoria_NS_15, param_victoria_SN_15, param_central_EW_15, param_central_WE_15 = run_DS(start_t, t_DS_end, prev_DS_god, update_interval, param_central_EW = param_central_EW_15, param_central_WE = param_central_WE_15, param_victoria_NS = param_victoria_NS_15, param_victoria_SN = param_victoria_SN_15)
                                                 
    
        RW_god, param_victoria_NS, param_victoria_SN, param_central_EW, param_central_WE = run_RW (start_t, t_RW_end, prev_RW_god, update_interval, prev_god = DS_god, param_central_EW = param_central_EW, param_central_WE = param_central_WE, param_victoria_NS = param_victoria_NS, param_victoria_SN =  param_victoria_SN)
    
    # book keeping
    god_story.append(DS_god)
    # update god_of_fifteen based on RW_god
    updated_god_of_fifteen = update_god_of_15(god_of_fifteen, RW_god)
               
    
    
    prev_RW_god = RW_god 
    prev_DS_god = updated_god_of_fifteen 
    
    
    
end_time = time.time()   
print (end_time - start_time)/60

                  
#==============================================================================
# print "#############################################"
# print "Start the second iteration "
# csv_file =  open("C:\\Users\\Peyman.n\\Documents\\Viz_of_simulation-victoriaAndcentral\\static\\csv/trains_states.csv", 'wb') 
# csv_writer = csv.writer(csv_file)  
# csv_writer.writerow(('t', 'car_id', 'position', 'load', 'load_history_array', "next_station_id"))
# 
# st_csv_file =  open("C:\\Users\\Peyman.n\\Documents\\Viz_of_simulation-victoriaAndcentral\\static\\csv\\stations_states.csv", 'wb') 
# st_csv_writer = csv.writer(st_csv_file)  
# st_csv_writer.writerow(('t', 'station_id', 'platform', 'queue', 'hist_queue_array'))
# 
# victoria_csv_file =  open("C:\\Users\\Peyman.n\\Documents\\Viz_of_simulation-victoriaAndcentral\\static\\csv/trains_states_victoria.csv", 'wb') 
# victoria_csv_writer = csv.writer(victoria_csv_file)  
# victoria_csv_writer.writerow(('t', 'car_id', 'position', 'load', 'load_history_array', "next_station_id"))
# 
# victoria_st_csv_file =  open("C:\\Users\\Peyman.n\\Documents\\Viz_of_simulation-victoriaAndcentral\\static\\csv\\stations_states_victoria.csv", 'wb') 
# victoria_st_csv_writer = csv.writer(victoria_st_csv_file)  
# victoria_st_csv_writer.writerow(('t', 'station_id', 'platform', 'queue', 'hist_queue_array'))
# 
# DS_god_second_iterations, param_victoria_NS2, param_victoria_SN2, param_central_EW2, param_central_WE2 = run_simulation(second_iterations_simulation_time, 
#                                           the_god, csv_file, st_csv_file,
#                                           victoria_csv_file, victoria_st_csv_file, update_interval,
#                                           prev_god=DS_god, act_dumb = False )
# print "#############################################"
# 
# 
# print "#############################################"
# print "Start the third iteration "
# csv_file =  open("C:\\Users\\Peyman.n\\Documents\\Viz_of_simulation-victoriaAndcentral\\static\\csv/trains_states.csv", 'wb') 
# csv_writer = csv.writer(csv_file)  
# csv_writer.writerow(('t', 'car_id', 'position', 'load', 'load_history_array', "next_station_id"))
# 
# st_csv_file =  open("C:\\Users\\Peyman.n\\Documents\\Viz_of_simulation-victoriaAndcentral\\static\\csv\\stations_states.csv", 'wb') 
# st_csv_writer = csv.writer(st_csv_file)  
# st_csv_writer.writerow(('t', 'station_id', 'platform', 'queue', 'hist_queue_array'))
# 
# victoria_csv_file =  open("C:\\Users\\Peyman.n\\Documents\\Viz_of_simulation-victoriaAndcentral\\static\\csv/trains_states_victoria.csv", 'wb') 
# victoria_csv_writer = csv.writer(victoria_csv_file)  
# victoria_csv_writer.writerow(('t', 'car_id', 'position', 'load', 'load_history_array', "next_station_id"))
# 
# victoria_st_csv_file =  open("C:\\Users\\Peyman.n\\Documents\\Viz_of_simulation-victoriaAndcentral\\static\\csv\\stations_states_victoria.csv", 'wb') 
# victoria_st_csv_writer = csv.writer(victoria_st_csv_file)  
# victoria_st_csv_writer.writerow(('t', 'station_id', 'platform', 'queue', 'hist_queue_array'))
# 
# DS_god_third_iterations, param_victoria_NS3, param_victoria_SN3, param_central_EW3, param_central_WE3 = run_simulation(third_iterations_simulation_time, 
#                                           the_god, csv_file, st_csv_file,
#                                           victoria_csv_file, victoria_st_csv_file, update_interval,
#                                           prev_god=DS_god_second_iterations, act_dumb = False )
# print "#############################################"
# 
# 
#==============================================================================
