from django.shortcuts import render
from django.http import JsonResponse
from . utils import scrape_sulekha_events

# Create your views here.

def events(request):
    city = request.GET.get("city", "")
    if not city:
        return JsonResponse({"error": "City parameter is required."}, status=400)

    events = scrape_sulekha_events(city)
    return JsonResponse({"city": city.capitalize(), "events": events})