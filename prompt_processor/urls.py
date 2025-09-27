# prompt_processor/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('convert/', views.convert_prompt, name='convert_prompt'),
    path('review/<int:conversion_id>/', views.review, name='review'),
    path('feedback/<int:conversion_id>/', views.save_feedback, name='save_feedback'),
    path('history/', views.history, name='history'),
    path('api/convert/', views.api_convert, name='api_convert'),
]
