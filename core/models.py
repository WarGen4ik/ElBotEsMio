from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.contrib.postgres.fields import ArrayField
from django.db import models
from fernet_fields import EncryptedCharField


class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError('Users must have an email address')

        user = self.model(
            email=self.normalize_email(email),
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
    )

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def get_full_name(self):
        # The user is identified by their email address
        return self.email

    def get_short_name(self):
        # The user is identified by their email address
        return self.email

    def has_perm(self, perm, obj=None):
        """Does the user have a specific permission?"""
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        """Does the user have permissions to view the app `app_label`?"""
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        """Is the user a member of staff?"""
        # Simplest possible answer: All admins are staff
        return self.is_admin

    def __str__(self):
        return self.email


class Profile(models.Model):
    user = models.OneToOneField(User)
    phone_number = models.CharField(max_length=30)
    two_factor_auth = models.BooleanField(default=False)
    base_32 = models.CharField(max_length=63, default='')
#
# class Logs(models.Model):
#     user = models.ForeignKey(User)
#     stock_exchange = models.CharField(max_length=50)
#     pair = models.CharField(max_length=20)
#     date = models.DateTimeField()
#     message = models.CharField(max_length=255)


class Strategy(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(max_length=50)
    stock_exchange = models.CharField(max_length=30, blank=True)
    currency_1 = models.CharField(max_length=30, blank=True)
    currency_2 = models.CharField(max_length=30, blank=True)
    stop_loss = models.FloatField(default=0)
    profit = models.FloatField(default=0)
    depo = models.FloatField(default=0)
    candle_time = models.IntegerField(default=0)
    indicators = ArrayField(ArrayField(models.CharField(max_length=255, blank=True), blank=True), blank=True)
    isStrategy = models.BooleanField()  # True - strategy, False - bot

    def __str__(self):
        return self.name


class KeySecret(models.Model):
    key = models.CharField(max_length=255)
    secret = models.CharField(max_length=255)

    class Meta:
        abstract = True


class PoloniexKey(KeySecret):
    user = models.ForeignKey(User)
    pass

    def __str__(self):
        return str(self.user)
