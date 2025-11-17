from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.hashers import make_password

# Create your views here.
def index(request):
    return render(request, 'pages/index.html')

def about(request):
    return render(request, 'pages/about.html')

def account(request):
    return render(request, 'pages/account.html')

def attractions(request):
    return render(request, 'pages/attractions.html')

def confirmation(request):
    return render(request, 'pages/confirmation.html')

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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        
        #Empty field check
        if not all([first, last, email, phone, password, confirm]):
            messages.error(request, "All fields are required.")
            return redirect("register")
        #Empty password check
        if not password:
            messages.error(request, "Password cannot be empty.")
            return redirect("register")
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        return redirect("login")
=======
        return redirect("index")
>>>>>>> Stashed changes
=======
        return redirect("index")
>>>>>>> Stashed changes
=======
        return redirect("index")
>>>>>>> Stashed changes
=======
        return redirect("index")
>>>>>>> Stashed changes
    return render(request, 'pages/register.html')

def reservation(request):
    return render(request, 'pages/reservation.html')

def search(request):
    return render(request, 'pages/search.html')