"""
CSD-460 Capstone Blue Team
Moffat Bay Lodge Project
Vee Bell, Deja Faison, Julia Gonzalez, Jess Monnier
Professor Sue Sampson
Developed October thru December of 2025
"""

from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from ..models import Reservation
from web.views.helpers import validate_email

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
        
        # Empty field check
        if not all([first, last, email, phone, password, confirm]):
            messages.error(request, "All fields are required.")
            return redirect("register")
        # Empty password check
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

def logout_view(request):
    if request.method == "POST":
        auth_logout(request)
    return redirect('index')

@login_required(login_url='login')
def account(request):
    user = request.user
    customer = getattr(user, 'customer', None)
    if not customer:
        messages.error(request, "No customer profile found.")
        return redirect('index')
    print(request.POST)

    # Handle form submissions
    if request.method == "POST":
        action = request.POST.get("action")

        # --- Update customer info ---
        if action == "update_info":
            first = request.POST.get("first_name", "").strip()
            last = request.POST.get("last_name", "").strip()
            email = request.POST.get("email", "").strip()
            phone = request.POST.get("phone_number", "").strip()
            address_street = request.POST.get("address_street", "").strip()
            address_city = request.POST.get("address_city", "").strip()
            address_state = request.POST.get("address_state", "").strip()
            address_zipcode = request.POST.get("address_zipcode", "").strip()
            address_country = request.POST.get("address_country", "").strip()

            # Validate required fields
            if not all([first, last, email]):
                messages.error(request, "First name, last name, and email are required.")
            else:
                # Validate email format
                try:
                    validate_email(email)
                except ValidationError:
                    messages.error(request, "Invalid email format.")
                    return redirect("account")

                # Check for duplicate email (username)
                if User.objects.filter(username=email).exclude(id=user.id).exists():
                    messages.error(request, "Email is already in use.")
                    return redirect("account")

                # Update user fields
                user.first_name = first
                user.last_name = last
                user.email = email
                user.username = email
                user.save()

                # Update customer fields
                customer.phone_number = phone
                customer.address_street = address_street
                customer.address_city = address_city
                customer.address_state = address_state
                customer.address_zipcode = address_zipcode
                customer.address_country = address_country
                customer.save()

                messages.success(request, "Your information has been updated.")

        # --- Update password ---
        elif action == "update_password":
            current_password = request.POST.get("current_password", "")
            new_password = request.POST.get("new_password", "")
            confirm_password = request.POST.get("confirm_password", "")

            if not user.check_password(current_password):
                messages.error(request, "Current password is incorrect.")
            elif new_password != confirm_password:
                messages.error(request, "New passwords do not match.")
            elif not new_password:
                messages.error(request, "Password cannot be empty.")
            else:
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                messages.success(request, "Password updated successfully.")

    # --- Prepare context ---
    recent_reservations = Reservation.objects.filter(customer=customer).order_by('-start_date')[:5]
    total_reservations = Reservation.objects.filter(customer=customer).count()

    context = {
        "customer": customer,
        "recent_reservations": recent_reservations,
        "has_more_reservations": total_reservations > 5,
    }
    return render(request, 'pages/account.html', context)