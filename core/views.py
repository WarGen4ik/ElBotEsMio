from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import get_object_or_404
from multiprocessing import Value, Process
from rest_framework import parsers, renderers, status
from rest_framework.authtoken.models import Token
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from bot import settings
from core.models import PoloniexKey, Strategy
from core.serializers import AuthTokenSerializer, UserSerializer, PoloniexKeySerializer, StrategySerializer, \
    StrategyListSerializer, AuthException
from BotsConnections.poloniexConn import Poloniex, PoloniexError
from core.utils import perform_indicators_to_str, perform_str_to_indicator, get_stock_exchange_params
from core.utils.Bot import bot_start
from core.utils.BotConn import BotConn
from core.utils.InputDataVerification import InputDataVerification


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
            return Response({'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)


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


class CheckUserAuth(APIView):
    def post(self, request):
        return Response(status=status.HTTP_200_OK)


class CreateUserPoloniexKey(CreateAPIView):
    model = PoloniexKey
    permission_classes = (AllowAny,)
    serializer_class = PoloniexKeySerializer
    renderer_classes = (JSONRenderer,)

    def create(self, request, *args, **kwargs):
        if self.verificate(request)['result']:
            request.data['user'] = request.user.id
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    def verificate(self, request):
        key = request.data.get('key', '')
        secret = request.data.get('secret', '')

        try:
            get_object_or_404(PoloniexKey, key=key, secret=secret)
            return {'error': 'This key and secret are already in use', 'result': False}
        except Http404:
            verify = InputDataVerification('poloniex', key, secret)

            ret = {'result': verify.verify_key_secret()}
            if not ret['result']:
                ret['error'] = 'Your key and/or secret are not working'

            return ret


class GetMovingAverage(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        pass


class BotStart(APIView):
    def post(self, request):
        v = Value('b', True)
        data = request.data.copy()
        data['v'] = v
        data['user_id'] = request.user.id
        proc = Process(target=bot_start, args=(data,))

        # bot_start(data)
        proc.start()
        pid = proc.pid

        if request.user.id not in settings.bots:
            settings.bots[request.user.id] = dict()

        if request.data['stock_exchange'] not in settings.bots[request.user.id]:
            settings.bots[request.user.id][request.data['stock_exchange']] = dict()

        pair = request.data['currency_1'] + '_' + request.data['currency_2']

        try:
            if settings.bots[request.user.id][request.data['stock_exchange']][pair]['stop'] is True:
                return Response({'msg': 'Bot is working now'}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError:
            pass
        settings.bots[request.user.id][request.data['stock_exchange']][pair] = {'stop': v, 'id': pid}

        return Response({}, status=status.HTTP_200_OK)


class BotStop(APIView):
    def post(self, request):
        if request.user.id in settings.bots:
            if request.data['stock_exchange'] in settings.bots[request.user.id]:
                if request.data['pair'] in settings.bots[request.user.id][request.data['stock_exchange']]:
                    bot_settings = settings.bots[request.user.id][request.data['stock_exchange']].pop(request.data['pair'])
                    bot_settings['stop'].value = False
                    return Response({}, status=status.HTTP_200_OK)

        return Response({'msg': 'No process'}, status=status.HTTP_400_BAD_REQUEST)


class BotCreate(CreateAPIView):
    model = Strategy
    serializer_class = StrategySerializer
    renderer_classes = (JSONRenderer,)

    def create(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        request.data['indicators'] = [[], ]
        request.data['isStrategy'] = True
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        serializer.data['message'] = 'Bot has been created'
        return Response(serializer.data,
                        status=status.HTTP_201_CREATED, headers=headers)


class BotGetAll(ListAPIView):
    model = Strategy
    serializer_class = StrategyListSerializer
    renderer_classes = (JSONRenderer, )

    def get_queryset(self):
        return Strategy.objects.filter(user=self.request.user)


class BotRetrieveUpdateDelete(RetrieveUpdateDestroyAPIView):
    model = Strategy
    queryset = Strategy.objects.all()
    serializer_class = StrategySerializer
    renderer_classes = (JSONRenderer,)
    lookup_field = 'pk'

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        pk = instance.pk
        instance.delete()
        return Response({"id": pk, "deleted": True}, status=status.HTTP_200_OK)

    def update(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        request.data['indicators'] = perform_indicators_to_str(request.data['indicators'])

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = dict(serializer.data.copy())
        data['indicators'] = perform_str_to_indicator(data['indicators'])
        if data['stock_exchange'] != '':
            data.update(get_stock_exchange_params(data['stock_exchange'], BotConn(data['stock_exchange'])))
        return Response(data)


class GetStockExchangeParams(APIView):
    def post(self, request):
        return Response(get_stock_exchange_params(request.data['stock_exchange'],
                                                  BotConn(request.data['stock_exchange'])),
                        status=status.HTTP_200_OK)
