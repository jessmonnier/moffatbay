"""
CSD-460 Capstone Blue Team
Moffat Bay Lodge Project
Vee Bell, Deja Faison, Julia Gonzalez, Jess Monnier
Professor Sue Sampson
Developed October thru December of 2025
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings
from ..models import RoomType, Reservation
from datetime import datetime


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

def print_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)

    price_per_night = reservation.price_per_night
    nights = reservation.nights
    total_cost = reservation.total_cost

    context = {
        "reservation": reservation,
        "price_per_night": price_per_night,
        "nights": nights,
        "total_cost": total_cost,
    }

    return render(request, "pages/print_reservation.html", context)