from django.http import JsonResponse
from rest_framework.decorators import api_view
from .utils import scrape_horoscope

@api_view(["GET"])
def get_horoscope(request):
    data = scrape_horoscope()
    return JsonResponse({"horoscope": data}, safe=False)
