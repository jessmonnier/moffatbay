"""
CSD-460 Capstone Blue Team
Moffat Bay Lodge Project
Vee Bell, Deja Faison, Julia Gonzalez, Jess Monnier
Professor Sue Sampson
Developed October thru December of 2025
"""

from django.db import models
from django.contrib.auth.models import User

class Customer(models.Model):
    # One-to-one link with Django User
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    phone_number = models.CharField(max_length=25, blank=True, null=True)
    address_country = models.CharField(max_length=35, blank=True, null=True)
    address_street = models.CharField(max_length=254, blank=True, null=True)
    address_city = models.CharField(max_length=35, blank=True, null=True)
    address_state = models.CharField(max_length=35, blank=True, null=True)
    address_zipcode = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        db_table = 'customers'

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.user.email})"


class RoomType(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=25)
    price_per_night = models.DecimalField(max_digits=7, decimal_places=2)
    beds = models.IntegerField()
    max_guests = models.IntegerField()
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'room_types'
        managed = False
    
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
    room_number = models.CharField(unique=True, max_length=20)
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='Available')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'rooms'
    
    def __str__(self):
        return f"Room {self.room_number} ({self.room_type.name})"


class Reservation(models.Model):
    STATUS_CHOICES = [
        ('Hold', 'Hold'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ]
    # Use default `id` as primary key
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, blank=True, null=True)
    guest_first_name = models.CharField(max_length=35)
    guest_last_name = models.CharField(max_length=35)
    guest_phone = models.CharField(max_length=25)
    guest_email = models.CharField(max_length=254)
    created_time = models.DateTimeField(auto_now_add=True)
    expiration_time = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Hold')
    start_date = models.DateField()
    end_date = models.DateField()
    room_type = models.ForeignKey(RoomType, on_delete=models.SET_NULL, blank=True, null=True)
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        db_table = 'reservations'
    
    def __str__(self):
        return f"Reservation {self.id} - {self.guest_first_name} {self.guest_last_name}"
