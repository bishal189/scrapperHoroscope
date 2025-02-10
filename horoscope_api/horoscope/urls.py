from django.urls import path
from .views import get_horoscope

urlpatterns = [
    path("horoscope/", get_horoscope, name="get_horoscope"),
]
