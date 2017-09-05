# -*- coding: utf-8 -*-
"""
Created on Mon Jul 10 14:07:25 2017

@author: Peyman
"""
from collections import defaultdict
from __future__ import division

rw_mon_cent = RW_god.monitors['Central']
ds_mon_cent = god_of_15.monitors['Central']
rw_mon_vict = RW_god.monitors['Victoria']
ds_mon_vict = god_of_15.monitors['Victoria']



len(rw_mon_vict.garages['NS'].queue)
len(ds_mon_vict.garages['NS'].queue)

len(rw_mon_vict.garages['SN'].queue)
len(ds_mon_vict.garages['SN'].queue)

len(rw_mon_cent.garages['EW'].queue)
len(ds_mon_cent.garages['EW'].queue)

len(rw_mon_cent.garages['WE'].queue)
len(ds_mon_cent.garages['WE'].queue)
#==============================================================================
# Trains
#==============================================================================
#tr_ew = ds_mon_cent._trains['EW']
tr_ew = rw_mon_cent._trains['EW']
tr = tr_ew[10]
plt.figure(figsize=(10,10))
#path = np.array(tr._load_history['H'])
path_O = np.array(tr._load_history['O'])
plt.plot(path_O, label = tr.car_id)

#==============================================================================
# Stations
#==============================================================================
plt.figure(figsize=(10,10))
st1 = ds_mon_cent.stations[8] # blue 
st2 = rw_mon_cent.stations[8] # green 

pl1 = st1.platforms['WE']
pl2 = st2.platforms['WE']
# crowding level
path_O = np.array(pl1.hist_queue['do'])
path_O
plt.plot(path_O, color = "blue")
path_O = np.array(pl2.hist_queue['do'])
path_O
plt.plot(path_O, color = "green")
#==============================================================================


len(ds_mon_cent.all_passengers_created_observed) / len(rw_mon_cent.all_passengers_created_observed)
 
len(ds_mon_vict.all_passengers_created_observed) / len(rw_mon_vict.all_passengers_created_observed)




a = Param_Victoria_NS()
sum((np.cumsum(a.headways) < 17200))

a = Param_Victoria_SN()
sum((np.cumsum(a.headways) < 16200))


len(ds_mon_cent._trains["EW"])

len(ds_mon_vict._trains["NS"])
# since there are less trains in the garages of 1 direction, it must have been coming from the other depot


a = ds_mon_vict.garages['SN']
a_rw = rw_mon_vict.garages['SN']
len(a._dispatched_train_ids)
len(a_rw._dispatched_train_ids)




b_id = a._dispatched_train_ids[107]


bnext_id = a._dispatched_train_ids[121]  # 3, 6, etc. 116

for tr in ds_mon_vict._trains["NS"]:
    if tr.car_id == bnext_id:
        print "found"
        break
for tr_rw in rw_mon_vict._trains["NS"]:
    if tr_rw.car_id == bnext_id:
        print "found"
        break    

tr_rw._dispatch_times
tr._dispatch_times

    
tr_rw._next_stations_debugging
tr._next_stations_debugging


Param_Victoria_SN.stations[1:]

Param_Victoria_SN.stations





tr._speeds_debugging


[tr.car_id for tr in rw_mon_vict.garages['NS'].queue]

[tr.car_id for tr in ds_mon_vict.garages['NS'].queue]



tr.car_id
tr1.car_id


tr.









# denied boarding 

len(rw_mon_cent.passenger_denied_boarding ['O']) # 686
len(rw_mon_cent.passenger_denied_boarding_out_of_choice['O'])

len(ds_mon_cent.passenger_denied_boarding ['P']) #6457
len(ds_mon_cent.passenger_denied_boarding_out_of_choice['P'])
#
len(rw_mon_vict.passenger_denied_boarding ['O'])
len(rw_mon_vict.passenger_denied_boarding_out_of_choice['O'])

len(ds_mon_vict.passenger_denied_boarding ['P']) #3684
len(ds_mon_vict.passenger_denied_boarding_out_of_choice['P'])







# Bank : 513
# Liverpool : 634
# Bond : 524

# victoria : 741
# Oxford : 669
# Warren : 745

#==============================================================================

def return_platforms (monitor, station_id, central=True):
    found = False
    for st in monitor.stations:
        if st.ids == station_id:
            found = True
            break
    if found :
        if central:
            pl1 = st.platforms['WE']
            pl2 = st.platforms['EW']
            
            return (pl1, pl2 )
        else:
            pl1 = st.platforms['NS']
            pl2 = st.platforms['SN']
            
            return (pl1, pl2 )
    else:
        print "station not found"
        
#==============================================================================
        
        
pl1, pl2 = return_platforms(rw_mon_cent, 769)
ds_pl1, ds_pl2 = return_platforms(ds_mon_cent, 513)

pl1.hist_queue['t']
ds_pl1.hist_queue['t']

np.diff(pl1.hist_queue['t'])
np.diff(ds_pl1.hist_queue['t'])
#==============================================================================

def return_platform_loads(monitor, station_id, central=True, level = 'do'):
    found = False
    for st in monitor.stations:
        if st.ids == station_id:
            found = True
            break
    if found :
        if central:
            pl1 = st.platforms['WE']
            pl2 = st.platforms['EW']
            
            return (pl1.hist_queue[level], pl2.hist_queue[level] )
        else:
            pl1 = st.platforms['NS']
            pl2 = st.platforms['SN']
            
            return (pl1.hist_queue[level], pl2.hist_queue[level] )
    else:
        print "station not found"
#==============================================================================

pl1, pl2 = return_platform_loads(rw_mon_cent, 513)     
ds_pl1, ds_pl2 = return_platform_loads(ds_mon_cent, 513, level = 'dh')










rw_mon_cent.passenger_denied_boarding ['O'][0][0]


            
    