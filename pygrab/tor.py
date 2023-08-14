import subprocess as _subprocess
import os as _os
import atexit as _atexit
import signal as _signal
import tarfile as _tarfile
from pathlib import Path as _Path

class Tor():
    __tor_service_enabled = False
    __tor_path = None
    __tor_process = None
    tor_proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    tor_headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': 'https://www.google.com',
    }

    @classmethod
    def start_tor(cls, verbose:int=0):
        if cls.__tor_service_enabled:
            cls.end_tor()

        if cls.__tor_path is None:
            tor_path = _Path(_os.path.dirname(_os.path.realpath(__file__)))
            if "./tor-dependencies" not in _os.listdir(tor_path):
                _os.mkdir(_os.path.join(tor_path, "./tor-dependencies"))
            cls.__tor_path = _os.path.join(tor_path, "./tor-dependencies")

        if 'tor' not in _os.listdir(cls.__tor_path):
            error_msg = "It seems like you're missing the tor.exe dependency. You can download it from 'https://www.torproject.org/download/tor/'.\n"
            error_msg += "Then call pygrab.Tor.load_tor_dependencies(./path/to/tor-something-something.tar.gz)"
            raise FileNotFoundError (error_msg)
        elif 'tor.exe' not in _os.listdir(_os.path.join(cls.__tor_path, './tor')):
            error_msg = "It seems like you're missing the tor.exe dependency. You can download it from 'https://www.torproject.org/download/tor/'.\n"
            error_msg += "Then call pygrab.Tor.load_tor_dependencies(./path/to/tor-something-something.tar.gz)"
            raise FileNotFoundError (error_msg)
        
        cls.__tor_process = _subprocess.Popen(
            [_os.path.join(cls.__tor_path, './tor/tor.exe')], 
            stdout=_subprocess.PIPE, 
            stderr=_subprocess.STDOUT, 
            text=True
        )

        _atexit.register(cls.end_tor)
        _signal.signal(_signal.SIGTERM, cls.__signal_handler)

        # Read the output line by line
        for line in iter(cls.__tor_process.stdout.readline, ''):
            if verbose >= 1: print(line.strip())
            if "Bootstrapped100%".lower() in line.replace(' ', '').lower():
                if verbose >=1 : print("Connected to Tor Service\n")
                cls.__tor_service_enabled = True
                break


    @classmethod
    def end_tor(cls):
        if cls.__tor_process is not None:
            cls.__tor_process.terminate()
            cls.__tor_process.wait()
            cls.__tor_service_enabled = False

    @classmethod
    def get_status(cls) -> bool:
        return cls.__tor_service_enabled
    
    @classmethod
    def load_tor_dependencies(cls, filepath:str):
        if cls.__tor_path is None:
            tor_path = _Path(_os.path.dirname(_os.path.realpath(__file__)))
            if "./tor-dependencies" not in _os.listdir(tor_path):
                _os.mkdir(_os.path.join(tor_path, "./tor-dependencies"))
            cls.__tor_path = _os.path.join(tor_path, "./tor-dependencies")
        
        if filepath.endswith('.tar.gz'):
            with _tarfile.open(filepath, 'r:gz') as tar:
                tar.extractall(path=cls.__tor_path)
        elif filepath.endswith('tor.exe'):
            if 'tor' not in _os.listdir(cls.__tor_path):
                _os.mkdir(_os.path.join(cls.__tor_path, "./tor"))
            with open(filepath, 'rb') as f:
                data = f.read()
            with open (_os.path.join(cls.__tor_path, "./tor/tor.exe"), 'wb') as f:
                f.write(data)

    @classmethod
    def __signal_handler(cls, signum, frame):
        cls.end_tor()
        exit(1)