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
from ..models import RoomType, Reservation, Customer
from django.db.models import Q
from datetime import timedelta
from django.utils import timezone
from web.views.helpers import get_available_rooms, parse_dates, validate_emails, calculate_total_cost

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
    
    # Allow staff to make reservations for existing customers
    if request.user.is_staff:
        context['all_customers'] = Customer.objects.filter(
            user__is_staff=False
        ).order_by('user__first_name', 'user__last_name')

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
            else:
                for room in context['available_room_types']:
                    nights, total_cost = calculate_total_cost(check_in, check_out, room["price_per_night"])
                    room["nights"] = nights
                    room["total_cost"] = total_cost

    return render(request, 'pages/reservation.html', context)

@login_required
def save_reservation(request):
    """
    Save a new reservation with status 'Hold' or 'Confirmed', calculate pricing, 
    and show confirmation page. Hold reservations do not trigger email.
    """
    if request.method != "POST":
            return redirect("reservation")
        
    # Determine customer
    if request.user.is_staff:
        customer_id = request.POST.get('customer_id')
        if customer_id:
            customer = get_object_or_404(Customer, id=customer_id)
        else:
            messages.error(request, "Please select a customer.")
            return redirect("reservation")
    else:
        customer = getattr(request.user, 'customer', None)
        if not customer:
            messages.error(request, "No customer profile associated with your account.")
            return redirect("reservation")
        
    # Gather customer data from form or selected profile
    first_name = request.POST.get("first_name") or customer.user.first_name
    last_name = request.POST.get("last_name") or customer.user.last_name
    email = request.POST.get("email") or customer.user.email
    phone = request.POST.get("phone") or customer.phone_number
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
    nights, total_cost = calculate_total_cost(check_in, check_out, room_type.price_per_night)

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
            subject = f"Moffat Bay Lodge Reservation Confirmation #{reservation.public_id}"
            body = [
                f"Dear {first_name} {last_name},",
                "",
                "Thank you for choosing Moffat Bay Lodge.",
                f"Your reservation number is: {reservation.public_id}",
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
        "first_name": first_name,
        "last_name": last_name,
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
def reservation_detail(request, public_id):
    reservation = get_object_or_404(
        Reservation, 
        public_id=public_id,
        customer=request.user.customer
    )
    
    # Get room info
    room_type = reservation.room_type
    price_per_night = room_type.price_per_night
    nights, total_cost = calculate_total_cost(
        reservation.start_date, 
        reservation.end_date,
        price_per_night)

    context = {
        "first_name": reservation.guest_first_name,
        "last_name": reservation.guest_last_name,
        "email": reservation.guest_email,
        "phone": reservation.guest_phone,
        "check_in": reservation.start_date,
        "check_out": reservation.end_date,
        "guests": reservation.guests,
        "room_type": room_type.name if room_type else "",
        "price_per_night": price_per_night,
        "nights": nights,
        "total_cost": total_cost,
        "reservation_number": reservation.public_id,   # public facing res number
        "invalid_emails": [],                  # none on detail page
        "reservation": reservation,            # entire object just in case
        "is_hold": reservation.status == "Hold",
    }

    return render(request, 'pages/confirmation.html', context)

@login_required(login_url='login')
def search(request):
    """
    Search reservations that belong to the logged-in user based on customer ID.

    Options:
    - Email: must match searched email, but filter by customer ID
    - Name: first and/or last name, filter by customer ID
    - Public ID: look for reservation number, filter by customer ID
    """
    error_message = None
    results = []

    # For re-populating form fields
    form_email = ""
    form_first_name = ""
    form_last_name = ""
    form_reservation_id = ""

    if request.user.is_staff:
        base_qs = Reservation.objects.all()
    else:
        customer = getattr(request.user, "customer", None)
        if not customer:
            # handle error: no customer profile
            error_message = "No customer profile is associated with your account."
            return render(request, "pages/search.html", {
                "lookup_error": error_message,
                "results": results,
            })
        else:
            base_qs = Reservation.objects.filter(customer=customer)

    if request.method == "POST":
        search_type = request.POST.get("search_type")  # "email", "name", or "reservation_id"

        # Search by email
        if search_type == "email":
            email = request.POST.get("email", "").strip()
            form_email = email

            if not email:
                error_message = "Please enter your email address."
            else:
                results = base_qs.filter(guest_email__iexact=email).order_by("-start_date")
                if not results:
                    error_message = "No reservations were found for this email address."

        # --- Search by first/last name ---
        elif search_type == "name":
            first_name = request.POST.get("first_name", "").strip()
            last_name = request.POST.get("last_name", "").strip()
            form_first_name = first_name
            form_last_name = last_name

            if not first_name and not last_name:
                error_message = "Please enter a first name, last name, or both."
            else:
                qs = base_qs
                if first_name:
                    qs = qs.filter(guest_first_name__icontains=first_name)
                if last_name:
                    qs = qs.filter(guest_last_name__icontains=last_name)
                results = qs.order_by("-start_date")
                if not results:
                    error_message = "No reservations matched your search."

        # --- Search by public_id ---
        elif search_type == "reservation_id":
            reservation_id = request.POST.get("reservation_id", "").strip()
            form_reservation_id = reservation_id

            if not reservation_id:
                error_message = "Please enter a reservation ID."
            else:
                results = base_qs.filter(public_id__iexact=reservation_id)
                if not results:
                    error_message = "No reservations matched this reservation ID."

    context = {
        "lookup_error": error_message,
        "results": results,
        "form_email": form_email,
        "form_first_name": form_first_name,
        "form_last_name": form_last_name,
        "form_reservation_id": form_reservation_id,
    }
    return render(request, "pages/search.html", context)
    


@require_POST
def send_secondary_email(request):
    reservation_id = request.POST.get("reservation_id")
    if not reservation_id:
        # No ID -> nothing to email about, send back to start
        return redirect("reservation")

    reservation = get_object_or_404(Reservation, id=reservation_id)

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