"""
CSD-460 Capstone Blue Team
Moffat Bay Lodge Project
Vee Bell, Deja Faison, Julia Gonzalez, Jess Monnier
Professor Sue Sampson
Developed October thru December of 2025

The purpose of this migration is to create required database
records if they are missing. It also adds a maintenance_until
field to the rooms table.
"""

from django.db import migrations, models

def create_initial_room_types(apps, schema_editor):
    RoomType = apps.get_model('web', 'RoomType')

    initial_types = [
        {
            "name": "Double Full",
            "price_per_night": 126.00,
            "beds": 2,
            "max_guests": 4,
            "description": "Two full beds with island view."
        },
        {
            "name": "Queen",
            "price_per_night": 141.75,
            "beds": 1,
            "max_guests": 2,
            "description": "Single queen bed overlooking the bay."
        },
        {
            "name": "Double Queen",
            "price_per_night": 157.50,
            "beds": 2,
            "max_guests": 4,
            "description": "Two queen beds, partial ocean view."
        },
        {
            "name": "King",
            "price_per_night": 168.00,
            "beds": 1,
            "max_guests": 2,
            "description": "Large king room with premium amenities."
        },
    ]

    # Use update_or_create so the records will not be added over and over
    # if this migration is run multiple times
    for rt in initial_types:
        RoomType.objects.update_or_create(
            name=rt["name"],  # lookup by unique name
            defaults={
                "price_per_night": rt["price_per_night"],
                "beds": rt["beds"],
                "max_guests": rt["max_guests"],
                "description": rt["description"],
            }
        )


def create_initial_rooms(apps, schema_editor):
    Room = apps.get_model('web', 'Room')
    RoomType = apps.get_model('web', 'RoomType')

    initial_rooms = [
        {"room_number": "101", "status": "Available", "room_type_name": "King", "maintenance_until": None},
        {"room_number": "102", "status": "Cleaning", "room_type_name": "King", "maintenance_until": None},
        {"room_number": "201", "status": "Available", "room_type_name": "Double Queen", "maintenance_until": None},
        {"room_number": "202", "status": "Occupied", "room_type_name": "Double Queen", "maintenance_until": None},
        {"room_number": "301", "status": "Available", "room_type_name": "Double Full", "maintenance_until": None},
        {"room_number": "302", "status": "Maintenance", "room_type_name": "Double Full", "maintenance_until": "2025-11-25"},
        {"room_number": "401", "status": "Available", "room_type_name": "Queen", "maintenance_until": None},
        {"room_number": "402", "status": "Occupied", "room_type_name": "Queen", "maintenance_until": None},
    ]

    # Use update_or_create so the records will not be added over and over
    # if this migration is run multiple times
    for room in initial_rooms:
        room_type = RoomType.objects.get(name=room["room_type_name"])
        Room.objects.update_or_create(
            room_number=room["room_number"],
            defaults={
                "status": room["status"],
                "room_type": room_type,
            }
        )

class Migration(migrations.Migration):

    dependencies = [
        ('web', '0001_initial'),
    ]

    operations = [ 
        # Add maintenance_until field to Room
        migrations.AddField(
            model_name='room',
            name='maintenance_until',
            field=models.DateField(blank=True, null=True, help_text="Expected date room will be available after maintenance"),
        ),
        # Seed the required rooms and room_types fields
        migrations.RunPython(create_initial_room_types, reverse_code=migrations.RunPython.noop),
        migrations.RunPython(create_initial_rooms, reverse_code=migrations.RunPython.noop),
    ]
