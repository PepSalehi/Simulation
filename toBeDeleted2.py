# -*- coding: utf-8 -*-
"""
Created on Fri Jul 21 17:14:54 2017

@author: Peyman
"""


                       
start_time = time.time()
# since we need to keep the original god intact, as the other simulation should use the same one for initialization
god = deepcopy(the_god)

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
                
                
for param in [Param_Victoria_NS, Param_Victoria_SN, Param_Central_EW, Param_Central_WE]:
        param.timer = 0  
prev_god = DS_god

if prev_god:
    read_train_colors_from_god(god, prev_god)
    
for t in range(0, int(simulation_time)):
    if t >= (60 * 60) and t % (15*60) == 0:
        [station.produce_passsengers(god.monitors["Central"], act_dumb = True, t_offset=t ) 
                             for station in god.monitors["Central"].stations[0:len(god.monitors["Central"].stations)-1]]
        [station.produce_passsengers(god.monitors["Victoria"], act_dumb=True, t_offset=t ) 
                             for station in god.monitors["Victoria"].stations[0:len(god.monitors["Victoria"].stations)-1]]

    for param in [Param_Victoria_NS, Param_Victoria_SN]:
        if param.should_dispatch():
            direction = param.direction
            god.monitors["Victoria"].garages[direction].dispatch_train(t)      
    for param in [Param_Central_EW, Param_Central_WE]:
        if param.should_dispatch():
            direction = param.direction
            god.monitors["Central"].garages[direction].dispatch_train(t)
    for station in god.monitors["Central"].stations:
        station.update(t) 
    for station in god.monitors["Victoria"].stations:
        station.update(t)
    for _, train_list in god.monitors["Central"]._trains.iteritems():
        for train in train_list:
            train.update(god.monitors["Central"], t, god)
    for _, train_list in god.monitors["Victoria"]._trains.iteritems():
        for train in train_list:
            train.update(god.monitors["Victoria"], t, god)

print "DONE"

end_time = time.time()    
csv_file.close()
st_csv_file.close()
victoria_csv_file.close()
victoria_st_csv_file.close()

print (end_time - start_time)/60

