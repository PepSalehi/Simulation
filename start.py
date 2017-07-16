from config import * 
import time
from Param_Central import Param_Central, Param_Central_EW, Param_Central_WE
from Param_Victoria import Param_Victoria, Param_Victoria_NS, Param_Victoria_SN
from CentralMonitor import CentralMonitor
from God import God 
import csv


#def run():
    
#==============================================================================
# This part must be shared between real-life and the decision support simulations
#     
#==============================================================================
start_time = time.time()
simulation_time = Param_Central.SIMULATION_TIME #
simulation_time = 10000
MAX_POSITION = max(Param_Central.station_positions.values())
# central_monitor_instance = CentralMonitor("Central")
# victoria_central_monitor_instance = CentralMonitor("Victoria")
god = God()
god.make_central_monitor("Central")
god.make_central_monitor("Victoria")





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


for t in range(0, int(simulation_time)):

    # produce passengers every 15 minutes. Needed to update demand as new obs. come in every 15 minutes
#    if t % (15*60) == 0:
    if t >= (60 * 60) and t % (15*60) == 0: # give an  an hour warm up
#        t = t - (60*60)
        [station.produce_passsengers(god.monitors["Central"], t_offset=t) 
                             for station in god.monitors["Central"].stations[0:len(god.monitors["Central"].stations)-1]]
        [station.produce_passsengers(god.monitors["Victoria"], t_offset=t) 
                             for station in god.monitors["Victoria"].stations[0:len(god.monitors["Victoria"].stations)-1]]
    #

    # dispatch trains from garage every HEADWAY minutes

    for param in [Param_Victoria_NS, Param_Victoria_SN]:
        if param.should_dispatch():
            direction = param.direction
            god.monitors["Victoria"].garages[direction].dispatch_train(t) 
            
    for param in [Param_Central_EW, Param_Central_WE]:
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
    #

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
#     if t==300 :
#         break
print "DONE"

end_time = time.time()    
csv_file.close()
st_csv_file.close()
victoria_csv_file.close()
victoria_st_csv_file.close()

print( end_time - start_time)/60
    

#run()