"""
CSD-460 Capstone Blue Team
Moffat Bay Lodge Project
Vee Bell, Deja Faison, Julia Gonzalez, Jess Monnier
Professor Sue Sampson
Developed October thru December of 2025
"""

from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from ..models import RoomType, Reservation, Room
from django.db.models import Q
from datetime import datetime
from django.utils import timezone

def parse_dates(check_in_str, check_out_str):
    """Parse date strings into date objects and validate order."""
    try:
        check_in = datetime.strptime(check_in_str, "%Y-%m-%d").date()
        check_out = datetime.strptime(check_out_str, "%Y-%m-%d").date()
        today = timezone.localdate()

        # Prevent past check-in
        if check_in < today:
            return None, None, "Check-in date cannot be in the past."

        # Prevent check out day as or before check in bc that makes no sense
        if check_in >= check_out:
            return None, None, "Check-out date must be after check-in date."
        return check_in, check_out, None
    except ValueError:
        return None, None, "Invalid dates provided."

def validate_emails(*emails):
    """Return a tuple (valid_emails_set, invalid_emails_list)."""
    valid = set()
    invalid = []
    for addr in emails:
        addr = addr.strip()
        if not addr:
            continue
        try:
            validate_email(addr)
            valid.add(addr)
        except ValidationError:
            invalid.append(addr)
    return valid, invalid

def get_available_rooms(check_in, check_out, num_guests=None, selected_room_type_id=None):
    """
    Returns a list of available room types with counts based on
    check-in/check-out dates, optional guest count, and optional selected room type.
    Each entry is a dict: {"room_type": RoomType, "available_count": int}
    """
    available_room_types = []
    room_types = RoomType.objects.all().order_by('name')

    for room_type in room_types:
        # Filter by selected room type if applicable
        if selected_room_type_id and str(room_type.id) != str(selected_room_type_id):
            continue

        # Filter by guest count if provided
        if num_guests and room_type.max_guests < int(num_guests):
            continue

        # Count rooms of this type not under maintenance during the date range
        available_rooms_count = Room.objects.filter(
            room_type=room_type
        ).filter(
            Q(status__in=["Available", "Occupied", "Cleaning"]) |
            Q(status="Maintenance", maintenance_until__lt=check_in)
        ).count()

        if available_rooms_count == 0:
            continue  # no rooms available at all

        # Count overlapping reservations for this room type
        overlapping_count = Reservation.objects.filter(
            room_type=room_type,
            status__in=["Hold", "Confirmed"],
            start_date__lt=check_out,
            end_date__gt=check_in
        ).count()

        if overlapping_count >= available_rooms_count:
            continue  # room type fully booked

        # Room type is available
        available_room_types.append({
            "room_type": room_type,
            "available_count": available_rooms_count - overlapping_count,
            "price_per_night": room_type.price_per_night
        })

    return available_room_types

def calculate_total_cost(check_in, check_out, price_per_night):
    """
    Return total cost given check-in/out dates and price per night.
    Ensures minimum of 1 night.
    """
    nights = (check_out - check_in).days
    if nights < 1:
        nights = 1
    total_cost = nights * price_per_night
    return nights, total_cost