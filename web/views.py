from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout

# Create your views here.
def index(request):
    return render(request, 'pages/index.html')

def about(request):
    return render(request, 'pages/about.html')

from django.contrib.auth.decorators import login_required

@login_required(login_url='login')
def account(request):
    return render(request, 'pages/account.html')

def attractions(request):
    return render(request, 'pages/attractions.html')

def confirmation(request):
    return render(request, 'pages/confirmation.html')

def contact(request):
    return render(request, 'pages/contact.html')

#def login(request):
#    return render(request, 'pages/login.html')

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # Create the user
            user = form.save()
            # Log them in immediately after registration
            auth_login(request, user)
            # Send them to the account or home page
            return redirect("account")
    else:
        form = UserCreationForm()

    return render(request, "pages/register.html", {"form": form})

def reservation(request):
    return render(request, 'pages/reservation.html')

def search(request):
    return render(request, 'pages/search.html')
    
def logout_view(request):
    auth_logout(request)      # clears the session and logs the user out
    return redirect('index')  # send them back to the home page
