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
    __num_req = {'curr_req': None, 'max_req': None}
    __os = _platform.system()

    # socks proxies for tor
    tor_proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }

    @classmethod
    def start_tor(cls, verbose:int=0, force_start=None) -> None:
        if force_start is None and cls.__os == 'Windows':
            force_start = False
        elif force_start is None and cls.__os == 'Linux':
            force_start = True
        else:
            raise NotImplemented(f'Tor functionality not yet implemented for {cls.__os}')
    
        if cls.__tor_service_enabled:
            cls.end_tor()

        cls.__tor_path_init()

        if cls.__os == 'Windows':# Check if tor dependencies are installed for windows
            if 'tor' not in _os.listdir(cls.__tor_path) or 'tor.exe' not in _os.listdir(_os.path.join(cls.__tor_path, './tor')):
                error_msg = "It seems like you're missing the tor.exe dependency. You can download it from 'https://www.torproject.org/download/tor/'.\n"
                error_msg += "Then call pygrab.Tor.load_tor_dependencies(./path/to/tor-something-or-the-other.tar.gz)"
                print(f'FileNotFoundError: {error_msg}\n')
                dependency_filepath = input('OR, enter the file path here: ').strip(" '\"\n")
                if not _os.path.isfile(dependency_filepath):
                    raise Exception("Invalid filepath")
                else:
                    cls.load_tor_dependencies(dependency_filepath)
                    print("Successfully loaded tor dependencies\nStarting tor service...")
        elif cls.__os == 'Linux':
            # Check if tor dependencies are installed for linux
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

        # Set the tor service to me terminated on program exit
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
    def end_tor(cls) -> None:
        if cls.__tor_process is not None:
            cls.__tor_process.terminate()
            cls.__tor_process.wait()
            cls.__tor_service_enabled = False
        cls.__num_req = {'curr_req': None, 'max_req': None}

    @classmethod
    def tor_status(cls) -> bool:
        return cls.__tor_service_enabled
    
    @classmethod
    def override_status(cls) -> bool:
        return cls.__override_service_err
    
    @classmethod
    def load_tor_dependencies(cls, filepath: str) -> None:
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
    def increment_rotation_counter(cls, num_req: int = 1) -> None:
        if cls.__num_req['max_req'] is None: return
        cls.__num_req['curr_req'] += num_req
        if cls.__num_req['curr_req'] >= cls.__num_req['max_req']:
            cls.start_tor()
            cls.__num_req['curr_req'] = 0

    @classmethod
    def rotate_tor(cls, num_req_per_rotation: int) -> None:
        if cls.__override_service_err:
            raise Exception("Cannot rotate tor connections when an override is forced. End the other tor service in order to rotate connections.")
        if not cls.__tor_service_enabled:
            cls.start_tor()
        if num_req_per_rotation < 1:
            raise ValueError("`num_req_per_rotation` must be positive")
        cls.__num_req = {'curr_req': 0, 'max_req': num_req_per_rotation}

    @classmethod
    def end_tor_rotation(cls) -> None:
        cls.__num_req = {'curr_req': None, 'max_req': None}

    @classmethod
    def __tor_path_init(cls):
        if cls.__tor_path is None:
            tor_path = _Path(_os.path.dirname(_os.path.realpath(__file__)))
            if "tor-dependencies" not in _os.listdir(tor_path):
                _os.mkdir(_os.path.join(tor_path, "./tor-dependencies"))
            cls.__tor_path = _os.path.join(tor_path, "./tor-dependencies")

    @classmethod
    def __tor_installed_linux(cls):
        # Determine if tor service is installed for linux
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
