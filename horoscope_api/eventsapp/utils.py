import requests
from bs4 import BeautifulSoup

def scrape_sulekha_events(city="washington"):
    """
    Scrape events from Sulekha for a given city metro area
    """
    # Format city name properly for URL (replace spaces with hyphens)
    formatted_city = city.lower().replace(" ", "-")
    url = f"https://events.sulekha.com/{formatted_city}-metro-area"
    
    print(f"Scraping URL: {url}")  # Debug statement
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        soup = BeautifulSoup(response.text, 'html.parser')
        events = []
        
        # Find all event cards
        for card in soup.select(".event-card"):
            try:
                # Extract basic info
                title_elem = card.select_one(".event-info .title h3 a")
                date_elem = card.select_one(".event-info .date")
                venue_elem = card.select_one(".event-info .location b")
                location_elem = card.select_one(".event-info .location a")
                price_elem = card.select_one(".event-info .price b")
                status_elem = card.select_one(".event-info .batch")
                image_elem = card.select_one(".event-img figure a img")
                
                # Extract performers/lineup
                performers = []
                lineup_elem = card.select_one(".event-info .lineup")
                if lineup_elem:
                    for artist_link in lineup_elem.select("a"):
                        performers.append(artist_link.text.strip())
                
                # Clean and format extracted data
                title = title_elem.text.strip() if title_elem else "N/A"
                link = f"https://events.sulekha.com{title_elem['href']}" if title_elem and title_elem.has_attr('href') else "#"
                date = date_elem.text.strip() if date_elem else "N/A"
                date = date.replace(date_elem.select_one("i").text if date_elem and date_elem.select_one("i") else "", "").strip()
                venue = venue_elem.text.strip() if venue_elem else "N/A"
                location = location_elem.text.strip() if location_elem else "N/A"
                price = price_elem.text.strip() if price_elem else "N/A"
                status = status_elem.text.strip() if status_elem else "N/A"
                image = image_elem['src'] if image_elem and image_elem.has_attr('src') else None
                
                events.append({
                    "title": title,
                    "link": link,
                    "date": date,
                    "venue": venue,
                    "location": location,
                    "price": f"Starts at {price}" if price != "N/A" else "N/A",
                    "status": status,
                    "performers": performers if performers else "N/A",
                    "image": image
                })
            except Exception as e:
                # Skip this event card if there's an error
                print(f"Error parsing event card: {e}")
                continue
                
        return events
    
    except requests.RequestException as e:
        print(f"Error fetching events: {e}")
        return []