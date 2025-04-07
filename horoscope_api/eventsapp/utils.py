
from bs4 import BeautifulSoup
import logging
import time
import random
import requests

logger = logging.getLogger(__name__)

def scrape_sulekha_events(city):
    """
    Scrape all events from Sulekha for a given city metro area,
    organized by section/category
    """
    url = f"https://events.sulekha.com/{city.lower()}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://events.sulekha.com/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }
    
    try:
        # Add a small delay to avoid rate limiting
        time.sleep(random.uniform(1, 3))
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        categorized_events = {}
        
        # Find all regular section containers
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
        
        # NEW: Find and scrape the "Upcoming Events" section
        upcoming_events = scrape_upcoming_events(soup, city)
        if upcoming_events:
            categorized_events.update(upcoming_events)
        
        return categorized_events
    
    except requests.RequestException as e:
        logger.error(f"Error fetching events: {e}")
        return {"error": str(e)}

def scrape_upcoming_events(soup, city):
    """
    Scrape the "Upcoming Events" section from the Sulekha website
    """
    try:
        # Find the "Upcoming Events" section
        upcoming_section = soup.select_one("section.global-eventwarp")
        if not upcoming_section:
            logger.warning(f"Could not find 'Upcoming Events' section for {city}")
            return {}
        
        # Extract the section title
        title_elem = upcoming_section.select_one(".discover-titlewarp .maintitle")
        if not title_elem:
            # Try alternative title selector
            title_elem = upcoming_section.select_one(".discover-titlewarp h2.maintitle")
        
        section_title = "Upcoming Events"
        if title_elem:
            section_title = title_elem.text.strip()
        
        # Initialize the events list for this category
        upcoming_events = {section_title: []}
        
        # Find all event cards within the "Upcoming Events" section
        event_articles = upcoming_section.select("article.global-eventlist")
        
        for article in event_articles:
            try:
                event_card_area = article.select_one("section.eventcardarea")
                if event_card_area:
                    event_data = extract_event_data_from_upcoming_card(event_card_area, article)
                    if event_data:
                        upcoming_events[section_title].append(event_data)
            except Exception as e:
                logger.error(f"Error parsing upcoming event card: {e}")
                continue
        
        logger.info(f"Found {len(upcoming_events.get(section_title, []))} events in '{section_title}' section")
        return upcoming_events
    
    except Exception as e:
        logger.error(f"Error scraping upcoming events: {e}")
        return {}

def extract_event_data_from_upcoming_card(card_area, article=None):
    """
    Extract event data from an upcoming event card area
    """
    # Extract basic info
    title_elem = card_area.select_one(".event-info .title h3 a")
    date_elem = card_area.select_one(".event-info .date")
    venue_elem = card_area.select_one(".event-info .location b")
    location_elem = card_area.select_one(".event-info .location a")
    status_elem = card_area.select_one(".event-info .batch")
    image_elem = card_area.select_one(".event-img figure a img")
    
    # Extract event ID and URL from article attributes
    event_id = None
    event_url = None
    
    if article:
        if article.has_attr('id'):
            id_parts = article['id'].split('-')
            if len(id_parts) > 1:
                event_id = id_parts[-1]
        
        if article.has_attr('data-filter-url'):
            event_url = article['data-filter-url']
    
    # Extract performers/lineup
    performers = []
    lineup_elem = card_area.select_one(".event-info .lineup")
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
    
    # Extract date and clean it
    date = "N/A"
    if date_elem:
        date_text = date_elem.text.strip()
        # Remove the SVG icon text if present
        icon_elem = date_elem.select_one("i")
        if icon_elem:
            icon_text = icon_elem.text.strip()
            date_text = date_text.replace(icon_text, "").strip()
        date = date_text
    
    venue = venue_elem.text.strip() if venue_elem else "N/A"
    location = location_elem.text.strip() if location_elem else "N/A"
    status = status_elem.text.strip() if status_elem else "N/A"
    image = image_elem['src'] if image_elem and image_elem.has_attr('src') else None
    
    # Price can be in different locations depending on the card style
    price = "N/A"
    price_elem = card_area.select_one(".actionarea .price b")
    if price_elem:
        price = price_elem.text.strip()
    else:
        # Try alternative price location
        alt_price_elem = card_area.select_one(".event-info .price b")
        if alt_price_elem:
            price = alt_price_elem.text.strip()
    
    # Get action type (Buy Tickets, Register, etc.)
    action_type = "Buy Tickets"
    action_elem = card_area.select_one(".actionarea .action a")
    if action_elem:
        action_text = action_elem.text.strip()
        # Clean up the text by removing whitespace and newlines
        action_type = ' '.join(action_text.split())
    
    # Extract category if available
    category = None
    category_elem = card_area.select_one(".event-info .lineup a[href*='category']")
    if category_elem:
        category = category_elem.text.strip()
    
    return {
        "id": event_id,
        "title": title,
        "link": link,
        "date": date,
        "venue": venue,
        "location": location,
        "price": f"Starts at {price}" if price != "N/A" else "N/A",
        "status": status,
        "category": category,
        "performers": performers if performers else "N/A",
        "image": image,
        "action_type": action_type,
        "event_url": event_url
    }

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
    if date_elem and date_elem.select_one("i"):
        date = date.replace(date_elem.select_one("i").text, "").strip()
    
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
    };

