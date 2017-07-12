# -*- coding: utf-8 -*-
"""
Created on Mon Jul 10 14:43:21 2017

@author: Peyman
"""
from __future__ import division
import numpy as np
import random 
random.seed(123)
from collections import deque, defaultdict
from string import ascii_lowercase, letters 
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import time
import cPickle as pickle
from collections import namedtuple
from os import listdir
from os.path import isfile, join
import logging
import seaborn as sns
from functools import partial
from copy import deepcopy

import shapely
from shapely.ops import transform
from functools import partial
import pyproj

data_path =  "C:/Users/Peyman.n/Dropbox/Research\\projects\\Short_term_forcast\\R code\\data\\"