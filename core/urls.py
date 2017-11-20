from django.conf.urls import url

from core.views import CustomObtainAuthToken, CreateUserViewSet, BotStart, BotStop, BotCreate, BotGetAll, \
    BotRetrieveUpdateDelete, CreateUserPoloniexKey, GetStockExchangeParams, CheckUserAuth

urlpatterns = [
    url(r'auth/login/$', CustomObtainAuthToken.as_view(), name='obtain_auth_token'),
    url(r'auth/register/$', CreateUserViewSet.as_view(), name='user_register'),
    url(r'auth/check/$', CheckUserAuth.as_view()),
    url(r'bot/start/$', BotStart.as_view()),
    url(r'bot/stop/$', BotStop.as_view()),
    url(r'bot/create/$', BotCreate.as_view()),
    url(r'bot/get/all/$', BotGetAll.as_view()),
    url(r'bot/delete/(?P<pk>.+)/$', BotRetrieveUpdateDelete.as_view()),
    url(r'bot/get/(?P<pk>.+)/$', BotRetrieveUpdateDelete.as_view()),
    url(r'bot/update/(?P<pk>.+)/$', BotRetrieveUpdateDelete.as_view()),
    url(r'key/add/$', CreateUserPoloniexKey.as_view()),
    url(r'bot/stock_exchange/params/$', GetStockExchangeParams.as_view()),
]
