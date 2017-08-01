# -*- coding: utf-8 -*-
"""
Created on Tue Aug 01 14:27:30 2017

@author: Peyman
"""




from collections import OrderedDict
import datetime
import matplotlib.dates as md
import matplotlib  



#==============================================================================
# Plot function 
#==============================================================================
line = 'Victoria'
direction = 'SN'
a_monitor = DS_god.monitors[line]
ns = a_monitor.garages[direction]
param = None
for p in a_monitor.params:
    if p.direction == direction :
        param = p
        break
if not param:
    print "STOP THIS MADNESS!"
    

start_station = param.stations[0]
distances = param.station_distances[start_station]


y_ticks = [distances[p] for p in param.stations[1:]]
y_ticks.insert(0,0) # for the first station
y_labels = [param.station_lookup_by_nlc[p] for p in param.stations]
fig, ax = plt.subplots(figsize=(20, 15))

ax.set_yticks(y_ticks)
ax.set_yticklabels(y_labels)

x1_secs = [datetime.timedelta(seconds=x) for x in range(0, first_iterations_simulation_time + 900, 900)]
ax.set_xticks(range(0, first_iterations_simulation_time + 900, 900))
#xfmt = md.DateFormatter('%H:%M')
#ax.xaxis.set_major_formatter(xfmt)

for idx, tr in enumerate(ns._dispatched_train_ids):
    od = OrderedDict(sorted(a_monitor.train_trajectories[tr][direction].items()))
    y1 = np.array(od.values())
    x1 = np.array(od.keys())    
    if idx % 2 == 0:
        plt.plot(x1, y1, 'b')  
    else:
        plt.plot(x1, y1, 'r-')
    


#https://stackoverflow.com/questions/15240003/matplotlib-intelligent-axis-labels-for-timedelta
#==============================================================================
# def timeTicks(x, pos):                                                                                                                                                                                                                                                         
#     d = datetime.timedelta(seconds=x)                                                                                                                                                                                                                                          
#     return str(d)                                                                                                                                                                                                                                                              
#     
# formatter = matplotlib.ticker.FuncFormatter(timeTicks)                                                                                                                                                                                                                         
# ax.xaxis.set_major_formatter(formatter)  
#==============================================================================





