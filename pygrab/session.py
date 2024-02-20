from .warning import Warning as _Warning
from .tor import Tor as _Tor
from .js_scraper import js_scraper as _js_scraper
import requests as _requests
import threading as _threading
import time as _time

class Session(_requests.Session):
    def __init__(self, use_tor:bool=None, **kwargs):
        super().__init__(**kwargs)
        
        if use_tor is None:
            self.__use_tor = _Tor.tor_status()
        else:
            if (not isinstance(use_tor, bool)): raise Exception("argument 'use_tor' must be a boolean.")
            if use_tor: self.start_tor()
            self.__use_tor = use_tor

    def start_tor(self):
        if not _Tor.tor_status():
            _Tor.start_tor()
        self.__use_tor = True

    def end_tor(self):
        self.__use_tor = False

    def get(self, url:str, enable_js=False, timeout=5, **kwargs):
        if enable_js:
            res = _js_scraper.pyppeteer_get(url, self.__use_tor)
            return self.__responseify_html(res)
        else:
            self.__append_tor_kwargs(kwargs)
            return super().get(url, timeout=timeout, **kwargs)
    
    def get_async(self, urls, enable_js=False, thread_limit:int=None, time_rest:float=0, **kwargs) -> dict:
        if (isinstance(urls, (str, int, float, bool))):
            raise TypeError("Argument 'urls' must be an iterable object")
        elif not (isinstance(enable_js, bool)):
            raise TypeError("Argument 'enable_js' must be a bool")
        elif not (isinstance(time_rest, int) or isinstance(time_rest, float)):
            raise TypeError("Argument 'time_rest' must be a int or float")
        elif not (isinstance(thread_limit, int) or thread_limit is None):
            raise TypeError("Argument 'thread_limit' must be a int")

        if thread_limit is None:
            thread_limit = 30 if enable_js else 800

        # remove repeats to prevent possible DoS attacks
        urls = list(set(urls))

        # Handle async js enabled scraping
        if enable_js:
            res = {}
            for thread_counter in range (0, len(urls), thread_limit):
                curr_urls = urls[thread_counter:thread_counter+thread_limit]
                if enable_js:
                    htmls:dict = _js_scraper.pyppeteer_get_async(curr_urls, self.__use_tor)
                    res.update( {k:self.__responseify_html(v) for k,v in htmls.items()} )
            return res

        result = {}
        thread_counter = 0
        while thread_counter < len(urls):
            sub_urls = urls[thread_counter:thread_counter+thread_limit]
            threads = []
            for url in sub_urls:
                threads.append(_threading.Thread(target=self.__grab_thread_wrapper, args=[url, result, kwargs]))
                threads[-1].start()
                _time.sleep(time_rest)
            
            for thread in threads:
                thread.join()
            thread_counter += thread_limit
        return result

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

    def post_local(self, filepath:str, data:str, local_save_type:str="w", encoding:str='utf-8') -> None:
        """
        Writes data to a local file.

        This function is used to write or append data to a local file. It can be used in various scenarios such as saving request data, logging, or other local storage needs.

        Parameters:
            filepath (str): The path to the file where the data will be written. If the file does not exist, it will be created.
            data (str): The data that will be written to the file.
            local_save_type (str, optional): The mode in which the file is opened. Defaults to 'w' (write mode), and can also be set to 'a' (append mode) or any other valid file mode.
            encoding (str, optional): The encoding to be used when opening the file. Defaults to 'utf-8'.

        Returns:
            None
        """
        with open(filepath, local_save_type, encoding=encoding) as f:
            f.write(str(data))

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
    
    def download(self, url: str, local_filename:str=None) -> None:
        if not (isinstance(url, str)):
            raise TypeError("Argument 'url' must be a str")
        elif not (isinstance(local_filename, str) or local_filename is None):
            raise TypeError("Argument 'local_filename' must be a str")
        
        if local_filename is not None:
            if '.' not in local_filename:
                raise ValueError("Argument 'local_filename' must have file extension.")
        elif '/' in url:
            local_filename = url.split('/')[-1]
        else:
            local_filename=url

        # sends a request to get the file contents
        response = self.get(url)

        if response.status_code == 200:
            with open(local_filename, 'wb') as f:
                f.write(response.content)
        else:
            raise Exception(f"Error fetching url. Status code - {response.status_code}")

    def download_async(self, urls:list, local_filenames:list=None, thread_limit=500, time_rest=0) -> None:
        # Check argument types
        if (isinstance(urls, (str, int, float, bool))):
            raise TypeError("Argument 'urls' must be an iterable object")
        elif (isinstance(local_filenames, (str, int, float, bool)) or local_filenames is None):
            raise TypeError("Argument 'local_filename' must be an iterable object")
        elif not (isinstance(time_rest, int) or isinstance(time_rest, float)):
            raise TypeError("Argument 'time_rest' must be a int or float")

        # remove repeats to prevent possible DoS attacks
        urls = list(set(urls))
        local_filenames = list(set(local_filenames))

        if local_filenames is not None:
            if len(urls) != len(local_filenames):
                raise ValueError("Lists 'url' and 'local_filenames' must be of equal length.")
        else:
            local_filenames = [None for _ in range(len(urls))]

        # Uses the threading module to asynchronously download the files
        thread_counter = 0
        while (thread_counter < len(urls)):
            threads = []
            sub_urls = urls[thread_counter:thread_counter+thread_limit]
            sub_local_filename= local_filenames[thread_counter:thread_counter+thread_limit]

            for url, name in zip(sub_urls, sub_local_filename):
                threads.append(_threading.Thread(target=self.download, args=[url, name]))
                threads[-1].start()
                _time.sleep(time_rest)
            
            for thread in threads:
                thread.join()
            thread_counter += thread_limit

    def tor_status(self) -> bool:
        return self.__use_tor
    
    def display_tor_status(self) -> None:
        connection_data = self.get('http://ip-api.com/json').json()
        print("Tor Service Enabled:  ", self.__use_tor)
        print("Public Ip Address:    ", connection_data['query'])
        if 'country' in connection_data.keys():
            print("Country:              ", connection_data['country'])
        if 'regionName' in connection_data.keys():
            print("Region:               ", connection_data['regionName'])
        if 'city' in connection_data.keys():
            print("City:                 ", connection_data['city'])
    
    def __append_tor_kwargs(self, kwargs):
        if self.__use_tor:
            if not _Tor.tor_status():
                _Tor.start_tor()
            # Defaults to user specified proxies and headers over those defined by the tor interface
            if 'proxies' not in kwargs.keys():
                kwargs['proxies'] = _Tor.tor_proxies
            
            if 'headers' not in kwargs.keys():
                kwargs['headers'] = _Tor.tor_headers
            else:
                for key, val in _Tor.tor_headers.items():
                    if key not in kwargs['headers']:
                        kwargs['headers'][key] = val
    
    def __grab_thread_wrapper(self, url:str, payload:dict, kwargs):
        try:
            res = self.get(url, enable_js=False, **kwargs)
            payload[url] = res
        except _requests.exceptions.RequestException as err:
            _Warning.raiseWarning(f"Warning: Failed to grab {url} | {err}\n")

    def __responseify_html(self, html):
        resp = _requests.models.Response()
        resp.status_code = 200
        resp.headers = {'header_key': 'NaN'}
        resp._content = str(html).encode("utf-8")
        resp.request = _requests.models.PreparedRequest()
        return resp