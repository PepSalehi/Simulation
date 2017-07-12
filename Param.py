import cPickle as pickle
from string import letters
import numpy as np


class Param(object):
    '''store all the parameters inside this class
        TODO: currently all travel times are fixed. They should be changed to be stochastic.
        TODO: assign a numeric value to each station; makes it easier to get next/previous stations
    '''

    station_travel_times = pickle.load(
        open("E:/Research/projects/Crowding/central_line_station_travel_times.p", "rb"))

    station_distances = pickle.load(
        open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/station_distances.p", "rb"))

    route_nlcs = pickle.load(
        open("E:/Research/projects/Crowding/route_nlcs.p", "rb"))
    # 18 hours
    SIMULATION_TIME = 18 * 60 * 60
    HEADWAY = 3 * 60  # 3 minutes
    stations = [i for i in route_nlcs]

    # add Garage to 1 travel time (0)
    station_travel_times["garage"][560] = 1

    # create sufficient trains
    max_tt = max(station_travel_times[560].values())

    num_req_trains = int(np.ceil(max_tt / HEADWAY)) + 1  # safety measure
    train_ids = [alp for alp in letters[0:num_req_trains]]
    terminal_station = stations[len(stations) - 1]

    # assign station positions
    station_positions = pickle.load(
        open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/station_loopkup_geom_by_nlc.p", "rb"))

    central_line = pickle.load(
        open("C:/Users/Peyman.n/Dropbox/Research/projects/Crowding/central_line.p", "rb"))
