from pyppeteer import launch as _launch
import asyncio as _asyncio
import nest_asyncio as _nest_asyncio
_nest_asyncio.apply()


class js_scraper:
    @classmethod
    async def __pyppeteer_kernel(cls, url):
        browser = await _launch()
        page = await browser.newPage()
        await page.goto(url, waitUntil='networkidle0')
        html = await page.content()
        await browser.close()
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
        await page.goto(url, waitUntil='networkidle0')
        html = await page.content()
        await page.close()
        return html

    @classmethod
    async def scrape_all(cls, urls):
        browser = await _launch()
        try:
            tasks = [cls.get_page_content(browser, url) for url in urls]
            return await _asyncio.gather(*tasks)
        finally:
            await browser.close()

    @classmethod
    def pyppeteer_get_async(cls, urls):
        return _asyncio.run(cls.scrape_all(urls))
