from .warning import Warning
from .session import Session
from .pygrab import get
from urllib.parse import urlparse
from collections import defaultdict

class SessionDict:
    session_dict = {}

    def get_session(cls, domain):
        if cls.session_dict.get(domain) is None:
            cls.session_dict[domain] = Session()
        return cls.session_dict[domain]

class GroupedUrls:
    def __init__(self, grouped_urls) -> None:
        self.grouped_urls = grouped_urls
        self.length = sum([len(v) for v in self.grouped_urls.values()])
    
    def values(self):
        return self.grouped_urls.values()
    def keys(self):
        return self.grouped_urls.keys()
    def items(self):
        return self.grouped_urls.items()

    def __getattribute__(self, __name: str):
        return self.grouped_urls[__name]
    
    def __getitem__(self, x):
        if x >= self.length:
            raise IndexError(f'Index {x} out of bounds for length {self.length}')
        while x < 0:
            x = self.length+x
        
        counter = 0
        for v in self.grouped_urls.values():
            if counter + len(v) > x:
                return v[x-counter]
            else:
                counter += len(v)
    
    def __len__(self):
        return self.length


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

    return GroupedUrls(dict(domain_groups))


# Helper function for get_async with auto session support
def grab_thread_wrapper_autosession(start, num, domain, urls:GroupedUrls, timeout:int, payload:dict, args, kwargs):
    for i in range (start, start+num):
        if i == len(urls[domain]):
            break
    
        url = urls[domain][i]
        try:
            if len(urls[domain]) > 2:
                s = SessionDict.get_session(domain)
                payload[url] = s.get(url, enable_js=False, ignore_tor_rotations=True, timeout=timeout, *args, **kwargs)
            else:
                payload[url] = get(url, enable_js=False, ignore_tor_rotations=True, timeout=timeout, *args, **kwargs)
        except Exception as err:
            Warning.raiseWarning(f"Warning: Failed to grab {url} | {err}")







"""   

Using a single session for each domain results in a significant speed up for sync requests but results in no noticible speed up for async requests. 
This may be because the connection (including the TLS handshake) is not preserves for a single session when threading is introduced. 

look at aiohttp for a solution to this

UPDATE: aiohttp didn't work


"""