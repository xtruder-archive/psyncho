import stat

class Enumerate(object):
    def __init__(self, names):
        for number, name in enumerate(names.split()):
            setattr(self, name, number)
            
def is_file(info):
    return stat.S_ISREG( info["st_mode"] )

def is_dir(info):
    return stat.S_ISDIR( info["st_mode"] )

def is_lnk(info):
    return stat.S_ISLNK( info["st_mode"] )

def get_fmod(info):
    return info["st_mode"] & 0x00000FFF