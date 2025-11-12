# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = True` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models

class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=35)
    last_name = models.CharField(max_length=35)
    email = models.CharField(unique=True, max_length=254)
    phone_number = models.CharField(max_length=25)
    password_hash = models.CharField(max_length=128)
    address_country = models.CharField(max_length=35, blank=True, null=True)
    address_street = models.CharField(max_length=254, blank=True, null=True)
    address_city = models.CharField(max_length=35, blank=True, null=True)
    address_state = models.CharField(max_length=35, blank=True, null=True)
    address_zipcode = models.CharField(max_length=25, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'customers'

class RoomType(models.Model):
    # the id field is not defined because that's what Django uses by default for primary key
    name = models.CharField(max_length=25)
    price_per_night = models.DecimalField(max_digits=7, decimal_places=2)
    beds = models.IntegerField()
    max_guests = models.IntegerField()
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'room_types'


class Room(models.Model):
    STATUS_CHOICES = [
        ('Available', 'Available'),
        ('Occupied', 'Occupied'),
        ('Cleaning', 'Cleaning'),
        ('Maintenance', 'Maintenance'),
    ]
    room_id = models.AutoField(primary_key=True)
    room_number = models.CharField(unique=True, max_length=20)
    room_type = models.ForeignKey(RoomType, on_delete=models.PROTECT, db_column='room_type')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='Available')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'rooms'

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('Hold', 'Hold'),
        ('Confirmed', 'Confirmed'),
        ('Cancelled', 'Cancelled'),
    ]
    reservation_id = models.CharField(primary_key=True, max_length=36)
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
    room_type = models.ForeignKey('RoomType', on_delete=models.SET_NULL, db_column='room_type', blank=True, null=True)
    room = models.ForeignKey('Room', on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'reservations'