import asyncio
from rest_framework.views import APIView
from rest_framework.response import Response
from .utils import scrape_horoscope

class HoroscopeAPIView(APIView):
    """ DRF API View to return horoscope data """

    def get(self, request):
        """ Handles GET request for horoscope data """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(scrape_horoscope())
        return Response(result)
