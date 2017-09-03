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



def run_simulation(t_start, t_end, god_template, update_interval, prev_god = None, act_dumb= True, DEMAND_LEVEL = "O",
                   param_central_EW= None, param_central_WE= None, param_victoria_NS= None, param_victoria_SN = None, record_state=False, save_fifteen = True):
        
    
    god_of_fifteen = None
    # initialize timers/headways
    if param_central_EW is None:
#        print "############################################"
        print "initialize timers/headways"
        param_central_ew = Param_Central_EW()                       
        param_central_we = Param_Central_WE()  
        param_victoria_ns = Param_Victoria_NS() 
        param_victoria_sn = Param_Victoria_SN()                   
#        print "############################################"
    else :
        param_central_ew = deepcopy(param_central_EW)
        param_central_we = deepcopy(param_central_WE)
        param_victoria_ns = deepcopy(param_victoria_NS)
        param_victoria_sn = deepcopy(param_victoria_SN)
    
#    print "first chunck ", time.time() - s_
    
    start_time = time.time()
    # since we need to keep the original god intact, as the other simulation should use the same one for initialization
    god = deepcopy(god_template)
    
#    s_ = time.time()
    # set demand level i.e. historical, predicted, observed
    for name in god.monitors.keys():
        for n2, train_list in god.monitors[name]._trains.iteritems(): 
            for train in train_list :
                train.set_demand_level(DEMAND_LEVEL)
    for name in god.monitors.keys():
        for n2, train_list in god.monitors[name]._trains.iteritems(): 
            for train in train_list :
                assert train.DEMAND_LEVEL == [DEMAND_LEVEL]
#    print "2nd chunck ", time.time() - s_           
    
    #
    def read_train_colors_from_god(this_god, some_god):
        
        for name in some_god.monitors.keys():
            
#==============================================================================
#             for n, train_list in this_god.monitors[name]._trains.iteritems():    
#                 this_god_trains = [train.car_id for train in train_list ]
#                 tr_list = some_god.monitors[name]._trains[n] 
#                 prev_god_trains = [train.car_id for train in tr_list ]
#                 
#             assert (this_god_trains == prev_god_trains )
#             print "trains are the same " 
#==============================================================================
            
            this_run_stations = this_god.monitors[name].stations
            prev_run_stations = some_god.monitors[name].stations
            
            for this_station, prev_station in zip(this_run_stations, prev_run_stations ): 
                for plat_name, this_plat in this_station.platforms.iteritems():
                    prev_plat = prev_station.platforms[plat_name]
                    assert (prev_plat.ids == this_plat.ids)
                    assert (prev_plat.direction == this_plat.direction)
                    # import train colors 
                    this_plat.imported_train_colors = prev_plat.train_colors
#                    print this_plat.imported_train_colors
    #
    if prev_god:
     
        # read train colors 
        read_train_colors_from_god(god, prev_god)

    for t in range(int(t_start), int(t_end)):
        # produce passengers every 15 minutes. Needed to update demand as new obs. come in every 15 minutes
        if t >= (60 * 60) and t % (15*60) == 0: # give an hour warm up
            [station.produce_passsengers(central_monitor_instance = god.monitors["Central"], level = DEMAND_LEVEL, act_dumb = act_dumb, t_offset = t ) 
                                 for station in god.monitors["Central"].stations[0:len(god.monitors["Central"].stations)-1]]
                                     
            [station.produce_passsengers(central_monitor_instance = god.monitors["Victoria"], level = DEMAND_LEVEL, act_dumb = act_dumb, t_offset = t ) 
                                 for station in god.monitors["Victoria"].stations[0:len(god.monitors["Victoria"].stations)-1]]
        
        # dispatch trains from garage every HEADWAY minutes
        for param in [param_victoria_ns, param_victoria_sn]:
            if param.should_dispatch():
                direction = param.direction
                god.monitors["Victoria"].garages[direction].dispatch_train(t, god.monitors["Victoria"] ) 
    
        for param in [param_central_ew, param_central_we]:
            if param.should_dispatch():
                direction = param.direction
                god.monitors["Central"].garages[direction].dispatch_train(t, god.monitors["Central"])
                
        # Central
        for station in god.monitors["Central"].stations:
            station.update(t, DEMAND_LEVEL)
        
        # Victoria  
        for station in god.monitors["Victoria"].stations:
            station.update(t, DEMAND_LEVEL)
       
        # Central
        for _, train_list in god.monitors["Central"]._trains.iteritems():
            for train in train_list:
                train.update(god.monitors["Central"], t, god, int(t_start))
        
#         Victoria
        for _, train_list in god.monitors["Victoria"]._trains.iteritems():
            for train in train_list:
                train.update(god.monitors["Victoria"], t, god, int(t_start))
        
        
           
                    
       # save god every 15 minutes 
        if save_fifteen :
#            s_ = time.time()
#            if t % ((15 * 60) -1)== 0 and t != int(t_start) and t != int(t_end):
            # it is important to save it one second sooner, because otherwise demand will be generated 
            if t == t_start + int((t_end - t_start)/2) :
                print "SAVING 15 at t", t
                god_of_fifteen = deepcopy(god)
                assert god_of_fifteen is not god
                param_central_EW_15 = deepcopy(param_central_ew)
                param_central_WE_15 = deepcopy(param_central_we)
                param_victoria_NS_15 = deepcopy(param_victoria_ns)
                param_victoria_SN_15 = deepcopy(param_victoria_sn)            
                
                # Central
                for _, train_list in god_of_fifteen.monitors["Central"]._trains.iteritems():
                    for train in train_list:
                        train.save_state_for_other_iterations()
                        
                # Victoria
                for _, train_list in god_of_fifteen.monitors["Victoria"]._trains.iteritems():
                    for train in train_list:
                        train.save_state_for_other_iterations()
                        
                
                


    
    print "DONE"
    
    
    # clean_up 
    # Very important, otherwise dispatching is gonna be messed up for the other simulation
    # but this is not the correct approach in general, because when this wants to continue, it
    # has to remember where it was
#    for param in [Param_Victoria_NS, Param_Victoria_SN, Param_Central_EW, Param_Central_WE]:
#        param.timer = 0
        
    end_time = time.time()    
    
    # What is the purpose of this save? -> for when it is run with real-world 
    # save updates
    # Central
    for _, train_list in god.monitors["Central"]._trains.iteritems():
        for train in train_list:
            train.save_state_for_other_iterations()
    # Victoria
    for _, train_list in god.monitors["Victoria"]._trains.iteritems():
        for train in train_list:
            train.save_state_for_other_iterations()
    
    print (end_time - start_time) / 60
    
    if save_fifteen: 
        return(god, param_victoria_ns, param_victoria_sn, param_central_ew, param_central_we, god_of_fifteen,
               param_victoria_NS_15, param_victoria_SN_15, param_central_EW_15, param_central_WE_15)
    else : 
        return(god, param_victoria_ns, param_victoria_sn, param_central_ew, param_central_we, god_of_fifteen)
#==============================================================================
# 
#==============================================================================
    
def run_DS(t_start, t_end, god_template, update_interval, prev_god = None, DEMAND_LEVEL = "P",
                   param_central_EW= None, param_central_WE= None, param_victoria_NS= None, param_victoria_SN = None):
     
    print "############################################"
    print "started 1st round of DS"
    print "############################################"                  
    DS_god, _, _, _, _, g1, _, _, _, _ = run_simulation(t_start, t_end, god_template, update_interval, DEMAND_LEVEL = DEMAND_LEVEL, param_central_EW = param_central_EW, param_central_WE = param_central_WE,
                                                 param_victoria_NS = param_victoria_NS, param_victoria_SN = 
                                                 param_victoria_SN, act_dumb= True)
    
    
    print "############################################"
    print "Finished 1st round of DS"
    print "############################################"
    


    
    print "############################################"
    print "started 2nd round of DS"
    print "############################################"
    DS_god_second_iterations, param_victoria_NS2, param_victoria_SN2, param_central_EW2, param_central_WE2, g2, _, _, _, _ = run_simulation(t_start, t_end, god_template, update_interval, DEMAND_LEVEL = DEMAND_LEVEL, param_central_EW = param_central_EW, param_central_WE = param_central_WE,
                                                 param_victoria_NS = param_victoria_NS, param_victoria_SN = 
                                                 param_victoria_SN, act_dumb = False, prev_god = DS_god )
                                                 
    
    
    print "############################################"        
    print "Finished 2nd round of DS"
    print "############################################"
#    del DS_god
    print "############################################"
    print "started 3rd round of DS"
    print "############################################"
    DS_god_third_iterations, param_victoria_NS3, param_victoria_SN3, param_central_EW3, param_central_WE3, god_of_fifteen, \
    param_victoria_NS_15, param_victoria_SN_15, param_central_EW_15, param_central_WE_15 = run_simulation(t_start, t_end, god_template, update_interval, DEMAND_LEVEL = DEMAND_LEVEL, param_central_EW = param_central_EW, param_central_WE = param_central_WE,
                                                 param_victoria_NS = param_victoria_NS, param_victoria_SN = 
                                                 param_victoria_SN, act_dumb = False, prev_god = DS_god_second_iterations )
    print "############################################"
    print "Finished 3rd round of DS"
    print "############################################"
    
#==============================================================================
#     print " queue lengths are " 
#     print len(god_of_fifteen.monitors['Victoria'].garages['NS'].queue)
#     print len(god_of_fifteen.monitors['Victoria'].garages['SN'].queue)
#     print len(god_of_fifteen.monitors['Central'].garages['EW'].queue)
#     print len(god_of_fifteen.monitors['Central'].garages['WE'].queue)
#     
#==============================================================================
    
#==============================================================================
#     print "Total number of pax produced is Victoria", len(g1.monitors['Victoria'].all_passengers_created_observed)
#     print "Total number of pax produced is ", len(g2.monitors['Victoria'].all_passengers_created_observed)
#     print "Total number of pax produced is ", len(god_of_fifteen.monitors['Victoria'].all_passengers_created_observed)    
#     
#     print "Total number of pax produced is Central", len(g1.monitors['Central'].all_passengers_created_observed)
#     print "Total number of pax produced is ", len(g2.monitors['Central'].all_passengers_created_observed)
#     print "Total number of pax produced is ", len(god_of_fifteen.monitors['Central'].all_passengers_created_observed) 
#==============================================================================
#    del DS_god_second_iterations
    return DS_god_third_iterations, god_of_fifteen, param_victoria_NS_15, param_victoria_SN_15, param_central_EW_15, param_central_WE_15
    


#==============================================================================
# 
#==============================================================================



def run_RW(t_start, t_end, god_template, update_interval, prev_god,  DEMAND_LEVEL="O",
                   param_central_EW= None, param_central_WE= None, param_victoria_NS= None, param_victoria_SN = None):
    
    RW_god, param_victoria_ns, param_victoria_sn, param_central_ew, param_central_we, _ = run_simulation(t_start, t_end, god_template, update_interval, prev_god = prev_god, DEMAND_LEVEL = DEMAND_LEVEL, param_central_EW = param_central_EW, param_central_WE = param_central_WE,
                                                 param_victoria_NS = param_victoria_NS, param_victoria_SN = 
                                                 param_victoria_SN, act_dumb = False, record_state = True, save_fifteen = False)
    print "############################################"
    print "FINISHED RW"
    print "############################################"   
    

    
    
#==============================================================================
#     
#     print "Total number of pax produced is Central ", len(RW_god.monitors['Central'].all_passengers_created_observed) 
#     print "Total number of pax produced is Victoria ", len(RW_god.monitors['Victoria'].all_passengers_created_observed) 
# 
#==============================================================================
    return RW_god, param_victoria_ns, param_victoria_sn, param_central_ew, param_central_we

    


def update_god_of_15 (go15, rw, history):
    
#    go15 = deepcopy(go15)
    # upadte train status
    
    temp = history
    for line_ in ['Central', 'Victoria']: # line ex. Central
        for (n1, train_list_go15), (n2, train_list_rw) in zip(go15.monitors[line_]._trains.iteritems(), rw.monitors[line_]._trains.iteritems()): 
            for tr1, tr2 in zip(train_list_go15, train_list_rw):
                assert tr1.car_id is tr2.car_id
              
                flag= False
                if tr1.is_in_service:
                    e1 = tr1.distance_from_garage
                    flag = True
#                    print "distance to front train, before ", tr1._get_distance_to_front_train()
                    
                tr1.read_state_from_other_iterations(tr2._save_detailed_state_for_later, go15.monitors[line_])
                if tr1.is_in_service:            
                    
                    tr1.update_next_platform_info(go15.monitors[line_])
                    if flag:
                        e2 = tr1.distance_from_garage
                        temp.append(e2-e1)
                        
#                        print "distance to front train, after ", tr1._get_distance_to_front_train()
                    
                    
                    
        # update upcoming trains
        for station_gop15, station_rw in zip(go15.monitors[line_].stations, rw.monitors[line_].stations):
            assert station_gop15.ids == station_rw.ids 
            for direction in go15.monitors[line_].directions: # ex. EW
                plt_gop15 = station_gop15.platforms[direction]
                plt_rw = station_rw.platforms[direction]                
                plt_gop15.upcoming_trains = deepcopy(plt_rw.upcoming_trains)
                
#                for car_id, info in plt_gop15.upcoming_trains.iteritems():
#                    if info[1][1]
                
    
    return temp  
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
        # update garages 
#==============================================================================
#         if line_ == 'Central': directions = ['EW', 'WE']
#         if line_ == 'Victoria': directions = ['NS', 'SN']
#         for direction in directions:
#             assert go15.monitors[line_].garages[direction].garage_name == rw.monitors[line_].garages[direction].garage_name
# #        go15.monitors[line_].garages = deepcopy(rw.monitors[line_].garages)
# #        for direction in directions :
# #            print go15.monitors[line_].garages[direction].garage_name
#             go15.monitors[line_].garages[direction].queue = deepcopy(rw.monitors[line_].garages[direction].queue)
#             go15.monitors[line_].garages[direction]._dispatched_train_ids = deepcopy(rw.monitors[line_].garages[direction]._dispatched_train_ids)
#     #            go15.monitors[line_].garages[direction].Param = rw.monitors[line_].garages[direction].Param
#             go15.monitors[line_].garages[direction].last_dispatched_train = deepcopy(rw.monitors[line_].garages[direction].last_dispatched_train)
#==============================================================================
    
#    fig, ax = plt.subplots(figsize=(20, 10))
#    plt.hist(temp)     

            
#==============================================================================
#             go15.monitors[line_].garages[direction].queue = rw.monitors[line_].garages[direction].queue
#             go15.monitors[line_].garages[direction]._dispatched_train_ids = rw.monitors[line_].garages[direction]._dispatched_train_ids
# #            go15.monitors[line_].garages[direction].Param = rw.monitors[line_].garages[direction].Param
#             go15.monitors[line_].garages[direction].last_dispatched_train = rw.monitors[line_].garages[direction].last_dispatched_train
#==============================================================================
     
        
#    return go15
            
            
        
