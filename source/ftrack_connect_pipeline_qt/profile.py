import cProfile
import os
from os.path import expanduser
home = expanduser("~")

def profileit(func):
    def wrapper(*args, **kwargs):
        datafn = os.path.abspath(os.path.join(home, func.__name__ + ".profile")) # Name the data file sensibly
        prof = cProfile.Profile()
        retval = prof.runcall(func, *args, **kwargs)
        prof.dump_stats(datafn)
        return retval

    return wrapper
