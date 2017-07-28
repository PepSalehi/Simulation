# -*- coding: utf-8 -*-
"""
Created on Fri Jul 21 13:39:48 2017

@author: Peyman
"""

print "#############################################"
print "Start the second iteration "
csv_file =  open("C:\\Users\\Peyman.n\\Documents\\Viz_of_simulation-victoriaAndcentral\\static\\csv/trains_states.csv", 'ab') 
csv_writer = csv.writer(csv_file)  
csv_writer.writerow(('t', 'car_id', 'position', 'load', 'load_history_array', "next_station_id"))

st_csv_file =  open("C:\\Users\\Peyman.n\\Documents\\Viz_of_simulation-victoriaAndcentral\\static\\csv\\stations_states.csv", 'ab') 
st_csv_writer = csv.writer(st_csv_file)  
st_csv_writer.writerow(('t', 'station_id', 'platform', 'queue', 'hist_queue_array'))

victoria_csv_file =  open("C:\\Users\\Peyman.n\\Documents\\Viz_of_simulation-victoriaAndcentral\\static\\csv/trains_states_victoria.csv", 'ab') 
victoria_csv_writer = csv.writer(victoria_csv_file)  
victoria_csv_writer.writerow(('t', 'car_id', 'position', 'load', 'load_history_array', "next_station_id"))

victoria_st_csv_file =  open("C:\\Users\\Peyman.n\\Documents\\Viz_of_simulation-victoriaAndcentral\\static\\csv\\stations_states_victoria.csv", 'ab') 
victoria_st_csv_writer = csv.writer(victoria_st_csv_file)  
victoria_st_csv_writer.writerow(('t', 'station_id', 'platform', 'queue', 'hist_queue_array'))

DS_god_second_iterations = run_simulation(simulation_time, the_god, csv_file, st_csv_file,
                                          victoria_csv_file, victoria_st_csv_file, update_interval,
                                          prev_god=DS_god, act_dumb = False )
print "#############################################"


