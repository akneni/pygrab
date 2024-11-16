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
from pygrab_ll import ThreadSessionRs, HttpResponse

# Libraries
import re as _re
import asyncio as _asyncio
import typing as _typing

__DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, br",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}

def get(
    url:str, 
    enable_js:bool=False, 
    timeout:int=None, 
    override_default_headers:bool=False, 
    params:dict=None, 
    **kwargs
) -> HttpResponse: 
    """
    Gets the content at the specified URL.

    Parameters:
        url (str): The URL to get.
        enable_js (bool, optional): Whether to use a headless browser to scrape a url.
        timeout (int, optional): The timeout in number of seconds
        params (dict, optional): The query parameters to append to the URL
        *args: Variable length argument list passed to requests.get.
        **kwargs: Arbitrary keyword arguments passed to requests.get.

    Returns:
        requests.Response: The response from the server.

    Raises:
        TypeError: If any of the arguments are not of the desired data type.
        ValueError: If the user is trying to read a local file
    """
    if not (isinstance(url, str)):
        raise TypeError("Argument `url` must be a str")
    if not (isinstance(enable_js, bool)):
        raise TypeError("Argument `enable_js` must be a bool")

    if timeout is None:
        timeout = 20 if enable_js else 5

    if _re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d{1,5})?$', url):
        url = "http://" + url
    local_file_starts = ['./', 'C:', '/'] 
    if any([url.startswith(i) for i in local_file_starts]):
        raise ValueError ("Url must start with http. use `get_local()` for local requests.")

    # Handles rotating tor connections
    Tor.increment_rotation_counter()
    
    # Handle query params
    url = __append_query_params(url, params)

    # Handle Js enables requests
    if enable_js:
        res = _js_scraper.pyppeteer_get(url, timeout=timeout)
        return HttpResponse([i for i in res.encode('utf-8')], 200, {})
    else:
        proxy = __set_proxy(kwargs)
        headers = __set_headers(kwargs) if not override_default_headers else kwargs.get('headers', {})
        client = ThreadSessionRs(timeout, headers, proxy)
        return client.get(url)

async def get_async(
    url:str, 
    enable_js:bool=False, 
    timeout:int=None, 
    override_default_headers:bool=False, 
    params:dict=None, 
    **kwargs
) -> HttpResponse: 
    """
    Asynchronously gets the content at the specified URL using a separate thread.

    Parameters:
        url (str): The URL to get.
        enable_js (bool, optional): Whether to use a headless browser to scrape the URL.
        timeout (int, optional): The timeout in number of seconds.
        override_default_headers (bool, optional): Whether to override default headers with custom headers.
        params (dict, optional): The query parameters to append to the URL.
        **kwargs: Arbitrary keyword arguments passed to the synchronous `get` function.

    Returns:
        HttpResponse: The response from the server.

    Raises:
        TypeError: If any of the arguments are not of the desired data type.
        ValueError: If the user is trying to read a local file.
    """
    return await _asyncio.to_thread(
        get, 
        url=url, 
        enable_js=enable_js, 
        timeout=timeout, 
        override_default_headers=override_default_headers, 
        params=params, 
        **kwargs
    )

def get_batch(
    urls:list, 
    enable_js:bool=False, 
    timeout:int=None, 
    params:list=None,
    thread_limit:int=None, 
    override_default_headers:bool=False, 
    **kwargs
) -> dict[str:HttpResponse]:

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
    try:
        urls = list(urls)
    except Exception as e:
        raise TypeError(f"Argument 'urls' must be an iterable object: {e}")
    if not (isinstance(enable_js, bool)):
        raise TypeError("Argument 'enable_js' must be a bool")
    if not (isinstance(thread_limit, (int)) or thread_limit is None):
        raise TypeError("Argument 'thread_limit' must be a int")
    if not (isinstance(timeout, (int, float)) or timeout is None):
        raise TypeError("Argument 'timeout' must be a int or float")
    
    if thread_limit is None:
        thread_limit = 30 if enable_js else 200
    
    if timeout is None:
        timeout = int( (25 if enable_js else 8) * (1.75 if Tor.tor_status() else 1) )

    # Handle query params
    if params is not None:
        if isinstance(params, dict):
            urls = [__append_query_params(url, params) for url in urls]
        else:
            if len(urls) != len(params):
                raise ValueError("Arguments `urls` and `params` must be of the same length.")
            urls = [__append_query_params(url, param) for url, param in zip(urls, params)]

    # remove repeats to prevent accidental DoS attacks
    urls = list(dict.fromkeys(urls))

    # Handle async js enabled scraping
    if enable_js:
        # Don't increment the number of requests, but rotate connections if it's necessary
        Tor.increment_rotation_counter(0) 
        result = {url:None for url in urls}
        for thread_counter in range (0, len(urls), thread_limit):
            curr_urls = urls[thread_counter:thread_counter+thread_limit]
            if enable_js:
                htmls:dict = _js_scraper.pyppeteer_get_async(curr_urls, timeout=timeout)
                result.update( {k:HttpResponse([i for i in v.encode('utf-8')], 200, {}) for k,v in htmls.items()} )
        Tor.increment_rotation_counter(len(urls))
        return result

    headers = __set_headers(kwargs) if not override_default_headers else kwargs.get('headers', {})
    proxy = __set_proxy(kwargs)
    client = ThreadSessionRs(timeout, headers, proxy)
    result = client.get_batch(urls, thread_limit, _Warning.warning_settings)
    Tor.increment_rotation_counter(len(urls))
    return result

def get_local(filename:str, local_read_type:str='r', encoding:str='utf-8') -> str:
    """
    Reads the contents of a file and returns it to the user.

    This function reads the contents of a file and returns it to the user.

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

def download(url:str, local_filename:str, timeout:float=5) -> None:
    """
    Downloads a file from a given URL and saves it locally.

    This function retrieves a file from a specified URL and saves it to a local directory. The file will be saved with the filename from the URL if no local filename is specified.

    Parameters:
        url (str): The URL of the file to be downloaded. Must include a file extension.
        local_filename (str): The name to be used when saving the file locally. If none is provided, the function uses the filename from the URL. Must include a file extension if provided.
        timeout: (float, optional): The number of seconds the request should timeout after
    Returns:
        None

    Raises:
        TypeError: If any of the arguments are not of the desired data type.
        ValueError: If 'local_filename' is specified but does not contain a file extension.
    """
    if not (isinstance(url, str)):
        raise TypeError("Argument 'url' must be a str")
    elif not (isinstance(local_filename, str)):
        raise TypeError("Argument 'local_filename' must be a str")
    
    # sends a request to get the file contents
    client = ThreadSessionRs(timeout, __set_headers({}), __set_proxy({}))
    client.download(url, local_filename)

async def download_async(url:str, local_filename:str, timeout:float=5) -> None:
    """
    Asynchronously downloads a file from a given URL and saves it locally using a separate thread.

    This function retrieves a file from a specified URL and saves it to a local directory. The file will be saved with the filename from the URL if no local filename is specified.

    Parameters:
        url (str): The URL of the file to be downloaded. Must include a file extension.
        local_filename (str): The name to be used when saving the file locally. If none is provided, the function uses the filename from the URL. Must include a file extension if provided.
        timeout: (float, optional): The number of seconds the request should timeout after.
        
    Returns:
        None

    Raises:
        TypeError: If any of the arguments are not of the desired data type.
        ValueError: If 'local_filename' is specified but does not contain a file extension.
    """
    return await _asyncio.to_thread(download, url=url, local_filename=local_filename, timeout=timeout)

def download_batch(urls:list, local_filenames:list=None, thread_limit:int=50, timeout:float=12.0, time_rest:float=0) -> None:
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
    # Validate argument 
    if local_filenames is not None:
        if len(urls) != len(local_filenames):
            raise ValueError("Lists 'url' and 'local_filenames' must be of equal length.")
    try:
        # Removes repeats to avoid accidental DoS
        # Maintains parallelism between lists
        if not isinstance(urls, dict):
            urls = {url:filename for url, filename in zip(urls, local_filenames)}
        urls, local_filenames = zip(*urls.items())
    except Exception:
        raise TypeError("`urls` must be list of dict and `local_filenames` must be list (or None if url is dict)")
    if not (isinstance(timeout, (int, float))):
        raise TypeError("Argument 'timeout' must be a int or float")
    if not (isinstance(time_rest, (int, float))):
        raise TypeError("Argument 'time_rest' must be a int or float")

    # Uses rust dependencies to asynchronously download files
    client = ThreadSessionRs(timeout, __set_headers({}), __set_proxy({}))
    client.download_batch(urls, local_filenames, thread_limit, _Warning.warning_settings)

    # If tor rotations isn't None, then make this entire batch of requests with one connection
    # and then the connection to be changed on the next request
    Tor.increment_rotation_counter(len(urls))
    

def head(url:str, params:dict=None, timeout:float=5, **kwargs) -> HttpResponse:
    Tor.increment_rotation_counter()
    headers = __set_headers(kwargs)
    proxy = __set_proxy(kwargs)
    url = __append_query_params(url, params)
    client = ThreadSessionRs(timeout, headers, proxy)
    return client.head(url)

def post(url:str, data=None, json:dict=None, params:dict=None, timeout:float=5, **kwargs) -> HttpResponse:
    """
    Sends a POST request to the specified URL.

    Parameters:
        url (str): The URL to send the POST request to.
        data (str, dict, bytes, optional): The data to be sent in the body of the request. Can be a string, dictionary, or bytes.
        json (dict, optional): A JSON object to be sent in the body of the request.
        params (dict, optional): The query parameters to append to the URL.
        timeout (float, optional): The timeout in number of seconds.
        **kwargs: Arbitrary keyword arguments passed to requests.post.

    Returns:
        HttpResponse: The response from the server.

    Raises:
        ValueError: If the URL is trying to create a local file.
        TypeError: If the data type of 'data', 'json', or 'params' is not supported.
    """
    local_file_starts = ['./', 'C:', '/'] 
    if any([url.startswith(i) for i in local_file_starts]):
        raise ValueError("use post_local() for creation of local files.")
    Tor.increment_rotation_counter()
    headers = __set_headers(kwargs)
    proxy = __set_proxy(kwargs)
    url = __append_query_params(url, params)
    client = ThreadSessionRs(timeout, headers, proxy)
    if data is not None and isinstance(data, str):
        data = data.encode('utf-8')
        return client.post(url, data)
    if json is not None and isinstance(json, dict):
        json = {str(k): str(v) for k, v in json.items()}
        return client.post_json(url, json)
    if data is not None and isinstance(data, dict):
        data = {str(k): str(v) for k, v in data.items()}
        return client.post_json(url, data)
    if data is not None and isinstance(data, bytes):
        return client.post(url, [i for i in data])

async def post_async(url:str, data=None, json:dict=None, params:dict=None, timeout:float=5, **kwargs) -> HttpResponse:
    """
    Asynchronously sends a POST request to the specified URL using a separate thread.

    Parameters:
        url (str): The URL to send the POST request to.
        data (str, dict, bytes, optional): The data to be sent in the body of the request. Can be a string, dictionary, or bytes.
        json (dict, optional): A JSON object to be sent in the body of the request.
        params (dict, optional): The query parameters to append to the URL.
        timeout (float, optional): The timeout in number of seconds.
        **kwargs: Arbitrary keyword arguments passed to requests.post.

    Returns:
        HttpResponse: The response from the server.

    Raises:
        ValueError: If the URL is trying to create a local file.
        TypeError: If the data type of 'data', 'json', or 'params' is not supported.
    """
    return await _asyncio.to_thread(post, url=url, data=data, json=json, params=params, timeout=timeout, **kwargs)

def post_batch(urls:list[str] | str, data:list[_typing.Any], timeout:float=5, **kwargs):
    Tor.increment_rotation_counter(len(urls))
    headers = __set_headers(kwargs)
    proxy = __set_proxy(kwargs)
    client = ThreadSessionRs(timeout, headers, proxy)

    if isinstance(urls, str):
        urls = [urls for _ in range(len(data))]

    if isinstance(data[0], str):
        data = [i.encode('utf-8') for i in data]
        return client.post_batch(urls, data)
    if isinstance(data[0], bytes):
        return client.post_batch(urls, data)
    if isinstance(data[0], dict):
        return client.post_json_batch(urls, data)

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

def put(url, data:str=None, timeout:float=5, **kwargs):
    Tor.increment_rotation_counter()
    headers = __set_headers(kwargs)
    proxy = __set_proxy(kwargs)
    client = ThreadSessionRs(timeout, headers, proxy)
    return client.put(url, data)

def patch(url, data=None, **kwargs):
    raise NotImplementedError("Not yet implemented in rust backend")
    Tor.increment_rotation_counter()

def delete(url, timeout:float=5, **kwargs):
    Tor.increment_rotation_counter()
    headers = __set_headers(kwargs)
    proxy = __set_proxy(kwargs)
    client = ThreadSessionRs(timeout, headers, proxy)
    return client.delete(url)

def options(url, timeout:float=5, **kwargs):
    Tor.increment_rotation_counter()
    headers = __set_headers(kwargs)
    proxy = __set_proxy(kwargs)
    client = ThreadSessionRs(timeout, headers, proxy)
    return client.options(url)

def display_public_status() -> None:
    connection_data = get('http://ip-api.com/json').json()
    print("Tor Service Enabled:  ", Tor.tor_status())
    print("Public Ip Address:    ", connection_data['query'])
    if 'country' in connection_data.keys():
        print("Country:              ", connection_data['country'])
    if 'regionName' in connection_data.keys():
        print("Region:               ", connection_data['regionName'])
    if 'city' in connection_data.keys():
        print("City:                 ", connection_data['city'])

def warn_settings(warn: bool) -> True:
    if not isinstance(warn, bool):
        raise TypeError("Argument 'warn' must be a bool")
    _Warning.warning_settings = warn

def __set_proxy(kwargs) -> str:
    # Defaults to user specified proxies and headers over those defined by the tor interface
    if 'proxies' in kwargs.keys():
        try: return kwargs['proxies']['http']
        except: raise ValueError("proxies incorrectly formatted. {'http': '0.0.0.0:8080', 'https': '0.0.0.0:8080'}")
    elif Tor.tor_status():
        return Tor.tor_proxies['http']

def __set_headers(kwargs):
    headers = __DEFAULT_HEADERS.copy()
    headers.update(kwargs.get('headers', {}))
    return headers

def __append_query_params(url:str, params:dict=None) -> str:
    """
    A function to append query parameters to a URL.

    Args:
        url (str): The original URL.
        params (dict, optional): The parameters to be appended to the URL. Defaults to None.

    Returns:
        str: The URL with the appended query parameters.
    """
    if params is None:
        return url
    params = '&'.join(f'{k}={v}' for k, v in params.items())
    url += ('&' if '?' in url else '?') + params
    return url
