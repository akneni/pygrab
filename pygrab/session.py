import requests as _requests
import threading as _threading
from tor import Tor as _Tor
from warning import Warning as _Warning

class Session(_requests.Session):
    def __init__(self, use_tor=False, **kwargs):
        super().__init__(**kwargs)
        
        if use_tor:
            self.start_tor()
        else:
            self.__use_tor = False

    def start_tor(self):
        if not _Tor.tor_status():
            _Tor.start_tor()
        self.__use_tor = True

    def end_tor(self):
        self.__use_tor = False

    def get(self, url:str, **kwargs):
        self.__append_tor_kwargs(kwargs)
        return super().get(url, **kwargs)
    
    def get_local(self, filename:str, local_read_type:str='r', encoding:str='utf-8')->str:
        if not (isinstance(filename, str)):
            raise TypeError("Argument 'filename' must be a str")
        if not (isinstance(local_read_type, str)):
            raise TypeError("Argument 'local_read_type' must be a str")
        if not (isinstance(encoding, str)):
            raise TypeError("Argument 'encoding' must be a str")
        
        with open(filename, local_read_type, encoding=encoding) as f:
            res = f.read()
        return res

    def head(self, url:str, **kwargs):
        self.__append_tor_kwargs(kwargs)
        return super().head(url, **kwargs)

    def post(self, url:str, data=None, json=None, **kwargs):
        self.__append_tor_kwargs(kwargs)
        return super().post(url, data=data, json=json, **kwargs)

    def put(self, url:str, data=None, **kwargs):
        self.__append_tor_kwargs(kwargs)
        return super().put(url, data=data, **kwargs)

    def patch(self, url:str, data=None, **kwargs):
        self.__append_tor_kwargs(kwargs)
        return super().patch(url, data=data, **kwargs)

    def delete(self, url:str, **kwargs):
        self.__append_tor_kwargs(kwargs)
        return super().delete(url, **kwargs)

    def options(self, url:str, **kwargs):
        self.__append_tor_kwargs(kwargs)
        return super().options(url, **kwargs)

    def __append_tor_kwargs(self, kwargs):
        if self.__use_tor:
            if not _Tor.tor_status():
                _Tor.start_tor()
            # Defaults to user specified proxies and headers over those defined by the tor interface
            if 'proxies' not in kwargs.keys():
                kwargs['proxies'] = _Tor.tor_proxies
            else:
                _Warning.raiseWarning("ProxyWarning: Using specified proxy over Tor Network.")
            
            if 'headers' not in kwargs.keys():
                kwargs['headers'] = _Tor.tor_headers
            else:
                for key, val in _Tor.tor_headers.items():
                    if key not in kwargs['headers']:
                        kwargs['headers'][key] = val