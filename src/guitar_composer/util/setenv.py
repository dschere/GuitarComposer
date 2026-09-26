import ctypes
import sys
import os

def setenv(name, value):
    """
    Call the standard C library setenv (except for windows) 
    """
    if sys.platform.startswith('win'):
        # On Windows, the C library function is usually '_putenv_s'
        libc = ctypes.cdll.msvcrt
        
        # Windows _putenv_s doesn't use an overwrite flag, it always overwrites
        # Returns 0 on success
        libc._putenv_s(name.encode('utf-8'), value.encode('utf-8'))
    else:
        # On Linux and macOS, load standard libc
        libc = ctypes.CDLL(None)
        
        # Explicitly define argument types for safety
        libc.setenv.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
        libc.setenv.restype = ctypes.c_int
        libc.setenv(name.encode('utf-8'), value.encode('utf-8'), ctypes.c_int(1))
    os.environ[name] = value    
