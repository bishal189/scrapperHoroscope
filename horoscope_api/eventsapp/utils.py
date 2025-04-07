import requests
from bs4 import BeautifulSoup
import logging
import re
import time
import random
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

def scrape_sulekha_events(city="washington"):
    """
    Scrape all events from Sulekha for a given city metro area,
    organized by section/category
    """
    url = f"https://events.sulekha.com/{city.lower()}-metro-area"
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
        
        # 2. IMPROVED: Find "Events Near [City] Metro Area" section
        events_near_title = f"Events Near {city.title()} Metro Area"
        
        # APPROACH 1: Look for the notitle section that contains the text "Events Near [City] Metro Area"
        notitle_sections = soup.select("section.notitle")
        events_near_section = None
        
        for section in notitle_sections:
            section_text = section.get_text().strip()
            if re.search(r"Events\s+Near\s+.*\s+Metro\s+Area", section_text, re.IGNORECASE):
                events_near_title = section_text
                # The actual events are in the next section with class global-event
                events_near_section = section.find_next_sibling("section.global-eventwarp, section.global-event")
                break
        
        # APPROACH 2: Look directly for the global-eventwarp section
        if not events_near_section:
            global_event_sections = soup.select("section.global-eventwarp, section.global-event")
            for section in global_event_sections:
                # Check if there's a preceding section with the "Events Near" text
                prev_section = section.find_previous_sibling("section")
                if prev_section and "Events Near" in prev_section.get_text():
                    events_near_section = section
                    events_near_title = prev_section.get_text().strip()
                    break
        
        # APPROACH 3: Look for the section that contains both the title and events
        if not events_near_section:
            for section in soup.select("section.global-eventwarp"):
                # Check if this section contains a div with the "Events Near" text
                title_divs = section.select("div")
                for div in title_divs:
                    if "Events Near" in div.get_text() and city.lower() in div.get_text().lower():
                        events_near_section = section
                        events_near_title = div.get_text().strip()
                        break
                if events_near_section:
                    break
        
        # Process the Events Near section if found
        if events_near_section:
            # Make sure we have the category in our events dictionary
            if events_near_title not in categorized_events:
                categorized_events[events_near_title] = []
            
            # Extract events from different possible structures
            
            # Structure 1: Event cards within this section
            event_cards = events_near_section.select(".event-card")
            for card in event_cards:
                try:
                    event_data = extract_event_data_from_card(card)
                    if event_data:
                        categorized_events[events_near_title].append(event_data)
                except Exception as e:
                    logger.error(f"Error parsing event card in Events Near section: {e}")
                    continue
            
            # Structure 2: Articles within global-event section
            event_articles = events_near_section.select("article.global-eventlist")
            for article in event_articles:
                try:
                    event_data = extract_event_data_from_nearby_article(article)
                    if event_data:
                        categorized_events[events_near_title].append(event_data)
                except Exception as e:
                    logger.error(f"Error parsing nearby event article: {e}")
                    continue
            
            # Structure 3: Event card areas within articles
            event_card_areas = events_near_section.select("article section.eventcardarea")
            if event_card_areas and not categorized_events[events_near_title]:
                for card_area in event_card_areas:
                    try:
                        event_data = extract_event_data_from_card_area(card_area)
                        if event_data:
                            categorized_events[events_near_title].append(event_data)
                    except Exception as e:
                        logger.error(f"Error parsing event card area: {e}")
                        continue
                    
            # Log what we found
            logger.info(f"Found {len(categorized_events.get(events_near_title, []))} events in '{events_near_title}' section")
        else:
            logger.warning(f"Could not find 'Events Near {city} Metro Area' section")
        
        return categorized_events
    
    except requests.RequestException as e:
        logger.error(f"Error fetching events: {e}")
        return {"error": str(e)}

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
    }

def extract_event_data_from_nearby_article(article):
    """
    Extract event data from an article in the "Events Near" section
    """
    # Get the event card area
    event_card_area = article.select_one("section.eventcardarea")
    if not event_card_area:
        return None
    
    return extract_event_data_from_card_area(event_card_area, article)

def extract_event_data_from_card_area(card_area, article=None):
    """
    Extract event data from an event card area, optionally using article data
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
    
    # Extract category/performer info
    category = None
    performer = None
    performers = []
    
    lineup_elem = card_area.select_one(".event-info .lineup")
    if lineup_elem:
        for artist_link in lineup_elem.select("a"):
            link_href = artist_link.get('href', '')
            if 'artist' in link_href:
                performers.append(artist_link.text.strip())
            elif not category and 'category' in link_href or link_href == '/':
                category = artist_link.text.strip()
    
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
    action_elem = card_area.select_one(".action a, .actionarea .action a")
    if action_elem:
        action_text = action_elem.text.strip()
        # Clean up the text by removing whitespace and newlines
        action_type = ' '.join(action_text.split())
    
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
        "performers": performers if performers else (
            [category] if category else "N/A"
        ),
        "image": image,
        "action_type": action_type,
        "event_url": event_url
    }