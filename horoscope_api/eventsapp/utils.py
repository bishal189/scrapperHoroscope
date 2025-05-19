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
            
        # Add artist details
        if "artist_details" in event_details_data and event_details_data["artist_details"]:
            event_data["artist_details"] = event_details_data["artist_details"]
            
        # Add organizer details
        if "organizer_details" in event_details_data and event_details_data["organizer_details"]:
            event_data["organizer_details"] = event_details_data["organizer_details"]

        # Add ticket information
        if "ticket_information" in event_details_data and event_details_data["ticket_information"]:
            event_data["ticket_information"] = event_details_data["ticket_information"]


       
    
            
    
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

        # Extract artist details
        artist_details = extract_artist_details(soup)
        if artist_details:
            event_details["artist_details"] = artist_details
        
        # Extract organizer details
        organizer_details = extract_organizer_details(soup)
        if organizer_details:
            event_details["organizer_details"] = organizer_details
            

        # Extract ticket information
        ticket_info = extract_ticket_information(soup)
        if ticket_info:
            event_details["ticket_information"] = ticket_info


        

            
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


def extract_artist_details(soup):
    """
    Extract artist details from the event details page sidebar
    """
    artist_article = soup.select_one("aside article.rhsbg div.atistdetailswrp")
    if not artist_article:
        return None
    
    artist_details = {}
    
    # Extract from artist details section
    artist_item = artist_article.select_one("ul li div.artistbg")
    if artist_item:
        # Extract artist image
        img_elem = artist_item.select_one("figure img")
        if img_elem:
            artist_details["image"] = img_elem.get("src", "")
            if img_elem.has_attr("alt"):
                artist_details["image_alt"] = img_elem.get("alt", "")
        
        # Extract artist name and link
        name_elem = artist_item.select_one("h3 a")
        if name_elem:
            artist_details["name"] = name_elem.text.strip()
            if name_elem.has_attr("href"):
                artist_details["link"] = name_elem.get("href", "")
            if name_elem.has_attr("title"):
                artist_details["link_title"] = name_elem.get("title", "")
        
        # Extract artist description
        description_elem = artist_item.select_one("p")
        if description_elem:
            # Get the text but exclude the "More »" link text
            more_link = description_elem.select_one("a")
            if more_link:
                more_link.extract()  # Remove the link from the paragraph
            
            artist_details["description"] = description_elem.text.strip()
            
            # Add the "more" link separately if needed
            more_link = artist_item.select_one("p a")
            if more_link and more_link.has_attr("href"):
                artist_details["more_link"] = more_link.get("href", "")
    
    # Extract tour information if available
    tour_article = soup.select_one("div#div_artistcurrent article")
    if tour_article:
        tour_title_elem = tour_article.select_one("div.rhstitle span")
        if tour_title_elem:
            artist_details["tour_title"] = tour_title_elem.text.strip()
        
        # Extract upcoming shows
        upcoming_shows = []
        show_items = tour_article.select("div.atistdetailswrp ul li div.atistdetails")
        
        for show in show_items:
            show_info = {}
            
            # Extract date
            date_elem = show.select_one("div.datewrp")
            if date_elem:
                day_elem = date_elem.select_one("span.day")
                month_elem = date_elem.select_one("span.month")
                
                if day_elem and month_elem:
                    show_info["day"] = day_elem.text.strip()
                    show_info["month"] = month_elem.text.strip()
            
            # Extract location details
            location_info = show.select_one("div.dateloc ul.whnwre")
            if location_info:
                # City/state
                city_elem = location_info.select_one("li h3.h3 a")
                if city_elem:
                    show_info["title"] = city_elem.get("title", "") if city_elem.has_attr("title") else ""
                    show_info["location_link"] = city_elem.get("href", "") if city_elem.has_attr("href") else ""
                    show_info["city"] = city_elem.text.strip()
                
                # Time information
                time_elem = location_info.select_one("li.times")
                if time_elem:
                    show_info["time"] = time_elem.text.strip().replace("\xa0", " ")
                
                # Venue information
                venue_elem = location_info.select_one("li.venuename")
                if venue_elem:
                    venue_text = venue_elem.text.strip().replace("\xa0", " ")
                    
                    # Try to extract venue name and address
                    venue_link = venue_elem.select_one("a")
                    if venue_link:
                        show_info["venue_name"] = venue_link.text.strip()
                        show_info["venue_link"] = venue_link.get("href", "") if venue_link.has_attr("href") else ""
                        
                        # Address is the text after the venue name
                        venue_text_parts = venue_text.split(show_info["venue_name"], 1)
                        if len(venue_text_parts) > 1:
                            show_info["venue_address"] = venue_text_parts[1].strip().strip(',')
                    else:
                        # No link - just extract the text
                        show_info["venue_info"] = venue_text
            
            if show_info:  # Only add if we have some info
                upcoming_shows.append(show_info)
        
        if upcoming_shows:
            artist_details["upcoming_shows"] = upcoming_shows
    
    return artist_details


def extract_organizer_details(soup):
    """
    Extract organizer details from the event details page
    """
    # Fix the CSS selector for compatibility
    # Using a more general selector that doesn't rely on :contains
    organizer_section = soup.select_one("section.eventdetailrow h2.evesubtitle")
    if organizer_section and "Organizer Details" in organizer_section.text:
        organizer_section = organizer_section.parent  # Get the parent section
    else:
        # Try alternative approach to find the organizer section
        for section in soup.select("section.eventdetailrow"):
            title = section.select_one("h2.evesubtitle")
            if title and "Organizer Details" in title.text:
                organizer_section = section
                break
        else:
            return None
    
    organizer_details = {}
    
    # Extract section title
    title_elem = organizer_section.select_one("h2.evesubtitle")
    if title_elem:
        organizer_details["title"] = title_elem.text.strip()
    
    # Extract organizer information
    org_article = organizer_section.select_one("article.orgwrap")
    if org_article:
        # Extract organizer logo
        logo_elem = org_article.select_one("div.orglogo figure img")
        if logo_elem:
            organizer_details["logo"] = logo_elem.get("src", "") if logo_elem.has_attr("src") else ""
            if logo_elem.has_attr("title"):
                organizer_details["logo_title"] = logo_elem.get("title", "")
        
        # Extract organizer name and event count
        org_details_div = org_article.select_one("div.org-detals")
        if org_details_div:
            # Organizer name
            name_elem = org_details_div.select_one("b")
            if name_elem:
                organizer_details["name"] = name_elem.text.strip()
            
            # Upcoming events count
            events_link = org_details_div.select_one("a.upcmtext")
            if events_link:
                organizer_details["events_link"] = events_link.get("href", "") if events_link.has_attr("href") else ""
                if events_link.has_attr("title"):
                    organizer_details["events_link_title"] = events_link.get("title", "")
                
                # Extract the number from the text (e.g., "20 Upcoming Event(s)")
                events_text = events_link.text.strip()
                import re
                events_count_match = re.search(r'(\d+)\s+Upcoming\s+Event', events_text)
                if events_count_match:
                    organizer_details["upcoming_events_count"] = events_count_match.group(1)
        
        # Extract action links
        action_div = org_article.select_one("div.org-action")
        if action_div:
            # Profile link
            profile_link = action_div.select_one("a[title*='Profile']")
            if profile_link:
                organizer_details["profile_link"] = profile_link.get("href", "") if profile_link.has_attr("href") else ""
            
            # Follow/Following links (these are usually JavaScript actions)
            follow_link = action_div.select_one("a.btn-follow605")
            if follow_link:
                organizer_details["follow_link_available"] = True
    
    # Extract events by this organizer
    org_events_div = soup.select_one("div#div_orgmasterevents article")
    if org_events_div:
        events_list = []
        
        # Get all event items
        event_items = org_events_div.select("div.orgartistinfo ul li")
        
        for event in event_items:
            event_info = {}
            
            # Artist name
            artist_name_elem = event.select_one("h3.artistname a")
            if artist_name_elem:
                event_info["artist_name"] = artist_name_elem.text.strip()
                event_info["artist_link"] = artist_name_elem.get("href", "") if artist_name_elem.has_attr("href") else ""
            
            # Event image
            img_elem = event.select_one("figure img")
            if img_elem:
                event_info["image"] = img_elem.get("src", "") if img_elem.has_attr("src") else ""
                if img_elem.has_attr("title"):
                    event_info["image_title"] = img_elem.get("title", "")
            
            # Event title
            title_elem = event.select_one("small a")
            if title_elem:
                event_info["title"] = title_elem.text.strip()
                event_info["link"] = title_elem.get("href", "") if title_elem.has_attr("href") else ""
                if title_elem.has_attr("title"):
                    event_info["link_title"] = title_elem.get("title", "")
            
            # Event time/date
            time_elem = event.select_one("span.timezone")
            if time_elem:
                event_info["time"] = time_elem.text.strip().replace("\xa0", " ")
            
            # Venue
            venue_elem = event.select_one("p")
            if venue_elem:
                event_info["venue"] = venue_elem.text.strip().replace("\xa0", " ")
            
            # Ticket link
            ticket_link = event.select_one("a.btn-ghost-red1")
            if ticket_link:
                event_info["ticket_link"] = ticket_link.get("href", "") if ticket_link.has_attr("href") else ""
                if ticket_link.has_attr("title"):
                    event_info["ticket_link_title"] = ticket_link.get("title", "")
            
            if event_info:  # Only add if we extracted some info
                events_list.append(event_info)
        
        if events_list:
            organizer_details["events"] = events_list
    
    return organizer_details


def extract_ticket_information(soup):
    """
    Extract ticket information including prices, categories, and availability
    """
    ticket_section = soup.select_one("section.tkt-wraper.ACTION-sec-ticket")
    if not ticket_section:
        return None
    
    ticket_info = {}
    
    # Extract section title
    title_elem = ticket_section.select_one("h2")
    if title_elem:
        # Get the text but exclude the button text
        button = title_elem.select_one("a")
        if button:
            button.extract()  # Remove the button from the title
        ticket_info["title"] = title_elem.text.strip()
    
    # Extract all ticket types
    ticket_types = []
    ticket_articles = ticket_section.select("article.tkt-wrap")
    
    for article in ticket_articles:
        ticket_type = {}
        
        # Extract ticket category/title
        category_elem = article.select_one("b.tkt-title")
        if category_elem:
            ticket_type["category"] = category_elem.text.strip()
        
        # Extract ticket description
        desc_elem = article.select_one("small.tkt-desc")
        if desc_elem and desc_elem.text.strip():
            ticket_type["description"] = desc_elem.text.strip()
        
        # Extract ticket price
        price_elem = article.select_one("small.tkt-price-wrp")
        if price_elem:
            ticket_type["price"] = price_elem.text.strip()
        
        # Extract ticket status
        status_elem = article.select_one("span.tkt-status")
        if status_elem:
            ticket_type["status"] = status_elem.text.strip()
            # Check if it's almost sold out (has red class)
            if status_elem.has_attr("class") and "red" in status_elem["class"]:
                ticket_type["almost_sold_out"] = True
        
        # Extract ticket closing date
        closing_date_elem = article.select_one("div.tktopnstatus b")
        if closing_date_elem:
            ticket_type["closing_date"] = closing_date_elem.text.strip()
        
        # Extract any other available information
        closing_text_elem = article.select_one("div.tktopnstatus span")
        if closing_text_elem:
            ticket_type["closing_text"] = closing_text_elem.text.strip()
        
        if ticket_type:  # Only add if we have some info
            ticket_types.append(ticket_type)
    
    # Add ticket types to ticket info
    if ticket_types:
        ticket_info["ticket_types"] = ticket_types
    
    # Extract action button if available
    action_btn = ticket_section.select_one("article.tkt-totalbg a.buy-btn")
    if action_btn:
        ticket_info["action_button"] = {
            "text": action_btn.text.strip(),
            "onclick": action_btn.get("onclick", "") if action_btn.has_attr("onclick") else ""
        }
    
    return ticket_info


