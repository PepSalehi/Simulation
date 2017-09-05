# -*- coding: utf-8 -*-
"""
Created on Tue Aug 01 14:27:30 2017

@author: Peyman
"""

#==============================================================================
# Plot function 
#==============================================================================
lines = [ "Victoria", "Central"]
directions = {'Central' : ['WE', 'EW'], 'Victoria' :['NS', 'SN']}
for line in lines :
    for direction in directions[line]:
        a_monitor = god_of_15.monitors[line]
        ns = a_monitor.garages[direction]
        param = None
        for p in a_monitor.params:
            if p.direction == direction :
                param = p
                break
        if not param:
            print "STOP THIS MADNESS!"
            print "##############################################"
            print "##############################################"
            print "##############################################"
            print "##############################################"
            print "##############################################"
            print "##############################################"
            break
        start_station = param.stations[0]
        distances = param.station_distances[start_station]
        y_ticks = [distances[p] for p in param.stations[1:]]
        y_ticks.insert(0,0) # for the first station
        y_labels = [param.station_lookup_by_nlc[p] for p in param.stations]
        fig, ax = plt.subplots(figsize=(20, 12))
        
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels)
        
        x1_secs = [datetime.timedelta(seconds=x) for x in range(0, simulation_time + 30 * 60, 900)]
        ax.set_xticks(range(0, simulation_time + 30 * 60, 900))
        #xfmt = md.DateFormatter('%H:%M')
        #ax.xaxis.set_major_formatter(xfmt)
        
        for idx, tr in enumerate(ns._dispatched_train_ids):
            od = OrderedDict(sorted(a_monitor.train_trajectories[tr][direction].items()))
            y1 = np.array(od.values())
            x1 = np.array(od.keys())    
            if idx % 2 == 0:
                plt.plot(x1, y1, 'b')  
            else:
                plt.plot(x1, y1, c = 'r', linewidth=3)
            
            
#==============================================================================
#     
# line = lines[0]
# direction = directions[line][0]
# 
#     
#==============================================================================


fig, ax = plt.subplots(figsize=(20, 10))
plt.hist(history )

#https://stackoverflow.com/questions/15240003/matplotlib-intelligent-axis-labels-for-timedelta
#==============================================================================
# def timeTicks(x, pos):                                                                                                                                                                                                                                                         
#     d = datetime.timedelta(seconds=x)                                                                                                                                                                                                                                          
#     return str(d)                                                                                                                                                                                                                                                              
#     
# formatter = matplotlib.ticker.FuncFormatter(timeTicks)                                                                                                                                                                                                                         
# ax.xaxis.set_major_formatter(formatter)  
#==============================================================================
temps = []
for tr in god_of_15.monitors[line]._trains[direction]:
    if tr.car_id in ns._dispatched_train_ids:
        temps.append(tr)





temps = []
temp = None
j=0
for line_ in ['Central']: # line ex. Central  ['Central', 'Victoria']
    for (n1, train_list_go15)in god_of_15.monitors[line_]._trains.iteritems() : 
        for tr in train_list_go15:
            if tr.is_in_service :
                if min(tr._dist_to_front) < 50 :
                    temps.append(tr)
#                j+=1 
#                if j==2:
#                    temp = tr
#                    print tr._dist_to_front
#                    break
for temp in temps:
    plt.plot(temp._dist_to_back)
    
    plt.plot(temp._dist_to_front)
    












b =  a_monitor.stations[15].platforms['EW']
b._dwell_times
plt.hist(b._dwell_times)


rw_mon_cent = RW_god.monitors['Central']
ds_mon_cent = god_of_15.monitors['Central']
rw_mon_vict = RW_god.monitors['Victoria']
ds_mon_vict = god_of_15.monitors['Victoria']

i=0

for tr in a_monitor._trains[direction]:
    
    if tr.car_id in ns._dispatched_train_ids:
        
        print "current_speed ", tr.current_speed
        print "next_station_id", tr.next_station_id
        print "prev_station_id", tr.prev_station_id
        print "train_in_back", tr.train_in_back
        print "train_in_front", tr.train_in_front        
        print "in service", tr.is_in_service
        print "waiting", tr.waiting
        print "distance_from_garage", tr.distance_from_garage
        print "it_has_reached_a_station", tr.it_has_reached_a_station
        print "##############################"
        if tr.is_in_service:
            i+=1
#            print "prev_station", Param_Central.station_lookup_by_nlc[tr.prev_station_id]
#            print "current_station", Param_Central.station_lookup_by_nlc[tr.next_station_id]   
i






for line_ in god_of_15.monitors.keys(): # line ex. Central
    for (n1, train_list_go15), (n2, train_list_rw) in zip(god_of_15.monitors[line_]._trains.iteritems(), RW_god.monitors[line_]._trains.iteritems()): 
        for tr1, tr2 in zip(train_list_go15, train_list_rw):
            assert tr1.car_id is tr2.car_id
            if tr1.is_in_service :
                print tr1, tr2
                
            
            
            
            
            
            
                    

















