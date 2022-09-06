"""simple_votings_11 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from . import forms
from .views import *

urlpatterns = [
    path('', index),
    path('available_voting/', available_voting),
    path('create_voting/', create_voting),
    path('generate_voting/', generate_voting),
    path('register/', signup),
    path('vote/', vote),
    path('profile/', profile),
    path('change_info/', change_info),
    path('complain/', complain),
    path('edit_voting/', edit_voting),
    path('like_comment/', like_comment),
    path('recovery_password/', recovery_password),
    path('other_users_review/', other_users_review),
    path('user_votes_review/', user_votes_review),
    path('about_us/', about_us),
]