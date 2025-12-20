"""
CSD-460 Capstone Blue Team
Moffat Bay Lodge Project
Vee Bell, Deja Faison, Julia Gonzalez, Jess Monnier
Professor Sue Sampson
Developed October thru December of 2025
"""

from django.db import models
import uuid
from django.contrib.auth.models import User
from django.db.models import Case, When, Value, IntegerField

class Customer(models.Model):
    # One-to-one link with Django User
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        help_text="Link this customer to a Django user account."
    )

    phone_number = models.CharField(
        max_length=25,
        blank=True,
        null=True,
        help_text="Primary contact phone number for the customer."
    )
    address_country = models.CharField(
        max_length=35,
        blank=True,
        null=True,
        help_text="Country of the customer's primary address."
    )
    address_street = models.CharField(
        max_length=254,
        blank=True,
        null=True,
        help_text="Street address of the customer."
    )
    address_city = models.CharField(
        max_length=35,
        blank=True,
        null=True,
        help_text="City of the customer's address."
    )
    address_state = models.CharField(
        max_length=35,
        blank=True,
        null=True,
        help_text="State or province of the customer's address."
    )
    address_zipcode = models.CharField(
        max_length=25,
        blank=True,
        null=True,
        help_text="ZIP or postal code for the customer."
    )

    class Meta:
        db_table = 'customers'

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.user.email})"


class RoomType(models.Model):
    
    # no need for id, Python handles that by default

    name = models.CharField(
        max_length=25,
        unique=True,
        help_text="Name of the room type (e.g., Queen, King, Double Full)."
    )
    price_per_night = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        help_text="Standard price per night for this room type."
    )
    beds = models.IntegerField(
        help_text="Number of beds in this room type."
    )
    max_guests = models.IntegerField(
        help_text="Maximum number of guests allowed in this room type."
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional description or special features of this room type."
    )

    class Meta:
        db_table = 'room_types'
    
    def __str__(self):
        return f"{self.name} - ${self.price_per_night}/night"


class Room(models.Model):
    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Occupied', 'Occupied'),
        ('Cleaning', 'Cleaning'),
        ('Maintenance', 'Maintenance'),
    ]
    # Let Django use default `id` as primary key
    room_number = models.CharField(
        unique=True,
        max_length=20,
        help_text="Unique identifier for the room (e.g., 101, 202)."
    )
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.PROTECT,
        help_text="The type of this room (links to RoomType)."
    )
    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default='Available',
        help_text="Current status of the room."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Automatically updated timestamp when the room record is modified."
    )

    # new maintenance end date field; this is added in migration 0002
    maintenance_until = models.DateField(
        blank=True,
        null=True,
        help_text="If in maintenance, the date the room is expected to become available."
    )

    class Meta:
        db_table = 'rooms'
    
    def __str__(self):
        return f"Room {self.room_number} ({self.room_type.name})"

class ReservationQuerySet(models.QuerySet):
    def ordered(self):
        return self.annotate(
            status_order=Case(
                When(status='Hold', then=Value(1)),
                When(status='Confirmed', then=Value(2)),
                When(status='Cancelled', then=Value(3)),
                default=Value(99),
                output_field=IntegerField(),
            )
        ).order_by('status_order', '-start_date')

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('Hold', 'Hold'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ]

    objects = ReservationQuerySet.as_manager()
    # Use default `id` as primary key
    # But generate a unique public_id for customers to see and use
    public_id = models.CharField(
        max_length=12,
        unique=True,
        editable=False,
        help_text="Public-facing reservation ID."
    )

    customer = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Optional link to a registered customer."
    )
    guest_first_name = models.CharField(
        max_length=35,
        help_text="First name of the guest making the reservation."
    )
    guest_last_name = models.CharField(
        max_length=35,
        help_text="Last name of the guest making the reservation."
    )
    guest_phone = models.CharField(
        max_length=25,
        help_text="Phone number of the guest for contact purposes."
    )
    guest_email = models.CharField(
        max_length=254,
        help_text="Email address of the guest."
    )
    created_time = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the reservation was first created."
    )
    expiration_time = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Optional expiration time for holds or temporary reservations."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Automatically updated timestamp when the reservation is modified."
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Hold',
        help_text="Current status of the reservation."
    )
    start_date = models.DateField(
        help_text="Check-in date for the reservation."
    )
    end_date = models.DateField(
        help_text="Check-out date for the reservation."
    )
    room_type = models.ForeignKey(
        RoomType,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Optional preference for a specific room type."
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="Specific room assigned to this reservation, if any."
    )
    total_cost = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        help_text="The total cost to the customer for this reservation."
    )
    guests = models.PositiveSmallIntegerField(
        help_text="Number of guests for this reservation."
    )

    class Meta:
        db_table = 'reservations'
    
    # Override save to generate the public_id
    def save(self, *args, **kwargs):
        """
        As a note, this does not check for collisions. It's EXTREMELY statistically
        unlikely that an ID already in our database would be randomly generated again,
        even if we had like a hundred thousand reservations in there, but there still
        is a chance. I don't think it's worth implementing a check for this at this stage,
        but we would want to for a real project.
        """

        # Only generate a new public_id if it does not already have one
        if not self.public_id:
            self.public_id = "MBL-" + uuid.uuid4().hex[:8].upper()
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Reservation {self.id} - {self.guest_first_name} {self.guest_last_name}"