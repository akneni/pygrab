from .warning import Warning
from .tor import Tor
from pyppeteer import launch as _launch
import asyncio as _asyncio
import atexit as _atexit
import nest_asyncio as _nest_asyncio
_nest_asyncio.apply()


class js_scraper:
    browser = None
    browser_torred = False

    @classmethod
    async def __get_browser(cls):
        if cls.browser is None:
            if Tor.tor_status():
                cls.browser = await _launch(
                    args=[f"--proxy-server=socks5://127.0.0.1:9050"]
                )
                cls.browser_torred = True
            else:
                cls.browser = await _launch()
            _atexit.register(cls.browser.close)
        elif Tor.tor_status() and not cls.browser_torred:
            if cls.browser is not None: await cls.browser.close()
            cls.browser = await _launch(
                args=[f"--proxy-server=socks5://127.0.0.1:9050"]
            )
            cls.browser_torred = True
        elif not Tor.tor_status() and cls.browser_torred:
            if cls.browser is not None: await cls.browser.close()
            cls.browser = await _launch()
            cls.browser_torred = False
        return cls.browser

    @classmethod
    async def __pyppeteer_kernel(cls, url):
        browser = await cls.__get_browser()
        page = await browser.newPage()
        try:
            await page.goto(url, waitUntil='networkidle0', options={"timeout":10_000})
            html = await page.content()
        finally:
            await page.close()
        return html

    @classmethod
    def pyppeteer_get(cls, url):
        # Test it
        loop = _asyncio.get_event_loop()
        result = loop.run_until_complete(cls.__pyppeteer_kernel(url))
        return result

    @classmethod
    async def get_page_content(cls, browser, url):
        page = await browser.newPage()
        try:
            await page.goto(url, waitUntil='networkidle0', options={"timeout":10_000})
            html = await page.content()
        finally:
            await page.close()
        return html

    @classmethod
    async def scrape_all(cls, urls) -> dict:
        browser = await cls.__get_browser()
        tasks = [cls.get_page_content(browser, url) for url in urls]
        res = await _asyncio.gather(*tasks, return_exceptions=True)

        res_dict = {}
        for i, url in zip(res, urls):
            if isinstance(i, Exception):
                Warning.raiseWarning(f"Waring: error for {url}: {i}")
            else:
                res_dict[url] = i
        return res_dict

    @classmethod
    def pyppeteer_get_async(cls, urls) -> dict:
        return _asyncio.run(cls.scrape_all(urls))
