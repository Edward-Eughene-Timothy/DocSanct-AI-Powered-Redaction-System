from django.urls import path
from . import main

urlpatterns = [
    path('', main.home, name='home'),
    path('upload/', main.upload_file, name='upload_file'),
]
