from django.urls import path
from .views import HoroscopeAPIView

urlpatterns = [
    path("horoscope/", HoroscopeAPIView.as_view(), name="horoscope-api"),
]
