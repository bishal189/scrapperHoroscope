import requests
from bs4 import BeautifulSoup

# base url 
BASE_URL = "https://www.astroved.com"

def scrape_horoscope():
    """ Scrapes all horoscope links and their details """
    url = f"{BASE_URL}/horoscope/"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract all horoscope sign links
        horoscope_links = soup.find_all("a", href=True)
        horoscope_links = [a["href"] for a in horoscope_links if "/horoscopes/daily-horoscope/" in a["href"]]

        results = []
        for link in horoscope_links:
            sign_url = f"{BASE_URL}{link}"
            sign_name = link.split("/")[-1].capitalize() 

            print(f"Fetching {sign_name} Horoscope from {sign_url}")

            # Fetch horoscope details
            horoscope_data = scrape_horoscope_details(sign_url)

            # Append to results
            results.append({"sign": sign_name, "details": horoscope_data})

        return results

    else:
        return {"error": f"Failed to fetch data, status code {response.status_code}"}


def scrape_horoscope_details(url):
    """ Fetches detailed horoscope information from the horoscope page """
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        horoscope_section = soup.find("div", class_="horo-title")

        if not horoscope_section:
            return {"status": "fail", "message": "Horoscope section not found"}

        result = {}

        headers = horoscope_section.find_all("h3")  
        descriptions = horoscope_section.find_all("p")  

        for header, description in zip(headers, descriptions):
            category = header.get_text(strip=True)  
            description_text = description.get_text(strip=True) 
            result[category] = {"description": description_text}

        return result

    else:
        return {"error": f"Failed to fetch data, status code {response.status_code}"}
