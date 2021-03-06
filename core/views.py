import pymongo
from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import get_object_or_404
from multiprocessing import Value, Process
from rest_framework import parsers, renderers, status
from rest_framework.authtoken.models import Token
from rest_framework.generics import CreateAPIView, ListAPIView, RetrieveUpdateDestroyAPIView, RetrieveAPIView, \
    UpdateAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
import pyotp

from bot import settings
from core.models import PoloniexKey, Strategy
from core.serializers import AuthTokenSerializer, UserSerializer, PoloniexKeySerializer, StrategySerializer, \
    StrategyListSerializer, AuthException
from core.utils import perform_indicators_to_str, perform_str_to_indicator, get_stock_exchange_params, \
    get_key_and_secret, get_conn
from core.utils.Bot import bot_start
from core.utils.BotConn import BotConn
from core.utils.InputDataVerification import InputDataVerification, VerifyException


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

            if user.profile.two_factor_auth:
                return Response({'status': '2-fa'}, status=status.HTTP_200_OK)

            token, created = Token.objects.get_or_create(user=user)

            return Response({'token': token.key,
                             'user_id': user.id, })
        except AuthException as e:
            return Response({'msg': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class Confirm2FA(APIView):
    throttle_classes = ()
    permission_classes = (AllowAny,)
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        auth = pyotp.TOTP(user.profile.base_32)
        if auth.verify(request['code']):
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key,
                             'user_id': user.id, })

        return Response({'error': 'code is not valid'}, status=status.HTTP_400_BAD_REQUEST)


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


class BotStart(APIView):
    def post(self, request):
        data = request.data.copy()
        data.pop('id')
        # key, secret = get_key_and_secret(request.user, data['stock_exchange'])
        # verify = InputDataVerification(data['stock_exchange'], key, secret)
        # try:
        #     if 'depo_percent' in data:
        #         verify.verify_all(currency=data['currency_1'],
        #                           depo_percent=data['depo_percent'],
        #                           pair='{}_{}'.format(data['currency_1'], data['currency_2']))
        #     else:
        #         verify.verify_all(currency=data['currency_1'],
        #                           depo=data['depo'],
        #                           pair='{}_{}'.format(data['currency_1'], data['currency_2']))
        # except VerifyException as ex:
        #     return Response({'error': str(ex)}, status=status.HTTP_400_BAD_REQUEST)

        v = Value('b', True)
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
        settings.bots[request.user.id][request.data['stock_exchange']][pair] = {'stop': v, 'pid': pid, 'id': request.data['id']}

        return Response({}, status=status.HTTP_200_OK)


class BotStop(APIView):
    def post(self, request):
        if request.user.id in settings.bots:
            if request.data['stock_exchange'] in settings.bots[request.user.id]:
                if request.data['pair'] in settings.bots[request.user.id][request.data['stock_exchange']]:
                    bot_settings = settings.bots[request.user.id][request.data['stock_exchange']].pop(
                        request.data['pair'])
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
    renderer_classes = (JSONRenderer,)

    def get_queryset(self):
        return Strategy.objects.filter(user=self.request.user, isStrategy=False)


class StrategiesGetAll(ListAPIView):
    model = Strategy
    serializer_class = StrategyListSerializer
    renderer_classes = (JSONRenderer,)

    def get_queryset(self):
        return Strategy.objects.filter(user=self.request.user, isStrategy=True)


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
        try:
            InputDataVerification(request.data['stock_exchange']).verify_pair('{}_{}'.format(request.data['currency_1'],
                                                                                            request.data['currency_2']))
        except VerifyException as ex:
            return Response({'message': str(ex)}, status=status.HTTP_400_BAD_REQUEST)
        except KeyError:
            pass
        request.data['user'] = request.user.id
        try:
            request.data['indicators'] = perform_indicators_to_str(request.data['indicators'])
        except KeyError as ex:
            print(ex)

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

        data['isBotWorking'] = False
        return Response(data, status=status.HTTP_200_OK)


class GetStockExchangeParams(APIView):
    def post(self, request):
        return Response(get_stock_exchange_params(request.data['stock_exchange'],
                                                  BotConn(request.data['stock_exchange'])),
                        status=status.HTTP_200_OK)


class Get2FAQR(APIView):
    permission_classes = (AllowAny, )

    def get(self, request):
        base_32 = pyotp.random_base32()
        otp_path = pyotp.totp.TOTP(base_32).provisioning_uri(request.user.email, issuer_name="El bot es mio")
        return Response({'qr_code': otp_path, 'base_32': base_32}, status=status.HTTP_200_OK)


class Enable2FA(APIView):
    def post(self, request):
        auth = pyotp.totp.TOTP(request.data['base_32'])
        if auth.verify(request.data['code']) and request.user.check_password(request.data['password']):
            request.user.profile.two_factor_auth = True
            request.user.profile.base_32 = request.data['base_32']
            request.user.profile.save()
            return Response({"status": True}, status=status.HTTP_200_OK)
        return Response({"status": False}, status=status.HTTP_400_BAD_REQUEST)


class Disable2FA(APIView):
    def post(self, request):
        auth = pyotp.totp.TOTP(settings.SECRET_KEY)
        if auth.verify(request.data['code']) and request.user.check_password(request.data['password']):
            request.user.profile.two_factor_auth = False
            request.user.profile.save()
            return Response({"status": True}, status=status.HTTP_200_OK)
        return Response({"status": False}, status=status.HTTP_400_BAD_REQUEST)


class BotGetLogs(RetrieveAPIView):
    model = Strategy
    queryset = Strategy.objects.all()
    serializer_class = StrategySerializer
    renderer_classes = (JSONRenderer,)
    lookup_field = 'pk'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        db = get_conn('mongodb://root:root@localhost:27017/elbotesmio')
        data = db.logs.find({'pair': '{}_{}'.format(serializer.data['currency_1'], serializer.data['currency_2']),
                             'stock_exchange': serializer.data['stock_exchange'],
                             'user_id': request.user.id}).sort([("date", pymongo.DESCENDING), ])
        ret = list()
        for i in data:
            i.pop('_id')
            ret.append(i)
        return Response(ret, status=status.HTTP_200_OK)


class RetrieveUpdateUser(RetrieveUpdateAPIView):
        queryset = get_user_model().objects.all()
        serializer_class = UserSerializer
        renderer_classes = (JSONRenderer,)
        lookup_field = 'pk'
