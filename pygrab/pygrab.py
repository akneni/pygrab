# Author: Anish Kanthamneni
import requests as _requests
from pyppeteer import launch as _launch
from random import choice as _choice
import asyncio as _asyncio

class ProxyList():
    PROXY_LIST = []
    
    @classmethod
    def is_empty(cls):
        return cls.PROXY_LIST == []
    
    @classmethod
    def get_random(cls):
        
        high_quality = []
        
        for ip in cls.PROXY_LIST:
            if ip[4] == 'Transparent':
                continue
            elif int(ip[-1]) < 550:
                continue
            high_quality.append(ip)
        
        if high_quality != []:
            x = _choice(high_quality)
            print (x)
            print (f'length: {len(cls.PROXY_LIST)}')
            return x
        return _choice(cls.PROXY_LIST)
    
    @classmethod
    def update_proxies(cls):
        while (cls.PROXY_LIST != []): cls.PROXY_LIST.pop(0)
        cls.gen_proxies()
    
    @classmethod
    async def grab_proxies_async(cls):
        browser = await _launch()
        page = await browser.newPage()
        await page.goto('https://proxyscrape.com/free-proxy-list', waitUntil='networkidle0')
        html = await page.content()    
        await browser.close()
        return html
    
    @classmethod
    def gen_proxies(cls):
        def parse(row):
            row = row.split('</td><td>')
            row[-1] = row[4].split('>')[-1].replace('ms', '')
            row[4] = row[4].split('<')[0]
            return row
        try:
            raw_html = _asyncio.get_event_loop().run_until_complete(cls.grab_proxies_async())
            html = raw_html.split('</thead>')[1]
            html = html.split('<tr><td>')
            html.pop(0)
            cls.PROXY_LIST = [parse(i) for i in html]
            
        except Exception as err:
            raise Exception(f'{err}\n\n{raw_html}\n\nThere seems to have been an error with finding a proxy IP. Please note that free proxies may not be reliable.')

    @classmethod
    def set_proxies(cls, lst):
        if len(lst) == 0: 
            cls.PROXY_LIST = []
            return
        
        if type(lst[0]) == list:
            lst[0], lst[1] = str(lst[0]), str(lst[1])
            for i in range (len(cls.PROXY_LIST)):
                if ('.' not in lst[i][0]):
                    raise Exception("Incorrect formatting for setting proxies. Must be [['23.144.56.65', '8080'], ...] or ['23.144.56.65:8080', ...]")
                cls.PROXY_LIST.append(lst[i])
        elif type(lst[0]) == str:
            for i in range (len(cls.PROXY_LIST)):
                if '://' in lst[0]:
                    lst[0] = lst[0].split('://')[1]
                if ('.' not in lst[i] or ':' not in lst[i]):
                    raise Exception("Incorrect formatting for setting proxies. Must be [['23.144.56.65', '8080'], ...] or ['23.144.56.65:8080', ...]")
                    
                cls.PROXY_LIST.append(lst[i].split(':'))
        raise Exception("Incorrect formatting for setting proxies. Must be [['23.144.56.65', '8080'], ...] or ['23.144.56.65:8080', ...]")




def get(url: str, use_proxy=False, retries=5, encoding='utf-8', enable_js=False, *args, **kwargs): 
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
    """
    local_file_starts = ['./', 'C:', '/'] 
    url_file_starts = ['http', 'ftp:', 'mailto:']
    if any([url.startswith(i) for i in local_file_starts]):
        return __local_grab(url, encoding=encoding)
    elif any([url.startswith(i) for i in url_file_starts]):
        if encoding != 'utf-8':
            raise Exception("'encoding' argument is only relevent to grabbing local files.")
        
        if enable_js:
            return __grab_enable_js(url)
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
    
def get_async(urls, use_proxy=False, retries=5, encoding='utf-8', enable_js=False, time_rest=0, *args, **kwargs) -> list:
    """
    Gets multiple URLs asynchronously.

    This function sends HTTP requests to a list of URLs in separate threads, allowing for concurrent HTTP requests.
    The function returns a list of responses from the grabbed URLs.

    Args:
        urls (list): A list of URLs to grab.
        use_proxy (bool, optional): If True, uses a proxy for the HTTP requests. Defaults to False.
        retries (int, optional): The number of times to retry the HTTP request in case of failure. Defaults to 5.
        time_rest (int, optional): The time in seconds to wait between starting each thread. Defaults to 0.
        *args: Variable length argument list to pass to the get function.
        **kwargs: Arbitrary keyword arguments to pass to the get function.

    Returns:
        list: A list of responses from the grabbed URLs.
    """
    # only import if async functionality is needed
    import threading as _threading
    import time as _time
    if type(urls) == str:
        return [get(urls, use_proxy=use_proxy, retries=retries, encoding=encoding, enable_js=enable_js, *args, **kwargs)]

    result = []
    threads = []
    for url in urls:
        threads.append(_threading.Thread(target=__grab_thread_wrapper, args=[url, result, args, kwargs, use_proxy, retries, enable_js]))
        threads[-1].start()
        _time.sleep(time_rest)
    
    for thread in threads:
        thread.join()
        
    return result

def download(url: str, name:str=None, use_proxy=False, retries=5) -> None:
    if '.' not in url:
        raise Exception("Argument 'url' needs a filepath extention")
    

    if name is not None:
        if '.' not in name:
            if '.' in url:
                name += '.' + url.split('.')[-1]
        elif name.split('.')[-1] != url.split('.')[-1]:
            raise Exception ("File extentions for 'url' and 'name' must match.")
    elif '/' in url:
        name = url.split('/')[-1]
    else:
        name=url
        

    response = get(url, use_proxy=use_proxy, retries=retries)

    if response.status_code == 200:
        with open(name, 'wb') as f:
            f.write(response.content)
    else:
        raise Exception(f"Error fetching url. Status code - {response.status_code}")

def download_async(urls:list, names:list=None, use_proxy=False, retries=5, time_rest=0) -> None:
    if names is not None:
        if len(urls) != len(names):
            raise Exception("Lists 'url' and 'name' must be of equal length.")
    else:
        names = [None for _ in range(len(urls))]

    # only import if async functionality is needed
    import threading as _threading
    import time as _time

    threads = []
    for url, name in zip(urls, names):
        threads.append(_threading.Thread(target=download, args=[url, name, use_proxy, retries]))
        threads[-1].start()
        _time.sleep(time_rest)
    
    for thread in threads:
        thread.join()
    

def head(url, **kwargs):
    return _requests.head(url, **kwargs)

def post(url:str, data=None, json=None, local_save_type:str=None, encoding:str='utf-8', **kwargs):
    local_file_starts = ['./', 'C:', '/'] 
    
    if any([url.startswith(i) for i in local_file_starts]):
        if local_save_type is None: local_save_type = 'w'
        
        with open(url, local_save_type, encoding=encoding) as f:
            f.write(data)
    else:
        if (local_save_type is not None or encoding != 'utf-8'):
            raise Exception("Arguments 'local_save_type' and 'encoding' are only relevent for posting to local files.")
        
        return _requests.post(url, data=data, json=json, **kwargs)

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

def __local_grab(dir: str, encoding='utf-8'):
    acceptableRegFiles = ['.txt', '.py', '.js', '.c', '.html', '.css', '.xml', '.md', '.yaml', '.yml', '.ipynb']
    acceptableImgFiles = ['.png', '.jpg']
    
    if any([dir.endswith(i) for i in acceptableRegFiles]):
        with open(dir, 'r', encoding=encoding) as f:
            data = f.read()
        return data
    elif dir.endswith('.csv'):
        with open(dir, 'r', encoding=encoding) as f:
            data = f.read().strip().split("\n")
        data = [i.split(",") for i in data ]
        return data
    if any([dir.endswith(i) for i in acceptableImgFiles]):
        with open(dir, 'rb') as f:
            data = f.read()
        return data

    raise Exception(f"File type not supported: {dir}")

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