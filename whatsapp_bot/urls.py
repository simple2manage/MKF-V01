from django.urls import path
from .views import webhook, TriggerMessageView

urlpatterns = [
    path('webhook/', webhook, name="webhook"),
    path('trigger/', TriggerMessageView.as_view(), name="trigger-message"),
]
