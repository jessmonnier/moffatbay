from django.shortcuts import render

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
    return render(request, 'pages/register.html')

def reservation(request):
    return render(request, 'pages/reservation.html')

def search(request):
    return render(request, 'pages/search.html')