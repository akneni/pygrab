"""
This module implements the primary developer interface for pygrab.

The main responsibilities of the :class:pygrab <pygrab> class revolve 
predominantly around the developer's perspective. pygrab delegates the 
majority of its heavy-duty tasks to smaller, specialized auxiliary 
modules and functions, ensuring an intuitive and seamless experience 
in handling various types of web requests, including asynchronous tasks, 
Javascript-enabled sites, and local requests.
"""

# Local modules
from .tor import Tor
from .session import Session
from .js_scraper import js_scraper as _js_scraper
from .warning import Warning as _Warning
from .tor_rotation import TorRotation as _TorRotation
from .autosession import autosession as _autosession

# Libraries
import requests as _requests
import time as _time
import socket as _socket
import re as _re
import threading as _threading
import math as _math

def get(url:str, enable_js:bool=False, ignore_tor_rotations:bool=False, timeout:int=None, *args, **kwargs): 
    """
    Gets the content at the specified URL.

    Parameters:
        url (str): The URL to get.
        enable_js (bool, optional): Whether to use a headless browser to scrape a url.
        ignore_tor_rotations (bool, optional): Whether to count this request when calculating tor rotations
        timeout (int, optional): The timeout in number of seconds
        *args: Variable length argument list passed to requests.get.
        **kwargs: Arbitrary keyword arguments passed to requests.get.

    Returns:
        requests.Response: The response from the server.

    Raises:
        TypeError: If any of the arguments are not of the desired data type.
        ValueError: If the user is trying to read a local file
    """
    if not (isinstance(url, str)):
        raise TypeError("Argument 'url' must be a str")
    elif not (isinstance(enable_js, bool)):
        raise TypeError("Argument 'enable_js' must be a bool")
    elif not (isinstance(ignore_tor_rotations, bool)):
        raise TypeError("Argument 'ignore_tor_rotations' must be a bool")

    if timeout is None:
        timeout = 20 if enable_js else 5

    local_file_starts = ['./', 'C:', '/'] 
    url_file_starts = ['http', 'ftp:', 'mailto:']
    if _re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d{1,5})?$', url):
        url = "http://" + url
    if any([url.startswith(i) for i in local_file_starts]):
        raise ValueError ("Url must start with http. use get_local() for local requests.")
    elif any([url.startswith(i) for i in url_file_starts]):
        # Handles rotating tor connections
        if not ignore_tor_rotations:
            __handle_tor_rotations()
        
        # Handle Js enables requests
        if enable_js:
            res = _js_scraper.pyppeteer_get(url, timeout=timeout)
            return __responseify_html(res)
        else:
            __append_tor_kwargs(kwargs)
            try:
                return _requests.get(url, timeout=timeout, *args, **kwargs)
            except _requests.exceptions.InvalidSchema as err:
                if 'Missing dependencies for SOCKS support'.lower() in str(err).lower():
                    raise ModuleNotFoundError("Required module 'PySocks' not found.")
                raise _requests.exceptions.InvalidSchema(err)

    raise ValueError(f"Invalid url or IP address: {url}")
    
def get_async(urls:list, enable_js:bool=False, timeout:int=None, time_rest:float=0, autosession:bool=None, thread_limit:int=None, *args, **kwargs) -> dict:
    """
    Gets multiple URLs asynchronously.

    This function sends HTTP requests to a list of URLs in separate threads, allowing for concurrent HTTP requests.
    The function returns a list of responses from the grabbed URLs. For each request that had a connection error,
    a warning will be printed to the console.

    Args:
        urls (list): A list of URLs to grab.
        thread_limit (int, optional): The maximum number of threads that will be spawned. 
        time_rest (float, optional): The time in seconds to wait between starting each thread. Defaults to 0.
        *args: Variable length argument list to pass to the get function.
        **kwargs: Arbitrary keyword arguments to pass to the get function.

    Returns:
        disc: A dictionary of responses with the grabbed URLs as keys and their respective responses as values.
    
    Raises:
        TypeError: If any of the arguments are not of the desired data type.
    """

    if (isinstance(urls, (str, int, float, bool))):
        raise TypeError("Argument 'urls' must be an iterable object")
    elif not (isinstance(enable_js, bool)):
        raise TypeError("Argument 'enable_js' must be a bool")
    elif not (isinstance(time_rest, int) or isinstance(time_rest, float)):
        raise TypeError("Argument 'time_rest' must be a int or float")
    elif not (isinstance(thread_limit, int) or (thread_limit is None)):
        raise TypeError("Argument 'thread_limit' must be a int")
    elif not (isinstance(timeout, int) or isinstance(timeout, float) or (thread_limit is None)):
        raise TypeError("Argument 'timeout' must be a int or float")
    
    if thread_limit is None:
        thread_limit = 30 if enable_js else 800
    
    if timeout is None:
        timeout = int( (25 if enable_js else 15) * (1.5 if Tor.tor_status() else 1) )

    # remove repeats to prevent possible DoS attacks
    urls = list(dict.fromkeys(list(urls)))
    result = {url:None for url in urls}

    # Autosession
    if autosession is None:
        autosession = (not enable_js) and (not Tor.tor_status())
    elif autosession:
        if enable_js: raise ValueError("autosession not supported for js-enabled scraping")
        if Tor.tor_status(): raise NotImplementedError("autosession not supported for Tor (support coming soon)")
    if autosession:
        _autosession.get_async_autosession(urls, timeout=timeout, time_rest=time_rest, payload=result, *args, **kwargs)
        return result
    
    # Handle async js enabled scraping
    if enable_js:
        __handle_tor_rotations(0) # Don't increment the number of requests, but rotate connections if it's necessary
        for thread_counter in range (0, len(urls), thread_limit):
            curr_urls = urls[thread_counter:thread_counter+thread_limit]
            if enable_js:
                htmls:dict = _js_scraper.pyppeteer_get_async(curr_urls, timeout=timeout)
                result.update( {k:__responseify_html(v) for k,v in htmls.items()} )
        __handle_tor_rotations(len(urls))
        return result

    batch_size = _math.ceil(len(urls)/thread_limit)
    batch_num = _math.ceil(len(urls)/batch_size)
    threads:list[_threading.Thread] = []
    for batch_ind in range (batch_num):
        threads.append(
            _threading.Thread(target=__grab_thread_wrapper, args=[batch_ind*batch_size, batch_size, urls, timeout, result, args, kwargs])
        )
        threads[-1].start()
        _time.sleep(time_rest)
        
    for thread in threads:
        thread.join()

    __handle_tor_rotations(len(urls))
        
    return result

def get_local(filename:str, local_read_type:str='r', encoding:str='utf-8') -> str:
    """
    Reads the contens of a file and returns it to the user.

    This function reads the contens of a file and returns it to the user.

    Parameters:
        filename (str): The file to read from.
        local_read_type (str, optional): The read type, 'r' or 'rb' for example.
        encoding (str, optional): Encoding, 'utf-8 or 'ascii' for example.

    Returns:
        data: The contents of the file

    Raises:
        TypeError: If any of the arguments are not of the desired data type.
    """
        
    if not (isinstance(filename, str)):
        raise TypeError("Argument 'filename' must be a str")
    if not (isinstance(local_read_type, str)):
        raise TypeError("Argument 'local_read_type' must be a str")
    if not (isinstance(encoding, str)):
        raise TypeError("Argument 'encoding' must be a str")


    with open(filename, local_read_type, encoding=encoding) as f:
        data = f.read()
    return data

def download(url:str, local_filename:str=None, ignore_tor_rotations:bool=False) -> None:
    """
    Downloads a file from a given URL and saves it locally.

    This function retrieves a file from a specified URL and saves it to a local directory. The file will be saved with the filename from the URL if no local filename is specified.

    Parameters:
        url (str): The URL of the file to be downloaded. Must include a file extension.
        local_filename (str, optional): The name to be used when saving the file locally. If none is provided, the function uses the filename from the URL. Must include a file extension if provided.

    Returns:
        None

    Raises:
        TypeError: If any of the arguments are not of the desired data type.
        ValueError: If 'local_filename' is specified but does not contain a file extension.
    """
    if not (isinstance(url, str)):
        raise TypeError("Argument 'url' must be a str")
    elif not (isinstance(local_filename, str) or local_filename is None):
        raise TypeError("Argument 'local_filename' must be a str")

    if local_filename is not None:
        if '.' not in local_filename:
            raise ValueError("Argument 'local_filename' must have file extention.")
    elif '/' in url:
        local_filename = url.split('/')[-1]
    else:
        local_filename=url
    
    # No need to handle tor roations here as it's already handled in get()

    # sends a request to get the file contents
    response = get(url, ignore_tor_rotations=ignore_tor_rotations)

    if response.status_code == 200:
        with open(local_filename, 'wb') as f:
            f.write(response.content)
    else:
        raise Exception(f"Error fetching url. Status code - {response.status_code}")

def download_async(urls:list, local_filenames:list=None, thread_limit=500, time_rest=0) -> None:
    """
    Executes multiple file downloads asynchronously from a list of given URLs and saves them locally.

    This function uses threading to download multiple files simultaneously. Each file is saved with a filename from the list of local filenames, if provided. If no local filename is provided, the function uses the filename from the corresponding URL.

    Parameters:
        urls (list of str): The URLs of the files to be downloaded. Each URL must include a file extension.
        local_filename (list of str, optional): A list of names to be used when saving the files locally. If none is provided, the function uses the filename from each corresponding URL. Each filename must include a file extension if provided. Must be of same length as 'urls' if provided.
        thread_limit (int, optional): The maximum number of threads that will be spawned. 
        time_rest (int, optional): The amount of time to rest between the start of each download thread. Defaults to 0 seconds.

    Returns:
        None

    Raises:
        TypeError: If any of the arguments are not of the desired data type.
        ValueError: If a 'local_filenames' is specified but does not contain a file extension.
    """
    # Check argument types
    if (isinstance(urls, (str, int, float, bool))):
        raise TypeError("Argument 'urls' must be an iterable object")
    elif (isinstance(local_filenames, (str, int, float, bool)) or local_filenames is None):
        raise TypeError("Argument 'local_filename' must be an iterable object")
    elif not (isinstance(time_rest, int) or isinstance(time_rest, float)):
        raise TypeError("Argument 'time_rest' must be a int or float")

    # remove repeats to prevent possible DoS attacks
    urls = list(dict.fromkeys(list(urls)))
    local_filenames = list(dict.fromkeys(list(local_filenames)))

    if local_filenames is not None:
        if len(urls) != len(local_filenames):
            raise ValueError("Lists 'url' and 'local_filenames' must be of equal length.")
    else:
        local_filenames = [None for _ in range(len(urls))]

    # Uses the threading module to asynchrounously download the files
    thread_counter = 0
    while (thread_counter < len(urls)):
        threads = []
        sub_urls = urls[thread_counter:thread_counter+thread_limit]
        sub_local_filename= local_filenames[thread_counter:thread_counter+thread_limit]

        for url, name in zip(sub_urls, sub_local_filename):
            threads.append(_threading.Thread(target=download, args=[url, name, True]))
            threads[-1].start()
            _time.sleep(time_rest)
        
        for thread in threads:
            thread.join()
        thread_counter += thread_limit

    # If tor rotations isn't None, then make this entire batch of requests with one connection
    # and then the connection to be changed on the next request
    __handle_tor_rotations(len(urls))
    

def head(url:str, **kwargs):
    __handle_tor_rotations(1)
    __append_tor_kwargs(kwargs)
    return _requests.head(url, **kwargs)

def post(url:str, data=None, json=None, **kwargs):
    local_file_starts = ['./', 'C:', '/'] 
    if any([url.startswith(i) for i in local_file_starts]):
        raise ValueError("use post_local() for creation of local files.")
    __handle_tor_rotations(1)
    __append_tor_kwargs(kwargs)
    return _requests.post(url, data=data, json=json, **kwargs)


def post_local(filepath:str, data:str, local_save_type:str="w", encoding:str='utf-8') -> None:
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

def put(url, data=None, **kwargs):
    __handle_tor_rotations(1)
    __append_tor_kwargs(kwargs)
    return _requests.put(url, data=data, **kwargs)

def patch(url, data=None, **kwargs):
    __handle_tor_rotations(1)
    __append_tor_kwargs(kwargs)
    return _requests.patch(url, data=data, **kwargs)

def delete(url, **kwargs):
    __handle_tor_rotations(1)
    __append_tor_kwargs(kwargs)
    return _requests.delete(url, **kwargs)

def options(url, **kwargs):
    __handle_tor_rotations(1)
    __append_tor_kwargs(kwargs)
    return _requests.options(url, **kwargs)

def tor_status() -> bool:
    return Tor.tor_status()

def display_tor_status() -> None:
    connection_data = get('http://ip-api.com/json').json()
    print("Tor Service Enabled:  ", Tor.tor_status())
    print("Public Ip Address:    ", connection_data['query'])
    if 'country' in connection_data.keys():
        print("Country:              ", connection_data['country'])
    if 'regionName' in connection_data.keys():
        print("Region:               ", connection_data['regionName'])
    if 'city' in connection_data.keys():
        print("City:                 ", connection_data['city'])

def rotate_tor(num_req_per_rotation):
    if Tor.override_status():
        raise Exception("Cannot rotate tor connections when an override is forced. End the other tor service in order to rotate connections.")
    if not Tor.tor_status():
        Tor.start_tor()
    if num_req_per_rotation < 1:
        _TorRotation.Tor_Reconnect = None
    _TorRotation.Tor_Reconnect = [num_req_per_rotation, num_req_per_rotation]

def end_rotate_tor():
    _TorRotation.Tor_Reconnect = None

def warn_settings(warn:bool):
    if not isinstance(warn, bool):
        raise TypeError("Argument 'warn' bust be a bool")
    _Warning.warning_settings = warn

def scan_ip(ip:str, port:int=80, timeout:int=1) -> bool:
    """
    Scans a given IP address to check if it's online.

    This function attempts to connect to a specified IP address and port, returning True if the connection is successful
    and False otherwise.

    Args:
        ip (str): The IP address to scan, in the format '10.0.0.3'.
        port (int, optional): The port number to connect to. Defaults to 80.
        timeout (int, optional): The timeout in seconds for the connection attempt. Defaults to 1.

    Returns:
        bool: True if the IP address is online, False otherwise.

    Raises:
        TypeError: If the 'ip' argument is not a string.
        ValueError: If the 'ip' argument is not in the correct format or if an invalid IP address is provided.
    """
    if not isinstance(ip, str):
        raise TypeError("Argument 'ip' must be a string.")

    pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$'
    if not _re.match(pattern, ip):
        raise ValueError("Argument 'ip' must be in the format 10.0.0.3")

    if Tor.tor_status():
        _Warning.raiseWarning("TorNotUtilizedWarning: Note that the tor network will not be usd when scanning ips")

    try:
        session = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
        session.settimeout(timeout)
        session.connect((ip, port))
        session.close()
        return True
    except (_socket.timeout, ConnectionRefusedError):
        return False
    except OSError:
        raise ValueError("Invalid ip address.")

def scan_iprange(ips:str, port:int=80, timeout:int=1) -> list:
    """
    Scans a range of IP addresses to check which ones are online.

    This function scans a specified range of IP addresses, returning a list of those that are online.

    Args:
        ips (str): The IP address range to scan, in the format '10.0.0.1-255'.
        port (int, optional): The port number to connect to. Defaults to 80.
        timeout (int, optional): The timeout in seconds for the connection attempt. Defaults to 1.

    Returns:
        list: A list of IP addresses that are online within the specified range.

    Raises:
        TypeError: If the 'ips' argument is not a string.
        ValueError: If the 'ips' argument is not in the correct format or if the IP range start is greater or equal to 255.
    """

    if not isinstance(ips, str):
        raise TypeError("Argument 'ips' must be a string.")

    ips = ips.replace(' ', '')
    pattern = r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}-\d{1,3}$'
    if not _re.match(pattern, ips):
        raise ValueError("Argument 'ips' must be in the format 10.0.0.1-255")

    first_three = ips.replace(ips.split('.')[-1], '')
    start, end = ips.split('.')[-1].split('-')
    ip_range = [first_three + str(i) for i in range (int(start), int(end)+1)]

    if int(start) >= 255:
        raise ValueError('Ip range must start below 255.')

    if Tor.tor_status():
        _Warning.raiseWarning("TorNotUtilizedWarning: Note that the tor network will not be usd when scanning ips")

    reset_warn = _Warning.warning_settings
    _Warning.warning_settings = False # stifle warnings while threading
    
    threads = []
    res = {i:False for i in ip_range}
    for i in ip_range:
        threads.append(
            _threading.Thread(target=__scan_ip_wrapper, args=[i, port, timeout, res])
        )
        threads[-1].start()
    
    for i in threads:
        i.join()
    
    _Warning.warning_settings = reset_warn

    
    return [key for key, value, in res.items() if value]

# Helper function for get_async
def __grab_thread_wrapper(start, num, urls:list[str], timeout:int, payload:dict, args, kwargs):
    for i in range (start, start+num):
        if i == len(urls):
            break
        url = urls[i]
        try:
            res = get(url, enable_js=False, ignore_tor_rotations=True, timeout=timeout, *args, **kwargs)
            payload[url] = res
        except Exception as err:
            _Warning.raiseWarning(f"Warning: Failed to grab {url} | {err}")

# Helper function for scan_iprange
def __scan_ip_wrapper(ip, port, timeout, res):
    try:
        res[ip] = scan_ip(ip=ip, port=port, timeout=timeout)
    except ValueError:
        pass

def __handle_tor_rotations(num_req=1):
    # Handles rotating tor connections
    if _TorRotation.Tor_Reconnect is not None:
        if _TorRotation.Tor_Reconnect[0] <= 0:
            Tor.start_tor()
            _TorRotation.Tor_Reconnect[0] = _TorRotation.Tor_Reconnect[1] - 1
        else:
            _TorRotation.Tor_Reconnect[0] -= num_req

def __append_tor_kwargs(kwargs):
    if Tor.tor_status():
        # Defaults to user specified proxies and headers over those defined by the tor interface
        if 'proxies' not in kwargs.keys():
            kwargs['proxies'] = Tor.tor_proxies
        
        if 'headers' not in kwargs.keys():
            kwargs['headers'] = Tor.tor_headers
        else:
            for key, val in Tor.tor_headers.items():
                if key not in kwargs['headers']:
                    kwargs['headers'][key] = val

def __responseify_html(html):
    resp = _requests.models.Response()
    resp.status_code = 200
    resp.headers = {'header_key': 'NaN'}
    resp._content = str(html).encode("utf-8")
    resp.request = _requests.models.PreparedRequest()
    return resp
