"""
This module implements the primary developer interface for pygrab.

The main responsibilities of the :class:pygrab <pygrab> class revolve 
predominantly around the developer's perspective. pygrab delegates the 
majority of its heavy-duty tasks to smaller, specialized auxiliary 
modules and functions, ensuring an intuitive and seamless experience 
in handling various types of web requests, including asynchronous tasks, 
Javascript-enabled sites, and local requests.

"""


from .proxylist import ProxyList
import requests as _requests
from pyppeteer import launch as _launch
import asyncio as _asyncio
import time as _time


def get(url: str, use_proxy=False, retries=5, enable_js=False, *args, **kwargs): 
    """
    Gets the content at the specified URL.

    Parameters:
        url (str): The URL to get.
        use_proxy (bool, optional): Whether to use a proxy. Defaults to False.
        retries (int, optional): The number of times to retry the request if it fails. Defaults to 5.
        encoding (str, optional): The encoding to use when reading the response. Defaults to 'utf-8'.
        *args: Variable length argument list passed to requests.get.
        **kwargs: Arbitrary keyword arguments passed to requests.get.

    Returns:
        requests.Response: The response from the server.

    Raises:
        TypeError: If any of the arguments are not of the desired data type.
    """
    if not (isinstance(url, str)):
        raise TypeError("Argument 'url' must be a str")
    elif not (isinstance(use_proxy, bool)):
        raise TypeError("Argument 'use_proxy' must be a bool")
    elif not (isinstance(retries, int)):
        raise TypeError("Argument 'retries' must be a int")
    elif not (isinstance(enable_js, bool)):
        raise TypeError("Argument 'enable_js' must be a bool")

    local_file_starts = ['./', 'C:', '/'] 
    url_file_starts = ['http', 'ftp:', 'mailto:']
    if any([url.startswith(i) for i in local_file_starts]):
        raise ValueError ("Url must start with http. use get_local() for local requests.")
    elif any([url.startswith(i) for i in url_file_starts]):        
        if enable_js:
            try:
                res = __grab_enable_js(url)
            except RuntimeError as err:
                if "This event loop is already running" in str(err):
                    raise RuntimeError("enable_js=True unsupported in jupiter environment.")
                else:
                    raise RuntimeError(err)
            
            resp = _requests.models.Response()
            resp.status_code = 200
            resp.headers = {'header_key': 'NaN'}  # replace with your actual headers
            resp._content = str(res).encode("utf-8")  # replace with your actual HTML content
            resp.request = _requests.models.PreparedRequest()
            return resp
        else:
            session = _requests.Session()
            retry = _requests.packages.urllib3.util.retry.Retry(total=retries, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
            adapter = _requests.adapters.HTTPAdapter(max_retries=retry)
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            
            if use_proxy:
                if ProxyList.is_empty():
                    ProxyList.gen_proxies()
                temp_prox = ProxyList.get_random()
                proxies = {
                    'http': f'http://{temp_prox[0]}:{temp_prox[1]}',
                    'https': f'https://{temp_prox[0]}:{temp_prox[1]}'
                }
                try:
                    return session.get(url, *args, **kwargs, proxies=proxies)
                except Exception as err:
                    raise Exception(f'{err}\n\nThere seems to have been an error with the proxy IP. Please note that free proxies may not be reliable.')

            return session.get(url, *args, **kwargs)
    raise Exception(f"Invalid url: {url}")
    
def get_async(urls, use_proxy=False, retries=5, enable_js=False, thread_limit=800, time_rest=0, *args, **kwargs) -> list:
    """
    Gets multiple URLs asynchronously.

    This function sends HTTP requests to a list of URLs in separate threads, allowing for concurrent HTTP requests.
    The function returns a list of responses from the grabbed URLs.

    Args:
        urls (list): A list of URLs to grab.
        use_proxy (bool, optional): If True, uses a proxy for the HTTP requests. Defaults to False.
        retries (int, optional): The number of times to retry the HTTP request in case of failure. Defaults to 5.
        thread_limit (int, optional): The maximum number of threads that will be spawned. 
        time_rest (int, optional): The time in seconds to wait between starting each thread. Defaults to 0.
        *args: Variable length argument list to pass to the get function.
        **kwargs: Arbitrary keyword arguments to pass to the get function.

    Returns:
        list: A list of responses from the grabbed URLs.
    
    Raises:
        TypeError: If any of the arguments are not of the desired data type.
    """
    if (isinstance(urls, (str, int, float, bool))):
        raise TypeError("Argument 'urls' must be an iterable object")
    elif not (isinstance(use_proxy, bool)):
        raise TypeError("Argument 'use_proxy' must be a bool")
    elif not (isinstance(retries, int)):
        raise TypeError("Argument 'retries' must be a int")
    elif not (isinstance(enable_js, bool)):
        raise TypeError("Argument 'enable_js' must be a bool")
    elif not (isinstance(time_rest, int) or isinstance(time_rest, float)):
        raise TypeError("Argument 'time_rest' must be a int or float")

    import threading as _threading # only import if async functionality is needed
    if type(urls) == str:
        return [get(urls, use_proxy=use_proxy, retries=retries, enable_js=enable_js, *args, **kwargs)]


    result = []
    thread_counter = 0

    while thread_counter < len(urls):
        sub_urls = urls[thread_counter:thread_counter+thread_limit]
        threads = []
        for url in sub_urls:
            threads.append(_threading.Thread(target=__grab_thread_wrapper, args=[url, result, args, kwargs, use_proxy, retries, enable_js]))
            threads[-1].start()
            _time.sleep(time_rest)
        
        for thread in threads:
            thread.join()
        thread_counter += thread_limit
        
    return result

def get_local(filename:str, local_read_type:str='r', encoding:str='utf-8'):
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

def download(url: str, local_filename:str=None, use_proxy=False, retries=5) -> None:
    """
    Downloads a file from a given URL and saves it locally.

    This function retrieves a file from a specified URL and saves it to a local directory. The file will be saved with the filename from the URL if no local filename is specified.

    Parameters:
        url (str): The URL of the file to be downloaded. Must include a file extension.
        local_filename (str, optional): The name to be used when saving the file locally. If none is provided, the function uses the filename from the URL. Must include a file extension if provided.
        use_proxy (bool, optional): If set to True, the function will use a proxy server for the download. Defaults to False.
        retries (int, optional): The number of retry attempts for the download in case of failure. Defaults to 5.

    Returns:
        None

    Raises:
        TypeError: If any of the arguments are not of the desired data type.
        ValueError: If 'url' does not contain a file extension or if there was an error fetching the URL.
        ValueError: If 'local_filename' is specified but does not contain a file extension.
    """
    if not (isinstance(url, str)):
        raise TypeError("Argument 'url' must be a str")
    elif not (isinstance(local_filename, str) or local_filename is None):
        raise TypeError("Argument 'local_filename' must be a str")
    elif not (isinstance(use_proxy, bool)):
        raise TypeError("Argument 'use_proxy' must be a bool")
    elif not (isinstance(retries, int)):
        raise TypeError("Argument 'retries' must be a int")
    
    if '.' not in url:
        raise ValueError("Argument 'url' needs a filepath extention")
    

    if local_filename is not None:
        if '.' not in local_filename:
            raise ValueError("Argument 'local_filename' must have file extention.")
    elif '/' in url:
        local_filename = url.split('/')[-1]
    else:
        local_filename=url
        

    response = get(url, use_proxy=use_proxy, retries=retries)

    if response.status_code == 200:
        with open(local_filename, 'wb') as f:
            f.write(response.content)
    else:
        raise Exception(f"Error fetching url. Status code - {response.status_code}")

def download_async(urls:list, local_filename:list=None, use_proxy=False, retries=5, thread_limit=500, time_rest=0) -> None:
    """
    Executes multiple file downloads asynchronously from a list of given URLs and saves them locally.

    This function uses threading to download multiple files simultaneously. Each file is saved with a filename from the list of local filenames, if provided. If no local filename is provided, the function uses the filename from the corresponding URL.

    Parameters:
        urls (list of str): The URLs of the files to be downloaded. Each URL must include a file extension.
        local_filename (list of str, optional): A list of names to be used when saving the files locally. If none is provided, the function uses the filename from each corresponding URL. Each filename must include a file extension if provided. Must be of same length as 'urls' if provided.
        use_proxy (bool, optional): If set to True, the function will use a proxy server for the downloads. Defaults to False.
        retries (int, optional): The number of retry attempts for the downloads in case of failure. Defaults to 5.
        thread_limit (int, optional): The maximum number of threads that will be spawned. 
        time_rest (int, optional): The amount of time to rest between the start of each download thread. Defaults to 0 seconds.

    Returns:
        None

    Raises:
        TypeError: If any of the arguments are not of the desired data type.
        ValueError: If 'local_filename' is specified but does not match the length of 'urls' or if a URL does not contain a file extension.
        ValueError: If a 'local_filename' is specified but does not contain a file extension.
    """
    if (isinstance(urls, (str, int, float, bool))):
        raise TypeError("Argument 'urls' must be an iterable object")
    elif (isinstance(local_filename, (str, int, float, bool)) or local_filename is None):
        raise TypeError("Argument 'local_filename' must be an iterable object")
    elif not (isinstance(use_proxy, bool)):
        raise TypeError("Argument 'use_proxy' must be a bool")
    elif not (isinstance(retries, int)):
        raise TypeError("Argument 'retries' must be a int")
    elif not (isinstance(time_rest, int) or isinstance(time_rest, float)):
        raise TypeError("Argument 'time_rest' must be a int or float")


    if local_filename is not None:
        if len(urls) != len(local_filename):
            raise ValueError("Lists 'url' and 'name' must be of equal length.")
    else:
        local_filename = [None for _ in range(len(urls))]

    # only import if async functionality is needed
    import threading as _threading

    thread_counter = 0
    while (thread_counter < len(urls)):
        threads = []
        sub_urls = urls[thread_counter:thread_counter+thread_limit]
        sub_local_filename= local_filename[thread_counter:thread_counter+thread_limit]

        for url, name in zip(sub_urls, sub_local_filename):
            threads.append(_threading.Thread(target=download, args=[url, name, use_proxy, retries]))
            threads[-1].start()
            _time.sleep(time_rest)
        
        for thread in threads:
            thread.join()
        thread_counter += thread_limit
    

def head(url, **kwargs):
    return _requests.head(url, **kwargs)

def post(url:str, data=None, json=None, **kwargs):
    local_file_starts = ['./', 'C:', '/'] 
    if any([url.startswith(i) for i in local_file_starts]):
        raise ValueError("use post_local() for creation of local files.")
        
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
    return _requests.put(url, data=data, **kwargs)

def patch(url, data=None, **kwargs):
    return _requests.patch(url, data=data, **kwargs)

def delete(url, **kwargs):
    return _requests.delete(url, **kwargs)

def options(url, **kwargs):
    return _requests.options(url, **kwargs)

def set_proxies(proxies:list):
    """Lets the user use their own proxies in the library

    Args:
        proxies (list): A list of proxies in the format [['23.144.56.65', '8080'], ...] or ['23.144.56.65:8080', ...]

    Raises:
        Exception: Raises an exception if the argument is not in the correct format
    """
    if (type(proxies) != list):
        raise Exception("Incorrect formatting for setting proxies. Must be [['23.144.56.65', '8080'], ...] or ['23.144.56.65:8080', ...]")
    ProxyList.set_proxies(proxies)

def update_proxies():
    """
    Updates the list of proxy servers.

    This method gets a fresh list of proxy servers from the source website and updates the class variable __PROXY_LIST.
    Existing proxies in the list are removed before the update.

    Note:
        This method should be called periodically to ensure that the list of proxy servers is up-to-date and contains 
        only working proxies.

    Returns:
        None
    """
    ProxyList.update_proxies()

def __grab_thread_wrapper(url:str, payload:list, args, kwargs, use_proxy=False, retries=5, enable_js=False):
    res = get(url, use_proxy=use_proxy, retries=retries, enable_js=enable_js, *args, **kwargs)
    payload.append(res)

def __grab_enable_js(url):
    return _asyncio.get_event_loop().run_until_complete(__grab_enable_js_async(url))

async def __grab_enable_js_async(url):
    browser = await _launch()
    page = await browser.newPage()
    await page.goto(url, waitUntil='networkidle0')
    html = await page.content()    
    await browser.close()
    return html