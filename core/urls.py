from django.conf.urls import url

from core.views import CustomObtainAuthToken, CreateUserViewSet

urlpatterns = [
    url(r'login/$', CustomObtainAuthToken.as_view(), name='obtain_auth_token'),
    url(r'register/$', CreateUserViewSet.as_view(), name='user_register'),
]