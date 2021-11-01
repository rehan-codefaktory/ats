from django.urls import path
from django.conf.urls import url
from . import views
app_name= 'agency'

urlpatterns = [
    path('agency_registration', views.agency_registration, name="agency_registration"),
    path('agency_home', views.agency_home, name="agency_home"),
]