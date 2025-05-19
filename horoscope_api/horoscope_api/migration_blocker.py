from django.core.management.base import CommandError

def block_migrations():
    raise CommandError("❌ Migrations are disabled for this project! Don't run makemigrations or migrate.")

