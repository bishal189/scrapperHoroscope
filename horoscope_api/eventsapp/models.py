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

    event_id = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    category = models.TextField(blank=True, null=True)
    action_type = models.TextField(blank=True, null=True)
    event_url = models.TextField(blank=True, null=True)

    # Venue Details
    venue_name = models.TextField(blank=True, null=True)
    venue_full_address = models.TextField(blank=True, null=True)
    venue_street = models.TextField(blank=True, null=True)
    venue_city = models.TextField(blank=True, null=True)
    venue_state = models.TextField(blank=True, null=True)
    venue_zip = models.TextField(blank=True, null=True)

    # Terms & Conditions
    terms_title = models.TextField(blank=True, null=True)
    terms_location = models.TextField(blank=True, null=True)
    terms_list = models.TextField(blank=True, null=True)  # Store JSON or newline-separated terms

    # Artist Details
    artist_name = models.TextField(blank=True, null=True)
    artist_image = models.TextField(blank=True, null=True)
    artist_description = models.TextField(blank=True, null=True)
    artist_link = models.TextField(blank=True, null=True)

    # Organizer Details
    organizer_name = models.TextField(blank=True, null=True)
    organizer_logo = models.TextField(blank=True, null=True)
    organizer_events_link = models.TextField(blank=True, null=True)
    organizer_upcoming_count = models.TextField(blank=True, null=True)
    organizer_follow_available = models.BooleanField(default=False)

    # Ticket Information
    ticket_types = models.TextField(blank=True, null=True)  # Store JSON array as string
    ticket_action_button = models.TextField(blank=True, null=True)


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

