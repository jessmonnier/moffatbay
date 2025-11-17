from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('account/', views.account, name='account'),
    path('attractions/', views.attractions, name='attractions'),
    path('confirmation/', views.confirmation, name='confirmation'),
    path('contact/', views.contact, name='contact'),
<<<<<<< Updated upstream
    path('login/', views.login, name='login'),
=======
    path('login/', auth_views.LoginView.as_view(template_name='pages/login.html'), name='login'),
      path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
>>>>>>> Stashed changes
    path('register/', views.register, name='register'),
    path('reservation/', views.reservation, name='reservation'),
    path('search/', views.search, name='search'),
]