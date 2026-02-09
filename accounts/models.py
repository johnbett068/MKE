from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.utils import timezone


# -------------------------
# Custom User Manager
# -------------------------
class AccountManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


# -------------------------
# Custom Account Model
# -------------------------
class Account(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)

    objects = AccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


# -------------------------
# Role Model
# -------------------------
class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g. customer, driver
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# -------------------------
# AccountRole (Many-to-Many)
# -------------------------
class AccountRole(models.Model):
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name="roles",
    )
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("account", "role")

    def __str__(self):
        return f"{self.account.email} - {self.role.name}"


# -------------------------
# Profile Model
# -------------------------
class Profile(models.Model):
    account = models.OneToOneField(
        Account,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    address = models.TextField(blank=True)
    verification_level = models.IntegerField(
        default=0
    )  # 0=Unverified, 1=Phone, 2=ID, 3=Business/Vehicle

    def __str__(self):
        return f"Profile of {self.account.email}"