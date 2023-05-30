from pygrab import ProxyList
import requests
import pygrab
import aiohttp
import asyncio
import time
from pyppeteer import launch


def gen_dict(ip, port=None):
    ip = ip.strip()
    if port is None: 
        port = ip.split(':')[1]
        ip = ip.split(':')[0]

    return {
        'http': f'http://{ip}:{port}',
        'https': f'{ip}:{port}'
    }

# var = requests.get('https://google.com', proxies=gen_dict('158.160.56.149:8080')).text


# print (var[0:600])



async def main():
    browser = await launch()
    page = await browser.newPage()
    await page.goto('https://proxyscrape.com/free-proxy-list', waitUntil='networkidle0')
    html = await page.content()
    # print(html)
    
    # with open('thing.txt', 'w', encoding='utf-8') as f:
    #     f.write(str(html))
    
    await browser.close()
    
    return html

var = asyncio.get_event_loop().run_until_complete(main())
print (var)
