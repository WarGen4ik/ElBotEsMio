from django.conf.urls import url

from core.views import CustomObtainAuthToken, CreateUserViewSet, BotStart, BotStop, BotCreate, BotGetAll, \
    BotRetrieveUpdateDelete

urlpatterns = [
    url(r'auth/login/$', CustomObtainAuthToken.as_view(), name='obtain_auth_token'),
    url(r'auth/register/$', CreateUserViewSet.as_view(), name='user_register'),
    url(r'bot/start/$', BotStart.as_view()),
    url(r'bot/stop/$', BotStop.as_view()),
    url(r'bot/create/$', BotCreate.as_view()),
    url(r'bot/get/all/$', BotGetAll.as_view()),
    url(r'bot/delete/(?P<name>.+)/$', BotRetrieveUpdateDelete.as_view()),
    url(r'bot/get/(?P<name>.+)/$', BotRetrieveUpdateDelete.as_view()),
    url(r'bot/update/(?P<name>.+)/$', BotRetrieveUpdateDelete.as_view()),
]