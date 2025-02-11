import aiohttp
import asyncio
from bs4 import BeautifulSoup

BASE_URL = "https://www.astroved.com/horoscope/"

async def fetch(session, url):
    """ Fetch page content asynchronously with optimized headers """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }
    async with session.get(url, headers=headers) as response:
        return await response.text() if response.status == 200 else None

async def scrape_horoscope():
    """ Scrapes all horoscope signs and their daily predictions concurrently """

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=50)) as session:
        page_content = await fetch(session, BASE_URL)

        if not page_content:
            return {"error": "Failed to fetch the main horoscope page"}

        soup = BeautifulSoup(page_content, "lxml")  # Use `lxml` for fast parsing
        horoscope_sections = soup.find_all("div", class_="m-horo-contentsec")

        results = []

        for section in horoscope_sections:
            # Extract Horoscope Sign
            sign_element = section.find("p", class_="m-horo-gradient")
            sign_name = sign_element.text.strip() if sign_element else "Unknown Sign"

            # Extract Horoscope Prediction
            description_element = section.find("div", class_="m-horo-content").find("p")
            description = description_element.text.strip() if description_element else "No prediction available"

            results.append({"sign": sign_name, "prediction": description})

        return results

def get_fresh_horoscope():
    """ Runs the scraper fresh every request without caching """
    
    # Run asynchronous scraping in a synchronous environment
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    horoscopes = loop.run_until_complete(scrape_horoscope())

    return {"data": horoscopes,}  
