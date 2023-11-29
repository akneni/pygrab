from .warning import Warning
from .session import Session
from .pygrab import get as pygrabget
import time
import threading
from urllib.parse import urlparse
from collections import defaultdict


CUTOFF = 2           # All domains with greater than CUTOFF urls will get autosessioned. 
REQ_MULTIPLE = 10    # Each thread will create a session and send out REQ_MULTIPLE*batch_size requests

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

def get_async_autosession(urls:list[str], timeout:int, time_rest:float, *args, **kwargs):
    res = {url:None for url in urls}
    grouped_urls = groupby_domain(urls)

    partition = gen_partition(grouped_urls, CUTOFF, 1, REQ_MULTIPLE)
    threads:list[threading.Thread] = []
    for i in range(len(partition)):
        threads.append(
            threading.Thread(target=autosession_threadfunc, args=[partition[i], grouped_urls, timeout, res, args, kwargs])
        )
        threads[-1].start()
        time.sleep(time_rest)
    
    for i in threads:
        i.join()
        
    return res

def autosession_threadfunc(partition, grouped_urls, timeout:int, payload:dict, args, kwargs):
    start, num, domain = partition

    if len(grouped_urls[domain]) > CUTOFF:
        s = Session(use_tor=False)

    for i in range(start, start+num):
        if i >= len(grouped_urls[domain]):
            break
        url = grouped_urls[domain][i]
        try:
            if len(grouped_urls[domain]) > CUTOFF:
                payload[url] = s.get(url, timeout=timeout, *args, **kwargs)
            else:
                payload[url] = pygrabget(url, timeout=timeout, ignore_tor_rotations=True *args, **kwargs)
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