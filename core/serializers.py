from django.contrib.auth import get_user_model, authenticate
from rest_framework import serializers
from social_auth.exceptions import AuthException

from core.models import PoloniexKey, User, Profile

from django.utils.translation import ugettext_lazy as _


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.CharField(label=_("Email"))
    password = serializers.CharField(label=_("Password"), style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(email=email, password=password)

            if user:
                if not user.is_active:
                    msg = _('Данный юзер отключен')
                    raise AuthException(msg)
            else:
                msg = _('Неверный логин и/или пароль.')
                raise AuthException(msg)
        else:
            msg = _('Must include "email" and "password".')
            raise AuthException(msg)

        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = ('id', 'phone_number',)


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    profile = UserProfileSerializer()

    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        serializer = UserProfileSerializer(data=profile_data)
        if serializer.is_valid():
            user = get_user_model().objects.create(email=validated_data['email'])
            user.set_password(validated_data['password'])
            user.save()

            Profile.objects.create(user=user, **profile_data)
            return user

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile')
        serializer = UserProfileSerializer(instance, data=profile_data)
        if serializer.is_valid():
            instance.email = validated_data.get('email', instance.email)
            instance.save()

            profile = Profile.objects.get(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

            return instance

    class Meta:
        model = User
        fields = ('email', 'password', 'profile')


class PoloniexKeySerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        poloniex_key = PoloniexKey.objects.create(user=validated_data.pop('user'))
        poloniex_key.key = validated_data.pop('key')
        poloniex_key.secret = validated_data.pop('secret')
        poloniex_key.save()

        return poloniex_key

    def update(self, instance, validated_data):
        instance.key = validated_data.get('key', instance.key)
        instance.secret = validated_data.get('secret', instance.secret)
        instance.save()

        return instance

    class Meta:
        model = PoloniexKey
        fields = ('id', 'key', 'secret')
