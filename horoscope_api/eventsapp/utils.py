import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def scrape_sulekha_events(city):
    """
    Scrape all events from Sulekha for a given city metro area,
    organized by section/category
    """
    url = f"https://events.sulekha.com/{city.lower()}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        categorized_events = {}
        
        # 1. Find all regular section containers
        section_containers = soup.select("section.container.container-max")
        
        for section in section_containers:
            # Extract section title
            title_elem = section.select_one(".title h2")
            if not title_elem:
                # Try alternative title selector for "Dance Events" type sections
                title_elem = section.select_one(".discover-titlewarp .title")
            
            section_title = "Uncategorized"
            if title_elem:
                section_title = title_elem.text.strip()
            
            # Initialize list for this category if it doesn't exist
            if section_title not in categorized_events:
                categorized_events[section_title] = []
            
            # Find all event cards within this section
            for card in section.select(".event-card"):
                try:
                    event_data = extract_event_data_from_card(card)
                    if event_data:
                        categorized_events[section_title].append(event_data)
                except Exception as e:
                    # Skip this event card if there's an error
                    logger.error(f"Error parsing event card: {e}")
                    continue
        
        # 2. Find "Events Near City Metro Area" section - Fixed approach
        nearby_title = f"Events Near {city.title()} Metro Area"
        
        # Look for sections that might contain nearby events
        nearby_sections = soup.select("section.global-eventwarp")
        
        for nearby_wrapper in nearby_sections:
            # Find the heading that contains the "Events Near" text
            heading_elements = nearby_wrapper.select("h2, h3, h4")
            
            for heading in heading_elements:
                if nearby_title in heading.text:
                    section_title = heading.text.strip()
                    
                    # Initialize list for this category
                    if section_title not in categorized_events:
                        categorized_events[section_title] = []
                    
                    # Find the container with the events
                    # This might be a sibling or child of the heading's parent
                    event_container = nearby_wrapper.select_one("section.global-event") or heading.parent.find_next_sibling("section")
                    
                    if event_container:
                        # Find all event articles within this section
                        event_articles = event_container.select("article.global-eventlist")
                        
                        if not event_articles:
                            # Try alternative selector if needed
                            event_articles = event_container.select("article")
                        
                        for article in event_articles:
                            try:
                                event_data = extract_event_data_from_nearby_article(article)
                                if event_data:
                                    categorized_events[section_title].append(event_data)
                            except Exception as e:
                                # Skip this event article if there's an error
                                logger.error(f"Error parsing nearby event article: {e}")
                                continue
                    
                    # Break after finding and processing the correct heading
                    break
        
        return categorized_events
    
    except requests.RequestException as e:
        logger.error(f"Error fetching events: {e}")
        return {}

def extract_event_data_from_card(card):
    """
    Extract event data from a regular event card
    """
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
    
    # Handle link extraction
    link = "#"
    if title_elem and title_elem.has_attr('href'):
        href = title_elem['href']
        link = f"https://events.sulekha.com{href}" if href.startswith('/') else href
    
    date = date_elem.text.strip() if date_elem else "N/A"
    date = date.replace(date_elem.select_one("i").text if date_elem and date_elem.select_one("i") else "", "").strip()
    venue = venue_elem.text.strip() if venue_elem else "N/A"
    location = location_elem.text.strip() if location_elem else "N/A"
    price = price_elem.text.strip() if price_elem else "N/A"
    status = status_elem.text.strip() if status_elem else "N/A"
    image = image_elem['src'] if image_elem and image_elem.has_attr('src') else None
    
    # Get action type (Buy Tickets, Register, etc.)
    action_elem = card.select_one(".action a")
    action_type = action_elem.text.strip() if action_elem else "Buy Tickets"
    
    return {
        "title": title,
        "link": link,
        "date": date,
        "venue": venue,
        "location": location,
        "price": f"Starts at {price}" if price != "N/A" else "N/A",
        "status": status,
        "performers": performers if performers else "N/A",
        "image": image,
        "action_type": action_type.strip() if action_type else "Buy Tickets"
    }

def extract_event_data_from_nearby_article(article):
    """
    Extract event data from an article in the "Events Near" section
    """
    # Get the event card area
    event_card_area = article.select_one("section.eventcardarea")
    if not event_card_area:
        return None
    
    # Extract basic info
    title_elem = event_card_area.select_one(".event-info .title h3 a")
    date_elem = event_card_area.select_one(".event-info .date")
    venue_elem = event_card_area.select_one(".event-info .location b")
    location_elem = event_card_area.select_one(".event-info .location a")
    status_elem = event_card_area.select_one(".event-info .batch")
    image_elem = event_card_area.select_one(".event-img figure a img")
    
    # Extract performers/lineup
    performers = []
    lineup_elem = event_card_area.select_one(".event-info .lineup")
    if lineup_elem:
        for artist_link in lineup_elem.select("a"):
            performers.append(artist_link.text.strip())
    
    # Extract event ID from data attributes
    event_id = None
    if article.has_attr('id'):
        id_parts = article['id'].split('-')
        if len(id_parts) > 1:
            event_id = id_parts[-1]
    
    # Extract event URL from data attributes
    event_url = None
    if article.has_attr('data-filter-url'):
        event_url = article['data-filter-url']
    
    # Clean and format extracted data
    title = title_elem.text.strip() if title_elem else "N/A"
    
    # Handle link extraction
    link = "#"
    if title_elem and title_elem.has_attr('href'):
        href = title_elem['href']
        link = f"https://events.sulekha.com{href}" if href.startswith('/') else href
    
    date = date_elem.text.strip() if date_elem else "N/A"
    date = date.replace(date_elem.select_one("i").text if date_elem and date_elem.select_one("i") else "", "").strip()
    venue = venue_elem.text.strip() if venue_elem else "N/A"
    location = location_elem.text.strip() if location_elem else "N/A"
    status = status_elem.text.strip() if status_elem else "N/A"
    image = image_elem['src'] if image_elem and image_elem.has_attr('src') else None
    
    # Price can be in different locations depending on the card style
    price = "N/A"
    price_elem = event_card_area.select_one(".actionarea .price b")
    if price_elem:
        price = price_elem.text.strip()
    else:
        # Try alternative price location
        alt_price_elem = event_card_area.select_one(".event-info .price b")
        if alt_price_elem:
            price = alt_price_elem.text.strip()
    
    # Get action type (Buy Tickets, Register, etc.)
    action_elem = event_card_area.select_one(".action a")
    action_type = action_elem.text.strip() if action_elem else "Buy Tickets"
    
    return {
        "id": event_id,
        "title": title,
        "link": link,
        "date": date,
        "venue": venue,
        "location": location,
        "price": f"Starts at {price}" if price != "N/A" else "N/A",
        "status": status,
        "performers": performers if performers else "N/A",
        "image": image,
        "action_type": action_type.strip() if action_type else "Buy Tickets",
        "event_url": event_url
    }

