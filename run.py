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
update_interval = 30
btw_simulation_gap = 1000 # 20 mins shorter simulation time for the second iteration
first_iterations_simulation_time = simulation_time + 2 * btw_simulation_gap
second_iterations_simulation_time = simulation_time + 1 * btw_simulation_gap
third_iterations_simulation_time = simulation_time
#==============================================================================
# This part must be shared between real-life and the decision support simulations
#     
#==============================================================================
# central_monitor_instance = CentralMonitor("Centsral")
# victoria_central_monitor_instance = CentralMonitor("Victoria")
the_god = God()
the_god.make_central_monitor("Central")
the_god.make_central_monitor("Victoria")   
#==============================================================================
# god.distribute_trains("Central")
# god.distribute_trains("Victoria")
#==============================================================================

# central_monitor_instance.distribute_trains()

csv_file =  open("C:\\Users\\Peyman.n\\Documents\\Viz_of_simulation-victoriaAndcentral\\static\\csv/trains_states.csv", 'wb') 
csv_writer = csv.writer(csv_file)  
csv_writer.writerow(('t', 'car_id', 'position', 'load', 'load_history_array', "next_station_id"))

st_csv_file =  open("C:\\Users\\Peyman.n\\Documents\\Viz_of_simulation-victoriaAndcentral\\static\\csv\\stations_states.csv", 'wb') 
st_csv_writer = csv.writer(st_csv_file)  
st_csv_writer.writerow(('t', 'station_id', 'platform', 'queue', 'hist_queue_array'))

victoria_csv_file =  open("C:\\Users\\Peyman.n\\Documents\\Viz_of_simulation-victoriaAndcentral\\static\\csv/trains_states_victoria.csv", 'wb') 
victoria_csv_writer = csv.writer(victoria_csv_file)  
victoria_csv_writer.writerow(('t', 'car_id', 'position', 'load', 'load_history_array', "next_station_id"))

victoria_st_csv_file =  open("C:\\Users\\Peyman.n\\Documents\\Viz_of_simulation-victoriaAndcentral\\static\\csv\\stations_states_victoria.csv", 'wb') 
victoria_st_csv_writer = csv.writer(victoria_st_csv_file)  
victoria_st_csv_writer.writerow(('t', 'station_id', 'platform', 'queue', 'hist_queue_array'))

#==============================================================================
# Simulation specific
#==============================================================================

def run_simulation(simulation_time, god_template, csv_file, st_csv_file, victoria_csv_file, 
                   victoria_st_csv_file, update_interval, prev_god = None, act_dumb= True, DEMAND_LEVEL="O",
                   param_central_EW= None, param_central_WE= None, param_victoria_NS= None, param_victoria_SN = None):
                       
    # initialize timers/headways
    if param_central_EW is None:
        param_central_EW = Param_Central_EW()                       
        param_central_WE = Param_Central_WE()  
        param_victoria_NS = Param_Victoria_NS() 
        param_victoria_SN = Param_Victoria_SN()                   
                       
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
            
            for n2, train_list in this_god.monitors[name]._trains.iteritems():    
                this_god_trains = [train.car_id for train in train_list ]
            for n2, train_list in this_god.monitors[name]._trains.iteritems():  
                prev_god_trains = [train.car_id for train in train_list ]
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
        
        
        
    the_file = open('train_log.txt', 'wb') 
    the_file_writer = csv.writer(the_file)
    for t in range(0, int(simulation_time)):
    
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
                
    #==============================================================================
    #         if t % (Param_Central.HEADWAY ) == 0:
    #             for name, garage in god.monitors["Central"].garages.iteritems():
    #                 garage.dispatch_train(t)   
    #                 
    #         if t % (Param_Victoria.HEADWAY ) == 0:
    #             for name, garage in god.monitors["Victoria"].garages.iteritems():
    #                 garage.dispatch_train(t)   
    #==============================================================================
    
        # update train positions every minute
    #     if t % (60) == 0 and t > 0:
    #         for train in CentralMonitor.trains:
    #             old = train.position
    #             new_pos = old + int(random.normalvariate(1*30,30))
    #             while new_pos <= 0 or new_pos > MAX_POSITION:
    #                 new_pos = old + int(random.normalvariate(1*30,30))
    #             train.update_position_load(t, new_pos)
    
    #     if (t% 1001) == 0 :
    #         if t != 0:
    #             print t
    #             break
        
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
        
        
        if t % update_interval == 0:
            # Central
            for _, train_list in god.monitors["Central"]._trains.iteritems():
                for train in train_list:
                    train.save_state_for_other_iterations()
            # Victoria
            for _, train_list in god.monitors["Victoria"]._trains.iteritems():
                for train in train_list:
                    train.save_state_for_other_iterations()
                    
                    
                    
            ############################ debugging
            for _, train_list in god.monitors["Central"]._trains.iteritems():
                tr = train_list[0]
                break
            if tr.is_in_service :
                if not tr.waiting:
#                    print t, tr.car_id, tr.distance_from_garage, tr.distance_to_train_in_back 
                    the_file_writer.writerow([tr.car_id, tr.distance_from_garage, tr.distance_to_train_in_back  ])
                else:
#                    print "Waiting"
                    the_file_writer.writerow(["Waiting"])
        
            ###########################       

            
            
        if t % (60 ) == 0:
            # write state to file
            # Central
            for _, train_list in god.monitors["Central"]._trains.iteritems():
                for train in train_list:
                    train.save_state(t, csv_writer)
            for station in god.monitors["Central"].stations:
                station.save_state(t, st_csv_writer)
                
            # write state to file
            # Victoria 
            for _, train_list in god.monitors["Victoria"]._trains.iteritems():
                for train in train_list:
                    train.save_state(t, victoria_csv_writer)
            for station in god.monitors["Victoria"].stations:
                station.save_state(t, victoria_st_csv_writer)
        
    
    print "DONE"
    # clean_up 
    # Very important, otherwise dispatching is gonna be messed up for the other simulation
    # but this is not the correct approach in general, because when this wants to continue, it
    # has to remember where it was
#    for param in [Param_Victoria_NS, Param_Victoria_SN, Param_Central_EW, Param_Central_WE]:
#        param.timer = 0
        
    end_time = time.time()    
    csv_file.close()
    st_csv_file.close()
    victoria_csv_file.close()
    victoria_st_csv_file.close()
    
    print (end_time - start_time)/60
    
    return(god, param_victoria_NS, param_victoria_SN, param_central_EW, param_central_WE)
    
#==============================================================================
# 
#==============================================================================
DS_god, param_victoria_NS, param_victoria_SN, param_central_EW, param_central_WE = run_simulation(first_iterations_simulation_time, the_god, csv_file, st_csv_file, victoria_csv_file, victoria_st_csv_file, update_interval )

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
