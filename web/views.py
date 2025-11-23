"""
CSD-460 Capstone Blue Team
Moffat Bay Lodge Project
Vee Bell, Deja Faison, Julia Gonzalez, Jess Monnier
Professor Sue Sampson
Developed October thru December of 2025
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings
from .models import RoomType, Reservation, Room
from django.db.models import Q
from datetime import datetime, timedelta
from django.utils import timezone
import random
import string

# ------------------- Helper Functions -------------------

def generate_reservation_number():
    """Create a simple reservation number like MB-12345678."""
    return "MB-" + "".join(random.choices(string.digits, k=8))

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
            "available_count": available_rooms_count - overlapping_count
        })

    return available_room_types

# ------------------------ Views ------------------------

def index(request):
    return render(request, 'pages/index.html')

def about(request):
    return render(request, 'pages/about.html')

@login_required(login_url='login')
def account(request):
    return render(request, 'pages/account.html')

def attractions(request):
    return render(request, 'pages/attractions.html')

def login(request):
    return render(request, 'pages/login.html')

def register(request):
    if request.method == "POST":
        first = request.POST.get("first_name")
        last = request.POST.get("last_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone_number")
        password = request.POST.get("password")
        confirm = request.POST.get("confirm_password")
        agreed = request.POST.get("agreedToTerms")

        # Validate terms checkbox
        if not agreed:
            messages.error(request, "You must agree to the Terms & Conditions.")
            return redirect("register")

        # Password match check
        if password != confirm:
            messages.error(request, "Passwords do not match.")
            return redirect("register")
        
        #Empty field check
        if not all([first, last, email, phone, password, confirm]):
            messages.error(request, "All fields are required.")
            return redirect("register")
        #Empty password check
        if not password:
            messages.error(request, "Password cannot be empty.")
            return redirect("register")

        # Email must be unique (used as username)
        if User.objects.filter(username=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("register")

        # Create user
        User.objects.create(
            username=email,     # ← Username stored as email
            email=email,
            first_name=first,
            last_name=last,
            password=make_password(password)
        )

        messages.success(request, "Account created! Please log in.")
        return redirect("login")
    
    return render(request, "pages/register.html")

@login_required(login_url='login')
def reservation(request):
    context = {}
    room_types = RoomType.objects.all().order_by('name')
    context['room_types'] = room_types
    context['available_room_types'] = []
    # flag for whether user attempted search
    context['searched'] = 'check_in' in request.GET

    # Use each search as an opportunity to cancel held reservations
    # that have expired already
    if context['searched']:
        now = timezone.now()
        Reservation.objects.filter(
            status = 'Hold',
            expiration_time__isnull=False,
            expiration_time__lt=now
        ).update(status='Cancelled')

    # Get input from form
    check_in_str = request.GET.get('check_in', '')
    check_out_str = request.GET.get('check_out', '')
    selected_room_type_id = request.GET.get('room_type', '')
    num_guests = request.GET.get('guests', '')

    # Pre-fill form data
    initial_data = {
        "check_in": check_in_str or "",
        "check_out": check_out_str or "",
        "room_type": selected_room_type_id or "",
        "guests": num_guests or "",
    }

    # Pre-fill guest info from user's Customer profile
    customer = getattr(request.user, 'customer', None)
    if customer:
        initial_data.update({
            "first_name": customer.user.first_name,
            "last_name": customer.user.last_name,
            "email": customer.user.email,
            "phone": customer.phone_number,
        })

    context['initial_data'] = initial_data

    if context['searched']:

        # Validate dates
        if not check_in_str or not check_out_str:
            context['error'] = "Please select both check-in and check-out dates."
        else:
            check_in, check_out, error = parse_dates(check_in_str, check_out_str)
            if error:
                context['error'] = error
            else:
                # Check if customer has overlapping dates already
                overlapping_reservations = []
                now = timezone.now()
                overlapping_reservations = Reservation.objects.filter(
                    customer=customer
                ).filter(
                    Q(status='Confirmed') |
                    Q(status='Hold', expiration_time__gt=now)
                ).filter(
                    Q(start_date__lt=check_out) &
                    Q(end_date__gt=check_in)
                )
                print(overlapping_reservations)

                if overlapping_reservations.exists():
                    context["overlap_warning"] = True
                    context["overlapping_reservations"] = overlapping_reservations
                
                # Check availability of rooms
                context['available_room_types'] = get_available_rooms(
                    check_in, check_out,
                    num_guests=num_guests,
                    selected_room_type_id=selected_room_type_id
                )
            if not context['available_room_types']:
                context['no_results'] = True

    return render(request, 'pages/reservation.html', context)

@login_required
def save_reservation(request):
    """
    Save a new reservation with status 'Hold' or 'Confirmed', calculate pricing, 
    and show confirmation page. Hold reservations do not trigger email.
    """
    if request.method != "POST":
        return redirect("reservation")

    first_name = request.POST.get("first_name")
    last_name = request.POST.get("last_name")
    email = request.POST.get("email")
    phone = request.POST.get("phone")
    check_in_str = request.POST.get("check_in")
    check_out_str = request.POST.get("check_out")
    guests = int(request.POST.get("guests_final"))
    room_type_id = request.POST.get("room_type")
    status = request.POST.get("status", "Hold")

    check_in, check_out, error = parse_dates(check_in_str, check_out_str)
    if error:
        messages.error(request, error)
        return redirect("reservation")

    room_type = get_object_or_404(RoomType, id=room_type_id)
    nights = (check_out - check_in).days
    total_cost = nights * room_type.price_per_night

    expiration_time = timezone.now() + timedelta(hours=24) if status == "Hold" else None

    reservation = Reservation.objects.create(
        customer=request.user.customer if hasattr(request.user, "customer") else None,
        guest_first_name=first_name,
        guest_last_name=last_name,
        guest_email=email,
        guest_phone=phone,
        start_date=check_in,
        end_date=check_out,
        guests=guests,
        room_type=room_type,
        status=status,
        expiration_time=expiration_time,
        total_cost=total_cost
    )

    invalid_emails = []

    # Send email only for Confirmed reservations
    if status == "Confirmed":
        recipients, invalid_emails = validate_emails(email, getattr(request.user, "email", None))
        if recipients:
            subject = f"Moffat Bay Lodge Reservation Confirmation #{reservation.id}"
            body = [
                f"Dear {first_name} {last_name},",
                "",
                "Thank you for choosing Moffat Bay Lodge.",
                f"Your reservation number is: {reservation.id}",
                "",
                "Reservation Details:",
                f"  Room Type: {room_type.name}",
                f"  Check-in: {check_in}",
                f"  Check-out: {check_out}",
                f"  Guests: {guests}",
                f"  Price per night: ${room_type.price_per_night}",
                f"  Nights: {nights}",
                f"  Total cost: ${total_cost}",
            ]
            body.append("\nWe look forward to your stay at Moffat Bay Lodge.")
            send_mail(subject, "\n".join(body), settings.DEFAULT_FROM_EMAIL, list(recipients))

    # Build context for confirmation template
    context = {
        "reservation": reservation,
        "is_hold": status == "Hold",
        "price_per_night": room_type.price_per_night,
        "nights": nights,
        "total_cost": total_cost,
        "guests": guests,  # number of guests included in context
        "invalid_emails": invalid_emails
    }

    return render(request, "pages/confirmation.html", context)

@login_required(login_url='login')
def reservation_detail(request, reservation_id):
    reservation = get_object_or_404(
        Reservation, 
        id=reservation_id, 
        customer=request.user.customer
    )
    return render(request, 'pages/confirmation.html', {"reservation": reservation})

@login_required(login_url='login')
def confirmation(request):
    if request.method != "POST":
        return redirect("reservation")

    # ----- 1. Collect form fields -----
    form_data = {
        "first_name": request.POST.get("first_name", "").strip(),
        "last_name": request.POST.get("last_name", "").strip(),
        "email": request.POST.get("email", "").strip(),  # guest email
        "phone": request.POST.get("phone_number", "").strip(),
        "check_in": request.POST.get("check_in_date", ""),
        "check_out": request.POST.get("check_out_date", ""),
        "guests": request.POST.get("num_guests", ""),
        "room_type": request.POST.get("room_type", ""),
        "additional_emails": request.POST.get("additional_emails", "").strip(),
    }

    # ----- 2. Look up room type and compute pricing -----
    price_per_night = None
    nights = None
    total_cost = None

    room_type_value = form_data["room_type"].strip()
    room_type_obj = None

    if room_type_value:
        if room_type_value.isdigit():
            room_type_obj = RoomType.objects.filter(id=int(room_type_value)).first()

        if room_type_obj is None:
            room_type_obj = RoomType.objects.filter(name__iexact=room_type_value).first()

    if room_type_obj:
        price_per_night = room_type_obj.price_per_night

        if form_data["check_in"] and form_data["check_out"]:
            try:
                check_in_date = datetime.strptime(form_data["check_in"], "%Y-%m-%d").date()
                check_out_date = datetime.strptime(form_data["check_out"], "%Y-%m-%d").date()
                nights = (check_out_date - check_in_date).days
                if nights < 1:
                    nights = 1
                total_cost = price_per_night * nights
            except ValueError:
                pass

    # ----- 3. Reservation number -----
    if "reservation_number" not in request.session:
        request.session["reservation_number"] = generate_reservation_number()
    reservation_number = request.session["reservation_number"]

    # ----- 4. Build context for the template -----
    context = {
        **form_data,
        "price_per_night": price_per_night,
        "nights": nights,
        "total_cost": total_cost,
        "reservation_number": reservation_number,
    }

    # ----- 5. Save ONLY form data + reservation number in the session -----
    session_data = {
        **form_data,
        "reservation_number": reservation_number,
    }
    request.session["reservation_data"] = session_data

     # ----- 6. Build list of email recipients with validation -----
    recipients = set()
    invalid_emails = []  # we'll show these on the confirmation page

    # Helper to safely add an email if it is valid
    def try_add_email(addr: str):
        addr = addr.strip()
        if not addr:
            return
        try:
            validate_email(addr)
            recipients.add(addr)
        except ValidationError:
            invalid_emails.append(addr)

    # 6a. Logged-in user's account email
    if request.user.is_authenticated and request.user.email:
        # usually safe, but we can still validate
        try_add_email(request.user.email)

    # 6b. Guest email typed on the form
    if form_data["email"]:
        try_add_email(form_data["email"])

    # 6c. Additional emails (comma or semicolon separated)
    extra = form_data["additional_emails"]
    if extra:
        separators = extra.replace(";", ",")
        for addr in separators.split(","):
            try_add_email(addr)

    # ----- 7. Send the confirmation email (only to valid recipients) -----
    if recipients:
        subject = f"Moffat Bay Lodge Reservation Confirmation #{reservation_number}"

        body_lines = [
            f"Dear {form_data['first_name']} {form_data['last_name']},",
            "",
            "Thank you for choosing Moffat Bay Lodge.",
            f"Your reservation number is: {reservation_number}",
            "",
            "Reservation Details:",
            f"  Room Type: {room_type_obj.name if room_type_obj else form_data['room_type']}",
            f"  Check-in: {form_data['check_in']}",
            f"  Check-out: {form_data['check_out']}",
            f"  Guests: {form_data['guests']}",
        ]

        if price_per_night is not None:
            body_lines.append(f"  Price per night: ${price_per_night}")
        if nights is not None:
            body_lines.append(f"  Nights: {nights}")
        if total_cost is not None:
            body_lines.append(f"  Total cost: ${total_cost}")

        body_lines.append("")
        body_lines.append("We look forward to your stay at Moffat Bay Lodge.")

        message_body = "\n".join(body_lines)

        if recipients and request.POST.get("status") != "Hold":
            send_mail(
                subject,
                message_body,
                settings.DEFAULT_FROM_EMAIL,
                list(recipients),
                fail_silently=False,
            )

    # ----- 8. Add invalid emails to context so template can show a warning -----
    context["invalid_emails"] = invalid_emails

    # ----- 9. Render confirmation page -----
    return render(request, "pages/confirmation.html", context)

@login_required(login_url='login')
def search(request):
    return render(request, 'pages/search.html')
    
def logout_view(request):
    if request.method == "POST":
        auth_logout(request)
    return redirect('index')
