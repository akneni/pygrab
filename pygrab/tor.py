import subprocess as _subprocess
import os as _os
import atexit as _atexit
import signal as _signal
import tarfile as _tarfile
from pathlib import Path as _Path
import platform as _platform
from .exceptions import *

class Tor():
    __tor_service_enabled = False
    __tor_path = None
    __tor_process = None
    __override_service_err = False
    __os = _platform.system()
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
    def start_tor(cls, verbose:int=0, force_start=False):
        if cls.__tor_service_enabled:
            cls.end_tor()

        cls.__tor_path_init()

        if cls.__os == 'Windows':
            if 'tor' not in _os.listdir(cls.__tor_path) or 'tor.exe' not in _os.listdir(_os.path.join(cls.__tor_path, './tor')):
                error_msg = "It seems like you're missing the tor.exe dependency. You can download it from 'https://www.torproject.org/download/tor/'.\n"
                error_msg += "Then call pygrab.Tor.load_tor_dependencies(./path/to/tor-something-or-the-other.tar.gz)"
                print(f'FileNotFoundError: {error_msg}\n')
                dependency_filepath = input('OR, enter the file path here: ').strip(" '\"\n")
                if not _os.path.isfile(dependency_filepath):
                    raise Exception("Invalid filepath")
                else:
                    cls.load_tor_dependencies(dependency_filepath)
                    print("Sucessfully loaded tor dependencies\nStarting tor service...")
        elif cls.__os == 'Linux':
            if not cls.__tor_installed_linux():
                raise DependencyLoadError("It seems like you're missing the tor dependency. Please run `sudo apt-get install tor` to download dependencies.")
        
        if cls.__os == 'Windows':
            cls.__tor_process = _subprocess.Popen(
                [_os.path.join(cls.__tor_path, './tor/tor.exe')], 
                stdout=_subprocess.PIPE, 
                stderr=_subprocess.STDOUT, 
                text=True
            )
        else:
            cls.__tor_process = _subprocess.Popen(
                ['tor', '/tor'], 
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
            elif "Could not bind to 127.0.0.1:9050" in line:
                cls.__override_service_err = (force_start or cls.__override_service_err)
                if cls.__override_service_err:
                    cls.__tor_service_enabled = True
                    break
                err_msg = "A service is already running on 127.0.0.1:9050. Do you already have an instance of Tor Running?\n"
                err_msg += "If another instance of tor is running, you can run pygrab.Tor.start_tor(force_start=True) to override this error."
                raise ResourceWarning (err_msg)


    @classmethod
    def end_tor(cls):
        if cls.__tor_process is not None:
            cls.__tor_process.terminate()
            cls.__tor_process.wait()
            cls.__tor_service_enabled = False

    @classmethod
    def tor_status(cls) -> bool:
        return cls.__tor_service_enabled
    
    @classmethod
    def override_status(cls) -> bool:
        return cls.__override_service_err
    
    @classmethod
    def load_tor_dependencies(cls, filepath:str):
        if cls.__os == 'Linux':
            raise DependencyLoadError(" If you're on linux, run `sudo apt-get` ")

        cls.__tor_path_init()        
        if filepath.endswith('.tar.gz'):
            with _tarfile.open(filepath, 'r:gz') as tar:
                tar.extractall(path=cls.__tor_path)
            return
        elif filepath.endswith('tor.exe'):
            if 'tor' not in _os.listdir(cls.__tor_path):
                _os.mkdir(_os.path.join(cls.__tor_path, "./tor"))
            with open(filepath, 'rb') as f:
                data = f.read()
            with open (_os.path.join(cls.__tor_path, "./tor/tor.exe"), 'wb') as f:
                f.write(data)
            return
        raise AttributeError("load_tor_dependencies only supports file types of '.tar.gz' and 'tor.exe'")

    @classmethod
    def __tor_path_init(cls):
        if cls.__tor_path is None:
            tor_path = _Path(_os.path.dirname(_os.path.realpath(__file__)))
            if "tor-dependencies" not in _os.listdir(tor_path):
                _os.mkdir(_os.path.join(tor_path, "./tor-dependencies"))
            cls.__tor_path = _os.path.join(tor_path, "./tor-dependencies")

    @classmethod
    def __tor_installed_linux(cls):
        try:
            result = _subprocess.run(['tor', '--version'], stdout=_subprocess.PIPE, stderr=_subprocess.PIPE)
            if result.returncode == 0:
                return True
        except FileNotFoundError:
            pass
        return False

    @classmethod
    def __signal_handler(cls, signum, frame):
        cls.end_tor()
        exit(1)
