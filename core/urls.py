from django.conf.urls import url

from core.views import CustomObtainAuthToken, CreateUserViewSet, BotStart, BotStop

urlpatterns = [
    url(r'auth/login/$', CustomObtainAuthToken.as_view(), name='obtain_auth_token'),
    url(r'auth/register/$', CreateUserViewSet.as_view(), name='user_register'),
    url(r'bot/start/$', BotStart.as_view()),
    url(r'bot/stop/$', BotStop.as_view()),
]