"""
CSD-460 Capstone Blue Team
Moffat Bay Lodge Project
Vee Bell, Deja Faison, Julia Gonzalez, Jess Monnier
Professor Sue Sampson
Developed October thru December of 2025
"""

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('account/', views.account, name='account'),
    path('attractions/', views.attractions, name='attractions'),
    # path('confirmation/', views.confirmation, name='confirmation'),
    # path('contact/', views.contact, name='contact'),
    path('login/', auth_views.LoginView.as_view(template_name='pages/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('login/', auth_views.LoginView.as_view(template_name='pages/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    path('reservation/', views.reservation, name='reservation'),
    path('reservation/save/', views.save_reservation, name='save_reservation'),
    path('reservation/<slug:public_id>/', views.reservation_detail, name='reservation_detail'),
    path('search/', views.search, name='search'),
    path("send-secondary-email/", views.send_secondary_email, name="send_secondary_email"),
    path("reservation/<slug:public_id>/confirm/", views.confirm_hold, name="confirm_hold_reservation"),
    path("reservation/<slug:public_id>/cancel/", views.cancel_reservation, name="cancel_reservation"),
    path("reservation/<slug:public_id>/modify/", views.reservation_modify, name="reservation_modify"),
    path("reservation/<slug:public_id>/retry/", views.retry_hold, name="retry_hold_availability"),
]
