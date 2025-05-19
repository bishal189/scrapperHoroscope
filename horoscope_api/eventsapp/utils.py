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

        soup = BeautifulSoup(response.text, "html.parser")
        categorized_events = {}

        # Find all regular section containers
        section_containers = soup.select("section.container.container-max")

        for section in section_containers:
            # Extract section title
            title_elem = section.select_one(".title h2")
            if not title_elem:
                # Try alternative title selector for "Dance Events" type sections
                title_elem = section.select_one(".discover-titlewarp .title")

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
                    event_data = extract_event_data_from_upcoming_card(
                        event_card_area, article
                    )
                    if event_data:
                        upcoming_events[section_title].append(event_data)
            except Exception as e:
                logger.error(f"Error parsing upcoming event card: {e}")
                continue

        logger.info(
            f"Found {len(upcoming_events.get(section_title, []))} events in '{section_title}' section"
        )
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
        if article.has_attr("id"):
            id_parts = article["id"].split("-")
            if len(id_parts) > 1:
                event_id = id_parts[-1]

        if article.has_attr("data-filter-url"):
            event_url = article["data-filter-url"]

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
    if title_elem and title_elem.has_attr("href"):
        href = title_elem["href"]
        link = f"https://events.sulekha.com{href}" if href.startswith("/") else href

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
    image = image_elem["src"] if image_elem and image_elem.has_attr("src") else None

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
        action_type = " ".join(action_text.split())

    # Extract category if available
    category = None
    category_elem = card_area.select_one(".event-info .lineup a[href*='category']")
    if category_elem:
        category = category_elem.text.strip()

    # Get comprehensive event details including description and venue details
    event_details_data = extract_event_details_inside_link(link)
    
    # Create a comprehensive event data dictionary
    event_data = {
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
        "event_url": event_url,
    }
    
    # Add detailed event information if available
    if event_details_data:
        # Add description
        if "description" in event_details_data:
            event_data["description"] = event_details_data["description"]
        
        # Add venue details
        if "venue_details" in event_details_data and event_details_data["venue_details"]:
            event_data["venue_details"] = event_details_data["venue_details"]
            
        # Add terms and conditions
        if "terms_and_conditions" in event_details_data and event_details_data["terms_and_conditions"]:
            event_data["terms_and_conditions"] = event_details_data["terms_and_conditions"]
    
    return event_data


def extract_event_details_inside_link(link):
    """
    Extract comprehensive event details including description, venue information, and terms & conditions
    """
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
        response = requests.get(link, headers=headers, timeout=15)
        response.raise_for_status()
        print("link", link)
        soup = BeautifulSoup(response.text, "html.parser")
        
        event_details = {}
        
        # Extract event description
        description_section = soup.select_one("section.ACTION-sec-eventdetails")
        if description_section:
            event_details["description"] = extract_formatted_paragraphs(description_section)
        
        # Extract venue details
        venue_details = extract_venue_details(soup)
        if venue_details:
            event_details["venue_details"] = venue_details
        
        # Extract terms and conditions
        terms_conditions = extract_terms_and_conditions(soup)
        if terms_conditions:
            event_details["terms_and_conditions"] = terms_conditions

        
            
        # Extract other sections if needed (organizer info, etc.)
        # Add more sections here as needed
        
        return event_details
        
    except Exception as e:
        logger.error(f"Error fetching event details: {e}")
        return {"description": "Error fetching details", "venue_details": None, "terms_and_conditions": None}


def extract_venue_details(soup):
    """
    Extract complete venue details from the event details page including all navigation options
    """
    venue_section = soup.select_one("section.eventdetailrow.ACTION-sec-venuedetails")
    if not venue_section:
        return None

    # Get venue name and address
    venue_info = venue_section.select_one("small")
    if not venue_info:
        return None
    
    # Extract venue text content
    venue_text = venue_info.get_text(separator=" ", strip=True)
    
    # Try to get the venue name (within <b> tags)
    venue_name_elem = venue_info.select_one("b")
    venue_name = venue_name_elem.text.strip() if venue_name_elem else "N/A"
    
    # Get address (everything after the venue name)
    address = venue_text.replace(venue_name, "", 1).strip() if venue_name != "N/A" else venue_text
    
    # Extract navigation links
    nav_links = {}
    
    # Find the navigation links container
    nav_container = venue_section.select_one("div.iconav")
    if nav_container:
        # Extract each navigation option by icon type
        nav_items = nav_container.select("li a")
        for nav_item in nav_items:
            # Look for icon classes to determine type
            icon = nav_item.select_one("i")
            if icon:
                nav_type = None
                if icon.has_attr("class"):
                    icon_class = " ".join(icon.get("class", []))
                    if "car" in icon_class:
                        nav_type = "driving"
                    elif "train" in icon_class:
                        nav_type = "transit"
                    elif "map-bike" in icon_class:
                        nav_type = "biking"
                    elif "map-walk" in icon_class:
                        nav_type = "walking"
                
                if nav_type and nav_item.has_attr("href"):
                    nav_links[nav_type] = nav_item["href"]
    
    # Extract map image if available
    map_img = venue_section.select_one("img")
    map_url = map_img["src"] if map_img and map_img.has_attr("src") else None
    map_title = map_img["title"] if map_img and map_img.has_attr("title") else None
    
    # Extract city and state information from the address
    city = "N/A"
    state = "N/A"
    zip_code = "N/A"
    street_address = "N/A"
    
    # Try to parse address components
    if address != "N/A":
        address_parts = address.split(",")
        if len(address_parts) >= 1:
            street_address = address_parts[0].strip()
            
        if len(address_parts) >= 2:
            city = address_parts[-3].strip() if len(address_parts) >= 3 else address_parts[-2].strip()
            
        if len(address_parts) >= 3:
            state_zip_part = address_parts[-2].strip() if len(address_parts) >= 4 else address_parts[-1].strip()
            state_zip_bits = state_zip_part.split()
            
            if len(state_zip_bits) >= 1:
                state = state_zip_bits[0].strip()
                
            if len(state_zip_bits) >= 2:
                zip_code = state_zip_bits[1].strip()
            
    return {
        "name": venue_name,
        "full_address": address,
        "street_address": street_address,
        "city": city,
        "state": state,
        "zip_code": zip_code,
        "navigation_links": nav_links,
        "map_url": map_url,
        "map_title": map_title
    }


def extract_event_performers(soup):
    """
    Extract event performers information from the event details page
    """
    performers_section = soup.select_one("div#div_eventpromers.ACTION-sec-artist") or soup.select_one("div.ACTION-sec-artist")
    if not performers_section:
        return None
    
    # Extract section title
    title_elem = performers_section.select_one(".evesubtitle")
    section_title = title_elem.text.strip() if title_elem else "Event Performers"
    
    # Initialize performers list
    performers = []
    
    # Find all performer items
    performer_items = performers_section.select(".owl-item .item")
    
    for item in performer_items:
        performer_data = {}
        
        # Extract performer link
        link_elem = item.select_one("a")
        if link_elem and link_elem.has_attr("href"):
            performer_data["link"] = link_elem["href"]
            if link_elem.has_attr("title"):
                performer_data["link_title"] = link_elem["title"]
        
        # Extract performer image
        img_elem = item.select_one("figure img")
        if img_elem and img_elem.has_attr("src"):
            performer_data["image"] = img_elem["src"]
            if img_elem.has_attr("title"):
                performer_data["image_title"] = img_elem["title"]
        
        # Extract performer name
        name_elem = item.select_one("figcaption")
        if name_elem:
            performer_data["name"] = name_elem.text.strip()
        
        # Only add performer if we have at least a name
        if "name" in performer_data:
            performers.append(performer_data)
    
    # If no performers found in carousel, try alternative selectors
    if not performers:
        # Try to find performers in the artist section
        artist_section = performers_section.select_one("#Arists") or performers_section.select_one(".evepermrs")
        if artist_section:
            alt_performers = artist_section.select("a[title]")
            for performer in alt_performers:
                performer_data = {
                    "name": performer.text.strip() if performer.text.strip() else "Unknown Performer",
                    "link": performer["href"] if performer.has_attr("href") else None,
                    "link_title": performer["title"] if performer.has_attr("title") else None
                }
                
                # Extract image if available
                img = performer.select_one("img")
                if img and img.has_attr("src"):
                    performer_data["image"] = img["src"]
                
                # Only add if there's at least some information
                if performer_data["name"] != "Unknown Performer" or performer_data["link"]:
                    performers.append(performer_data)
    
    return {
        "title": section_title,
        "performers": performers
    }
def extract_terms_and_conditions(soup):
    """
    Extract only the visible Terms & Conditions information from the event details page
    """
    terms_section = soup.select_one("section.eventdetailrow.ACTION-sec-condition")
    if not terms_section:
        return None
    
    # Extract the section title
    title_elem = terms_section.select_one(".evesubtitle")
    section_title = title_elem.text.strip() if title_elem else "Terms & Conditions"
    
    # Get the article container
    article = terms_section.select_one("article")
    if not article:
        return {
            "title": section_title,
            "terms": []
        }
    
    # Extract only visible paragraph elements
    terms = []
    
    # Process all paragraphs, skipping those with the "hide" class
    for p in article.select("p"):
        # Skip hidden terms
        if p.has_attr("class") and "hide" in p["class"]:
            continue
            
        term_text = p.get_text(separator=" ", strip=True)
        if term_text:
            terms.append(term_text)
    
    # Get location information if available
    location_id = article.get("id", "") if article.has_attr("id") else None
    
    return {
        "title": section_title,
        "location_id": location_id,
        "terms": terms
    }

def extract_formatted_paragraphs(section):
    """
    Extract formatted paragraphs from event description section
    """
    if not section:
        return "N/A"
        
    p_tags = section.select("p.MsoNormal")
    cleaned_texts = []

    # If no MsoNormal paragraphs found, try regular paragraphs
    if not p_tags:
        p_tags = section.select("p")

    for p in p_tags:
        # Get text and normalize internal line breaks
        raw_text = p.get_text(separator=" ", strip=True)
        normalized_text = " ".join(raw_text.split())  # remove \n, \r and extra spaces
        if normalized_text:
            cleaned_texts.append(normalized_text)

    final_output = "\n\n".join(cleaned_texts)
    return final_output if final_output else "N/A"