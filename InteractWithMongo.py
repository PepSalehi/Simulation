import pandas as pd
from pymongo import MongoClient

client = MongoClient()

TfL_live_02 = client['TfL_Live_2017-05-02']

Central_02 = TfL_live_02.central

print(Central_02.find())
