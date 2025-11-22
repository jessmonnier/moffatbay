"""
CSD-460 Capstone Blue Team
Moffat Bay Lodge Project
Vee Bell, Deja Faison, Julia Gonzalez, Jess Monnier
Professor Sue Sampson
Developed October thru December of 2025
"""

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings
import random
import string
from .models import RoomType
from datetime import datetime

# Create your views here.
def index(request):
    return render(request, 'pages/index.html')

def about(request):
    return render(request, 'pages/about.html')

@login_required(login_url='login')
def account(request):
    return render(request, 'pages/account.html')

def attractions(request):
    return render(request, 'pages/attractions.html')

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
        "special_requests": request.POST.get("special_requests", "").strip(),
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

        if form_data["special_requests"]:
            body_lines.append("")
            body_lines.append("Special Requests:")
            body_lines.append(f"  {form_data['special_requests']}")

        body_lines.append("")
        body_lines.append("We look forward to your stay at Moffat Bay Lodge.")

        message_body = "\n".join(body_lines)

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
    
def generate_reservation_number():
    """Create a simple reservation number like MB-12345678."""
    return "MB-" + "".join(random.choices(string.digits, k=8))

def contact(request):
    return render(request, 'pages/contact.html')

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
        user = User.objects.create(
            username=email,     # ← Username stored as email
            email=email,
            first_name=first,
            last_name=last,
            password=make_password(password)
        )

        messages.success(request, "Account created! Please log in.")
        return redirect("login")
    return render(request, "pages/register.html")

def reservation(request):
    return render(request, 'pages/reservation.html')

def search(request):
    return render(request, 'pages/search.html')
    
def logout_view(request):
    if request.method == "POST":
        auth_logout(request)
    return redirect('index')

from .models import Reservation
from django.contrib.auth.decorators import login_required

@login_required
def save_reservation(request):
    if request.method != "POST":
        return redirect("reservation")

    Reservation.objects.create(
        user=request.user,
        first_name=request.POST.get("first_name"),
        last_name=request.POST.get("last_name"),
        email=request.POST.get("email"),
        phone=request.POST.get("phone"),
        check_in=request.POST.get("check_in"),
        check_out=request.POST.get("check_out"),
        guests=request.POST.get("guests"),
        room_type=request.POST.get("room_type"),
        special_requests=request.POST.get("special_requests"),
        is_draft=True,     # ✔ OPTION FOR LATER COMPLETION
    )

    return render(request, "pages/save_success.html")
