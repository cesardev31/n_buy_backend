from django.urls import path
from . import views
from . import docs
from django.shortcuts import redirect

app_name = 'chat'

urlpatterns = [
    path('test/', views.chat_test, name='chat_test'),
    path('docs/', docs.chat_docs, name='chat_docs'),
    # Redirigir /chat/ a /chat/test/
    path('', lambda request: redirect('chat:chat_test'), name='chat_home'),
] 