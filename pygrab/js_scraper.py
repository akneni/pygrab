from .warning import Warning
from .tor import Tor

# Include this because pyppeteer is often a buggy library and will often crash on import
# Switch to new library soon
try:
    from pyppeteer import launch as _launch
    pyppeteer_working = True
except Exception:
    pyppeteer_working = False


import asyncio as _asyncio
import atexit as _atexit
import nest_asyncio as _nest_asyncio
_nest_asyncio.apply()


class js_scraper:
    browser_reg = None
    browser_tor = None
    cleanup_registered = False

    @classmethod
    def __browser_cleanup(cls):
        if cls.browser_reg is not None:
            _asyncio.run(cls.browser_reg.close())
        if cls.browser_tor is not None:
            _asyncio.run(cls.browser_tor.close())

    @classmethod
    async def __get_browser_reg(cls):
        if cls.browser_reg is None:
            cls.browser_reg = await _launch()
        return cls.browser_reg

    @classmethod
    async def __get_browser_tor(cls):
        if not Tor.tor_status():
            Tor.start_tor()
        if cls.browser_tor is None:
            cls.browser_tor = await _launch(
                args=["--proxy-server=socks5://127.0.0.1:9050"]
            )
        return cls.browser_tor

    @classmethod
    async def __get_browser(cls, use_tor=None):
        if use_tor is None:
            use_tor = Tor.tor_status()
        
        if not cls.cleanup_registered:
            _atexit.register(cls.__browser_cleanup)
            cls.cleanup_registered = True

        return await (cls.__get_browser_tor() if (use_tor) else cls.__get_browser_reg())

    @classmethod
    async def __pyppeteer_kernel(cls, url, use_tor:bool=None, timeout:int=20):
        browser = await cls.__get_browser(use_tor)
        page = await browser.newPage()
        try:
            await page.goto(url, waitUntil='networkidle0', options={"timeout":timeout*1000})
            html = await page.content()
        finally:
            await page.close()
        return html

    @classmethod
    def pyppeteer_get(cls, url, use_tor:bool=None, timeout:int=20):
        # Test it
        if not pyppeteer_working:
            return None
        loop = _asyncio.get_event_loop()
        result = loop.run_until_complete(cls.__pyppeteer_kernel(url, use_tor, timeout))
        return result

    @classmethod
    async def get_page_content(cls, browser, url, timeout:int=20):
        page = await browser.newPage()
        try:
            await page.goto(url, waitUntil='networkidle0', options={"timeout":timeout*1000})
            html = await page.content()
        finally:
            await page.close()
        return html

    @classmethod
    async def scrape_all(cls, urls, use_tor=None, timeout:int=20) -> dict:
        browser = await cls.__get_browser(use_tor)
        tasks = [cls.get_page_content(browser, url, timeout) for url in urls]
        res = await _asyncio.gather(*tasks, return_exceptions=True)

        res_dict = {}
        for i, url in zip(res, urls):
            if isinstance(i, Exception):
                Warning.raiseWarning(f"Waring: error for {url}: {i}")
            else:
                res_dict[url] = i
        return res_dict

    @classmethod
    def pyppeteer_get_async(cls, urls, use_tor=None, timeout:int=20) -> dict:
        if not pyppeteer_working:
            return None
        return _asyncio.run(cls.scrape_all(urls, use_tor=use_tor, timeout=timeout))
