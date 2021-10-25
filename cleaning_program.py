import pandas as pd
import numpy as np
import re
import os
import geopandas as gpd
import json
from pytopojson import topology

def my_mkdir(subdir_str):
    """Make a subdirectory if it doesn't exist yet."""
    if not os.path.exists("./{}".format(subdir_str)):
        os.mkdir(subdir_str)

if __name__ == "__main__":
    pass