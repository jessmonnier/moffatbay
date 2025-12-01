"""
CSD-460 Capstone Blue Team
Moffat Bay Lodge Project
Vee Bell, Deja Faison, Julia Gonzalez, Jess Monnier
Professor Sue Sampson
Developed October thru December of 2025
"""

from django import forms

class ContactForm(forms.Form):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={
        'placeholder': 'Last Name'
    }))
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'Email Address'
    }))
    message = forms.CharField(widget=forms.Textarea(attrs={
        'placeholder': 'Your message here...',
        'rows': 4,
        'cols': 50
    }))