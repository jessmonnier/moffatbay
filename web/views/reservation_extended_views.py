"""
CSD-460 Capstone Blue Team
Moffat Bay Lodge Project
Vee Bell, Deja Faison, Julia Gonzalez, Jess Monnier
Professor Sue Sampson
Developed October thru December of 2025
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings
from django.views.decorators.http import require_POST
from ..models import RoomType, Reservation
from datetime import timedelta
from django.utils import timezone
from web.views.helpers import get_available_rooms, parse_dates, validate_emails

@require_POST
def send_secondary_email(request):
    reservation_id = request.POST.get("reservation_id")
    if not reservation_id:
        # No ID -> nothing to email about, send back to start
        return redirect("reservation")

    reservation = get_object_or_404(Reservation, public_id=reservation_id)

    secondary_email = request.POST.get("secondary_email", "").strip()
    secondary_email_status = None
    secondary_email_error = None

    # Validate the email
    try:
        if not secondary_email:
            raise ValidationError("Please enter an email address.")
        validate_email(secondary_email)
    except ValidationError as e:
        secondary_email_error = f"'{secondary_email}' is not a valid email address. {e}"
    else:
        subject = f"Moffat Bay Lodge Reservation Confirmation #{reservation.public_id}"

        body_lines = [
            f"Dear {reservation.guest_first_name} {reservation.guest_last_name},",
            "",
            "Thank you for choosing Moffat Bay Lodge.",
            f"Your reservation number is: {reservation.public_id}",
            "",
            "Reservation Details:",
            f"  Room Type: {reservation.room_type.name}",
            f"  Check-in: {reservation.start_date}",
            f"  Check-out: {reservation.end_date}",
            f"  Guests: {reservation.guests}",
            f"  Price per night: ${reservation.room_type.price_per_night}",
            f"  Total cost: ${reservation.total_cost}",
        ]
        body_lines.append("")
        body_lines.append("We look forward to your stay at Moffat Bay Lodge.")

        send_mail(
            subject,
            "\n".join(body_lines),
            settings.DEFAULT_FROM_EMAIL,
            [secondary_email],
            fail_silently=False,
        )

        secondary_email_status = f"Confirmation email sent to {secondary_email}."

    # Rebuild the same context you use in save_reservation()
    context = {
        "reservation": reservation,
        "is_hold": reservation.status == "Hold" if hasattr(reservation, "status") else False,
        "price_per_night": reservation.room_type.price_per_night,
        "nights": (reservation.end_date - reservation.start_date).days,
        "total_cost": reservation.total_cost,
        "guests": reservation.guests,
        "invalid_emails": [],
        "secondary_email_status": secondary_email_status,
        "secondary_email_error": secondary_email_error,
    }

    return render(request, "pages/confirmation.html", context)

@require_POST
@login_required(login_url='login')
def cancel_reservation(request, public_id):
    reservation = get_object_or_404(
        Reservation,
        public_id=public_id,
        customer=request.user.customer
    )

    if reservation.status == "Cancelled":
        messages.info(request, "This reservation is already cancelled.")
        return redirect("reservation_detail", public_id=public_id)

    reservation.status = "Cancelled"
    reservation.expiration_time = None
    reservation.save()

    messages.success(request, "Your reservation has been cancelled.")
    return redirect("account")  

@require_POST
@login_required(login_url='login')
def confirm_hold(request, public_id):
    reservation = get_object_or_404(
        Reservation,
        public_id=public_id,
        customer=request.user.customer
    )

    if reservation.status != "Hold":
        messages.error(request, "This reservation is not on hold.")
        return redirect("reservation_detail", public_id=public_id)

    now = timezone.now()
    if reservation.expiration_time and reservation.expiration_time < now:
        messages.error(request, "This hold has expired. Please re-check availability.")
        return redirect("reservation_detail", public_id=public_id)

    # Re-check availability using helper function
    available = get_available_rooms(
        reservation.start_date,
        reservation.end_date,
        num_guests=reservation.guests,
        selected_room_type_id=reservation.room_type.id
    )

    if not available:
        messages.error(request, "The room is no longer available.")
        return redirect("reservation_detail", public_id=public_id)

    # Convert Hold to Confirmed
    reservation.status = "Confirmed"
    reservation.expiration_time = None
    reservation.save()

    # Send confirmation email
    recipients, _ = validate_emails(reservation.guest_email)
    if recipients:
        subject = f"Reservation Confirmed #{reservation.public_id}"
        body = f"""Dear {reservation.guest_first_name},

Your held reservation is now confirmed!

Reservation number: {reservation.public_id}
Room type: {reservation.room_type.name}
Check-in: {reservation.start_date}
Check-out: {reservation.end_date}
Guests: {reservation.guests}
Total cost: ${reservation.total_cost}

We look forward to your stay!
"""
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, list(recipients))

    messages.success(request, "Your reservation is now confirmed.")
    return redirect("reservation_detail", public_id=public_id)

@require_POST
@login_required(login_url='login')
def retry_hold(request, public_id):
    reservation = get_object_or_404(
        Reservation,
        public_id=public_id,
        customer=request.user.customer
    )

    available = get_available_rooms(
        reservation.start_date,
        reservation.end_date,
        reservation.guests,
        reservation.room_type.id,
    )

    if not available:
        messages.error(request, "Unfortunately, the room is no longer available.")
        return redirect("reservation_detail", public_id=public_id)

    # Re-apply 24 hour hold
    reservation.status = "Hold"
    reservation.expiration_time = timezone.now() + timedelta(hours=24)
    reservation.save()

    messages.success(request, "A new hold has been placed on this reservation.")
    return redirect("reservation_detail", public_id=public_id)

@login_required
def reservation_modify(request, public_id):
    reservation = get_object_or_404(Reservation, public_id=public_id)

    # Ensure user owns reservation or is staff
    if not request.user.is_staff and getattr(request.user, 'customer', None) != reservation.customer:
        messages.error(request, "You do not have permission to modify this reservation.")
        return redirect("index")

    if request.method == "POST":
        # ---- 1. Parse dates ----
        check_in_str = request.POST.get("check_in")
        check_out_str = request.POST.get("check_out")

        check_in, check_out, error = parse_dates(check_in_str, check_out_str)
        if error:
            messages.error(request, error)
            return redirect("reservation_modify", public_id=public_id)

        guests = int(request.POST.get("guests_final", reservation.guests))
        room_type_id = request.POST.get("room_type", reservation.room_type.id)

        available_rooms = get_available_rooms(
            check_in,
            check_out,
            num_guests=guests,
            selected_room_type_id=room_type_id,
        )

        if not available_rooms:
            messages.error(request, "No rooms available for the new dates.")
            return redirect("reservation_modify", public_id=public_id)

        # ---- 2. Save updates ----
        reservation.start_date = check_in
        reservation.end_date = check_out
        reservation.guests = guests
        reservation.room_type = get_object_or_404(RoomType, id=room_type_id)
        reservation.save()

        # ======================================================
        # EMAIL LOGIC 
        # ======================================================

        additional_raw = request.POST.get("additional_emails", "").strip()

        # Primary recipients (guest + logged-in user)
        primary_candidates = [
            (reservation.guest_email or "").strip(),
            (getattr(request.user, "email", "") or "").strip(),
        ]

        primary_valid, primary_invalid = validate_emails(
            *[e for e in primary_candidates if e]
        )

        # Additional emails
        additional_valid = set()
        additional_invalid = []

        if additional_raw:
            normalized = additional_raw.replace(";", ",")
            for addr in normalized.split(","):
                addr = addr.strip()
                if not addr:
                    continue
                valid_set, invalid_list = validate_emails(addr)
                if valid_set:
                    additional_valid.update(valid_set)
                if invalid_list:
                    additional_invalid.extend(invalid_list)

        # Remove duplicates
        primary_valid = set(primary_valid)
        additional_valid = set(additional_valid) - primary_valid

        all_invalid = list(primary_invalid) + list(additional_invalid)

        # ---- 3. Email primary recipients ----
        if primary_valid:
            subject = f"Reservation Updated #{reservation.public_id}"
            body = f"""Dear {reservation.guest_first_name} {reservation.guest_last_name},

Your reservation has been updated successfully.

Reservation number: {reservation.public_id}
Room type: {reservation.room_type.name}
Check-in: {reservation.start_date}
Check-out: {reservation.end_date}
Guests: {reservation.guests}

We look forward to your stay!
"""
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                list(primary_valid),
                fail_silently=False,
            )

        # ---- 4. Email additional recipients (fun template) ----
        if additional_valid:
            subject2 = f"Moffat Bay Lodge Reservation Update #{reservation.public_id}"
            body2 = f"""Hello,

{reservation.guest_first_name} {reservation.guest_last_name} invites you on a journey to Moffat Bay Lodge.

Updated Reservation Details:
Reservation number: {reservation.public_id}
Room type: {reservation.room_type.name}
Check-in: {reservation.start_date}
Check-out: {reservation.end_date}
Guests: {reservation.guests}

We look forward to welcoming you!
"""
            send_mail(
                subject2,
                body2,
                settings.DEFAULT_FROM_EMAIL,
                list(additional_valid),
                fail_silently=False,
            )

        # ---- 5. Messages ----
        if all_invalid:
            messages.error(
                request,
                "These email address(es) were invalid and were not emailed: "
                + ", ".join(all_invalid)
            )

        messages.success(request, "Reservation updated successfully.")
        return redirect("reservation_detail", public_id=reservation.public_id)

    # ===============================
    # GET REQUEST
    # ===============================
    initial_data = {
        "check_in": reservation.start_date,
        "check_out": reservation.end_date,
        "guests": reservation.guests,
        "room_type": reservation.room_type.id,
        "first_name": reservation.guest_first_name,
        "last_name": reservation.guest_last_name,
        "email": reservation.guest_email,
        "phone": reservation.guest_phone,
    }

    context = {
        "reservation": reservation,
        "initial_data": initial_data,
        "room_types": RoomType.objects.all().order_by("name"),
    }

    return render(request, "pages/reservation_modify.html", context)
