"""
CSD-460 Capstone Blue Team
Moffat Bay Lodge Project
Vee Bell, Deja Faison, Julia Gonzalez, Jess Monnier
Professor Sue Sampson
Developed October thru December of 2025
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from web.forms import ContactForm

def index(request):
    return render(request, 'pages/index.html')

def about(request):
    initial_data = {}
    if request.user.is_authenticated and not request.user.is_staff:
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email
        }
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Send email
            subject = f"Message from {form.cleaned_data['first_name']} {form.cleaned_data['last_name']}"
            message = form.cleaned_data['message']
            from_email = form.cleaned_data['email']
            recipient_list = ['reservations@moffatbaylodge.com']
            try:
                send_mail(subject, message, from_email, recipient_list)
                messages.success(request, "Your message has been sent successfully!")
                return redirect('about')
            except Exception:
                messages.error(request, "An error occurred. Please try again later.")
    else:
        form = ContactForm(initial=initial_data)

    return render(request, 'pages/about.html', {'form': form})

def attractions(request):
    return render(request, 'pages/attractions.html')





