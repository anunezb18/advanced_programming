from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
    path('create_account/', views.create_account, name='create_account'),
    path('sign_in/', views.sign_in, name='sign_in'),
    path('films/', views.films, name='films'),
    path('film/', views.film, name='film'),
    path('my_watchlist/', views.my_watchlist, name='my_watchlist'),
    path('user/', views.user, name='user'),
]