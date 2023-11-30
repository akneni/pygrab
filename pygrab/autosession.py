from .warning import Warning
from .session import Session
import time
import threading
import requests
import re
from urllib.parse import urlparse
from collections import defaultdict


class autosession:
    CUTOFF = 2           # All domains with greater than CUTOFF urls will get autosessioned. 
    REQ_MULTIPLE = 10    # Each thread will create a session and send out REQ_MULTIPLE*batch_size requests

    @staticmethod
    def pygrabget(url:str, timeout:int=None, *args, **kwargs): 
        """
        Gets the content at the specified URL.

        Parameters:
            url (str): The URL to get.
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
        
        timeout = 5 if timeout is None else timeout

        local_file_starts = ['./', 'C:', '/'] 
        url_file_starts = ['http', 'ftp:', 'mailto:']
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?::\d{1,5})?$', url):
            url = "http://" + url
        if any([url.startswith(i) for i in local_file_starts]):
            raise ValueError ("Url must start with http. use get_local() for local requests.")
        elif any([url.startswith(i) for i in url_file_starts]):
            try:
                return requests.get(url, timeout=timeout, *args, **kwargs)
            except requests.exceptions.InvalidSchema as err:
                if 'Missing dependencies for SOCKS support'.lower() in str(err).lower():
                    raise ModuleNotFoundError("Required module 'PySocks' not found.")
                raise requests.exceptions.InvalidSchema(err)

        raise ValueError(f"Invalid url or IP address: {url}")

    @staticmethod
    def groupby_domain(urls:list[str]) -> dict[str:list[str]]:
        """
        Groups a list of URLs by their domain.

        This function takes a list of URLs and groups them into a dictionary. 
        Each key in the dictionary is a domain, and the corresponding value is a list of URLs that belong to that domain. 
        The function uses Python's urllib.parse to extract the domain from each URL.

        Parameters:
        urls (list of str): A list of URLs (strings) to be grouped.

        Returns:
        dict: A dictionary where each key is a domain (str) and each value is a list of URLs (list of str) belonging to that domain.
        """
        domain_groups = defaultdict(list)
        for url in urls:
            domain = urlparse(url).netloc
            domain_groups[domain].append(url)

        return dict(domain_groups)

    @staticmethod
    def gen_partition(grouped_urls:dict[str:list[str]], cutoff:int, batch_size:int, req_multiple:int) -> list[tuple]:
        res = []

        last_domain = next(reversed(grouped_urls))
        counter = 0
        domain_iter = iter(grouped_urls)
        curr_domain = next(domain_iter)
        while 1:
            if len(grouped_urls[curr_domain]) > cutoff:
                res.append(
                    (counter, batch_size*req_multiple, curr_domain)
                )
                counter += batch_size*req_multiple
            else:
                res.append(
                    (counter, batch_size, curr_domain)
                )
                counter += batch_size
            
            if counter >= len(grouped_urls[curr_domain]):
                if curr_domain == last_domain:
                    break
                curr_domain = next(domain_iter)
                counter = 0
        return res

    @staticmethod
    def get_async_autosession(urls:list[str], timeout:int, time_rest:float, payload:dict, *args, **kwargs):
        grouped_urls = autosession.groupby_domain(urls)

        partition = autosession.gen_partition(grouped_urls, autosession.CUTOFF, 1, autosession.REQ_MULTIPLE)
        threads:list[threading.Thread] = []
        for i in range(len(partition)):
            threads.append(
                threading.Thread(target=autosession.autosession_threadfunc, args=[partition[i], grouped_urls, timeout, payload, args, kwargs])
            )
            threads[-1].start()
            time.sleep(time_rest)
        
        for i in threads:
            i.join()

    @staticmethod
    def autosession_threadfunc(partition, grouped_urls, timeout:int, payload:dict, args, kwargs):
        start, num, domain = partition

        if len(grouped_urls[domain]) > autosession.CUTOFF:
            s = Session(use_tor=False)

        for i in range(start, start+num):
            if i >= len(grouped_urls[domain]):
                break
            url = grouped_urls[domain][i]
            try:
                if len(grouped_urls[domain]) > autosession.CUTOFF:
                    payload[url] = s.get(url, timeout=timeout, *args, **kwargs)
                else:
                    payload[url] = autosession.pygrabget(url, timeout=timeout, *args, **kwargs)
            except Exception as err:
                Warning.raiseWarning(f"Warning: Failed to grab {url} | {err}")






"""   

Notes on auto session: 

Using a single session for each domain results in a significant speed up for sync requests but results in no noticible speed up for async requests. 
This may be because the connection (including the TLS handshake) is not preserves for a single session when threading is introduced. 

look at aiohttp for a solution to this

UPDATE: aiohttp didn't work


Creating a session in each individual thread seems to provide a reliable performence increase. 
The optimal value for REQ_MULTIPLE seems to be 10. 
The optimal value for REQ_MULTIPLE seems to be 3 when using the tor network. 

This performence increase seems to only be reliable when requests are NOT being routed through the tor service. 

"""