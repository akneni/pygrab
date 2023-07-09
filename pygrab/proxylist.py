from random import choice as _choice
import asyncio as _asyncio
from pyppeteer import launch as _launch


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
            raise Exception(f'{err}\n\nThere seems to have been an error with finding a proxy IP. Please note that free proxies may not be reliable.')

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