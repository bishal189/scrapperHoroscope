from django.db import models
# Create your models here.
class CommunityEvents(models.Model):
    name = models.CharField(max_length=255)
    date = models.DateField(blank=True, null=True)
    time = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    cover_image = models.TextField(blank=True, null=True)
    price = models.TextField(blank=True, null=True)
    venue = models.TextField(blank=True, null=True)
    performers = models.TextField(blank=True, null=True)
    link = models.TextField(blank=True, null=True)
    event_date = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'community_events'


class Mastercity(models.Model):
    mastercityid = models.IntegerField(blank=True, null=True)
    city = models.CharField(max_length=200, blank=True, null=True)
    state = models.CharField(max_length=200, blank=True, null=True)
    geohash = models.CharField(max_length=200, blank=True, null=True)
    long = models.CharField(max_length=200, blank=True, null=True)
    lat = models.CharField(max_length=200, blank=True, null=True)
    key = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=20, blank=True, null=True)
    createdby = models.CharField(max_length=100, blank=True, null=True)
    createddate = models.DateTimeField(blank=True, null=True)
    updatedby = models.CharField(max_length=100, blank=True, null=True)
    updateddate = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'mastercity'

