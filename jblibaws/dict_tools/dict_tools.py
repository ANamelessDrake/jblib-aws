import json
from datetime import datetime
from decimal import Decimal

def checkKey(dict, key):
    try:
        if key in dict.keys():
            return True
        else:
            return False
    except:
        return False
   