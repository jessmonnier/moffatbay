from django.contrib import admin
from .models import Customer, RoomType, Room, Reservation

admin.site.register(Customer)
admin.site.register(RoomType)
admin.site.register(Room)
admin.site.register(Reservation)