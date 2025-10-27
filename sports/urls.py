from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index-page'),
    path('teams/', views.teams, name='team-list'),
    path('teams/<str:team_name>/', views.rooster, name='team'),
    path('teams/<str:team_name>/<int:pk>', views.profile, name='player'),
    path('legends/', views.legends, name='legends'),
    path('api/more-games/<str:team_name>/<int:amount>', views.get_more_results, name='get_more_results'),
    path('api/more-upcomings/<str:team_name>/<int:amount>', views.get_more_upcomings, name='get_more_upcomings'),
] 