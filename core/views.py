from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import render, get_object_or_404
from multiprocessing import Value, Process
from rest_framework import parsers, renderers, status
from rest_framework.authtoken.models import Token
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from social_auth.exceptions import AuthException

from bot import settings
from core.models import PoloniexKey
from core.serializers import AuthTokenSerializer, UserSerializer, PoloniexKeySerializer
from BotsConnections.poloniexConn import Poloniex, PoloniexError
# from core.utils.Bot import bot_start
from core.tasks import test


class CustomObtainAuthToken(APIView):
    throttle_classes = ()
    permission_classes = (AllowAny,)
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer

    def post(self, request, *args, **kwargs):
        try:
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            # profile = Profile.objects.get(user=user)
            token, created = Token.objects.get_or_create(user=user)

            return Response({'token': token.key,
                             'user_id': user.id, })
        except AuthException as e:
            return Response({'msg': str(e)})


class CreateUserViewSet(CreateAPIView):
    model = get_user_model()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer
    renderer_classes = (JSONRenderer,)

    def create(self, request, *args, **kwargs):
        if request.data.pop('passwordConfirm') == request.data['password']:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response({"msg": "Пароли не совпадают"}, status=status.HTTP_400_BAD_REQUEST)


class CreateUserPoloniexKey(CreateAPIView):
    model = PoloniexKey
    permission_classes = (AllowAny,)
    serializer_class = PoloniexKeySerializer
    renderer_classes = (JSONRenderer,)

    def create(self, request, *args, **kwargs):
        if self.verificate(request)['result']:
            return super(CreateAPIView, self).create(request, *args, **kwargs)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def verificate(self, request):
        key = request.data.get('key', '')
        secret = request.data.get('secret', '')

        try:
            get_object_or_404(PoloniexKey, key=key, secret=secret)
            return {'error': 'This key and secret are already in use', 'result': False}
        except Http404:
            conn = Poloniex(key, secret)
            try:
                conn.returnBalances()
                return {'result': True}
            except PoloniexError:
                return {'error': 'Your key and/or secret are not usable', 'result': False}


class GetMovingAverage(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        pass


class BotStart(APIView):
    def post(self, request):
        # v = Value('b', True)
        # proc = Process(target=bot_start, args=(v, request.user, request.data['stock'], request.data['pair'], '1111'))
        #
        # proc.start()
        #
        # if request.user.id not in settings.bots:
        #     settings.bots[request.user.id] = dict()
        #
        # if request.data['stock'] not in settings.bots[request.user.id]:
        #     settings.bots[request.user.id][request.data['stock']] = dict()
        #
        # settings.bots[request.user.id][request.data['stock']][request.data['pair']] = v
        test.delay()
        return Response({}, status=status.HTTP_200_OK)


class BotStop(APIView):
    def post(self, request):
        if request.user.id in settings.bots:
            if request.data['stock'] in settings.bots[request.user.id]:
                if request.data['pair'] in settings.bots[request.user.id][request.data['stock']]:
                    stop = settings.bots[request.user.id][request.data['stock']].pop(request.data['pair'])
                    stop.value = False
                    return Response({}, status=status.HTTP_200_OK)

        return Response({'msg': 'No process'}, status=status.HTTP_400_BAD_REQUEST)
