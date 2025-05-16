from django.shortcuts import render
from django.http import JsonResponse
from .utils import scrape_sulekha_events

# Create your views here.
from .models import CommunityEvents, Mastercity

from django.utils import timezone


def insert_events_into_db(data):
    city_name = data["city"]
    all_events = []
    city_entry = Mastercity.objects.filter(city__iexact=city_name)[0]
    state_name = city_entry.state

    # Flatten all event lists across categories
    for category, events in data["events"].items():
        if isinstance(events, list):
            all_events.extend(events)

    for event in all_events:
        try:

            name = event.get("title", "")
            state = state_name
            city = city_name
            location = event.get("location", "")
            venue = event.get("venue", "")
            price = event.get("price", "")
            event_date = event.get("date", "")
            performers = event.get("performers", "")

            # Check if this event already exists
            existing = CommunityEvents.objects.filter(
                state=state,
                city=city,
                price=price,
                performers=performers,
                event_date=event_date,
                venue=venue,
                location=location,
            )

            if existing.exists():
                print(f"Already exists: {name}")
                existing.delete()

            CommunityEvents.objects.create(
                name=event.get("title", ""),
                state=state_name,
                time="",  # Not using original time since it's inside date string
                location=event.get("location", ""),
                description=event.get("description", ""),
                city=city_name,
                created_at=timezone.now(),
                updated_at=timezone.now(),
                performers=event.get("performers", ""),
                cover_image=event.get("image", ""),
                price=event.get("price", ""),
                venue=event.get("venue", ""),
                link=event.get("link", ""),
                event_date=event.get("date", ""),
            )
            print(f"Inserted: {event.get('title')}")
        except Exception as e:
            print(f"Failed to insert {event.get('title')}: {e}")


def events(request):
    cities = {
        "Austin": "austin-metro-area",
        "Dallas": "dallas-fortworth-area",
        "Houston": "houston-metro-area",
        "Los Angeles": "los-angeles-metro-area",
        "New York": "new-york-metro-area",
        "Philadelphia": "philadelphia-metro-area",
        "Miami": "miami-metro-area",
        "San Francisco": "bay-area",
        "Chicago": "chicago-metro-area",
        "Boston": "boston-metro-area",
        "Seattle": "seattle-metro-area",
        "Denver": "denver-metro-area",
        "Atlanta": "atlanta-metro-area",
        "Phoenix": "phoenix-metro-area",
        "San Diego": "san-diego-metro-area",
        "Las Vegas": "las-vegas-metro-area",
        "Portland": "portland-metro-area",
        "Detroit": "detroit-metro-area",
        "Baltimore": "baltimore-metro-area",
        "Charlotte": "research-triangle-area",
        "Minneapolis": "st-paul-metro-area",
        "Tampa": "tampa-metro-area",
        "St. Louis": "st-louis-metro-area",
        "New Orleans": "new-orleans-metro-area",
        "Salt Lake City": "ogden-metro-area",
        "Indianapolis": "indianapolis-metro-area",
        "Cleveland": "cleveland-metro-area",
        "Cincinnati": "cincinnati-metro-area",
        "Kansas City": "kansas-city-metro-area",
        "Omaha": "omaha-metro-area",
        "Oakland": "bay-area",
        "Orlando": "orlando-metro-area",
        "Sacramento": "sacramento-metro-area",
        "Nashville": "nashville-metro-area",
        "Milwaukee": "milwaukee-metro-area",
        "Raleigh": "research-triangle-area",
        "Memphis": "memphis-metro-area",
        "Portland": "portland-metro-area",
        "Virginia Beach": "richmond-metro-area",
        "Albuquerque": "albuquerque-metro-area",
        "Tulsa": "dallas-fortworth-area",
        "Fresno": "bay-area",
        "Columbus": "cincinnati-metro-area",
        "Wichita": "kansas-city-metro-area",
        "Pittsburgh": "bay-area",
        "Anchorage": "anchorage-metro-area",
        "Honolulu": "honolulu-metro-area",
        "Colorado Springs": "denver-metro-area",
        "El Paso": "dallas-fortworth-area",
        "Lexington": "lexington-metro-area",
        "Reno": "sacramento-metro-area",
        "Boise": "boise-metro-area",
        "Spokane": "seattle-metro-area",
        "Baton Rouge": "houston-metro-area",
        "Des Moines": "des-moines-metro-area",
        "Fort Worth": "dallas-fortworth-area",
        "Jacksonville": "orlando-metro-area",
        "Little Rock": "conway-metro-area",
        "Madison": "madison-metro-area",
        "Providence": "providence-metro-area",
        "Richmond": "richmond-metro-area",
        "Sioux Falls": "sioux-falls-metro-area",
        "Springfield": "chicago-metro-area",
        "Tucson": "phoenix-metro-area",
        "Bakersfield": "los-angeles-metro-area",
        "Chattanooga": "chattanooga-metro-area",
        "Durham": "research-triangle-area",
        "Fargo": "fargo-metro-area",
        "Green Bay": "milwaukee-metro-area",
        "Harrisburg": "philadelphia-metro-area",
        "Lubbock": "dallas-fortworth-area",
        "Mobile": "montgomery-metro-area",
        "Modesto": "bay-area",
        "Montgomery": "montgomery-metro-area",
        "Newark": "new-jersey-area",
        "Norfolk": "washington-metro-area",
        "Olympia": "seattle-metro-area",
        "Peoria": "chicago-metro-area",
        "Rochester": "new-york-metro-area",
        "Salem": "portland-metro-area",
        "Santa Fe": "phoenix-metro-area",
        "Syracuse": "new-york-metro-area",
        "Topeka": "kansas-city-metro-area",
        "Wilmington": "philadelphia-metro-area",
        "Augusta": "atlanta-metro-area",
        "Bismarck": "bismarck-metro-area",
        "Cheyenne": "cheyenne-metro-area",
        "Dover": "philadelphia-metro-area",
        "Helena": "helena-mt",
        "Jefferson City": "jefferson-city-mo",
        "Lincoln": "kansas-city-metro-area",
        "Montpelier": "montpelier-vt",
        "Tallahassee": "orlando-metro-area",
        "San Jose": "bay-area",
        "Fort Lauderdale": "miami-metro-area",
        "Riverside": "inland-empire-area",
        "Corpus Christi": "houston-metro-area",
        "Stockton": "bay-area",
        "Santa Ana": "los-angeles-metro-area",
        "St. Paul": "st-paul-metro-area",
    }

    for city_key, city_value in cities.items():
        if not city_key:
            return JsonResponse({"error": "City parameter is required."}, status=400)

        events = scrape_sulekha_events(city_value)

        insert_events_into_db({"city": city_key, "events": events})

    return JsonResponse(
        {"status": "Success", "message": "Events retrieved Successfully"}, status=200
    )
