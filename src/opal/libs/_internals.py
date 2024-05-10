from typeguard import check_type
from typing import Type

class dynamic: pass

class _TypeModes:
    HYBRID, CHECK, FORCE, NONE = 0, 1, 2, 3

class _TypeMode: _REP_ = 0
class hybrid(_TypeMode): _REP_ = _TypeModes.HYBRID
class check(_TypeMode):  _REP_ = _TypeModes.CHECK
class force(_TypeMode):  _REP_ = _TypeModes.FORCE
class none(_TypeMode):   _REP_ = _TypeModes.NONE

def _OPAL_PRINT_RETURN_(val):
    print(val)
    return val

class OpalNamespace:
    def __init__(self):
        raise TypeError("Can't instantiate a namespace")
    
class OpalObject:
    _OPAL_TYPEMODE_ = _TypeModes.HYBRID

def mode(mode: Type[_TypeMode]):
    def fn(cls: OpalObject):
        if mode not in (hybrid, check, force, none):
            raise TypeError(f'Invalid type mode "{mode}"')
        
        cls._OPAL_TYPEMODE_ = mode._REP_
        return cls
    return fn

_AUTOCAST_TYPES = (str, int, float, tuple, list, set, dict, bool, bytes)

def _OPAL_CHECK_TYPE_(value, type_):
    if issubclass(type_, OpalObject):
        match type_._OPAL_TYPEMODE_:
            case 0: pass # hybrid
            case 1: # check
                return check_type(value, type_)
            case 2: # force
                return type_(value)
            case 3: # none
                return value
            case _:
                raise TypeError(f'Invalid type mode "{type_._OPAL_TYPEMODE_}"')

    orig = value
    try:    
        tmp = type_(value)
        if type_ not in _AUTOCAST_TYPES: assert tmp == orig
    except: return check_type(value, type_)
    else:   return tmp 

def _OPAL_FORCE_TYPE_(value, type_):
    return type_(value)