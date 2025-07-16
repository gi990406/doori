from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator

class UserManager(BaseUserManager):

    def create_user(self, user_id, password, name, email, **extra_fields):
        if not user_id:
            raise ValueError('아이디를 입력해주세요.')

        email = self.normalize_email(email)
        user = self.model(user_id=user_id, email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_id, password, email, name=None):
        user = self.create_user(user_id, password, name, email)
        user.is_superuser = True
        user.is_staff = True
        user.is_admin = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser, PermissionsMixin):
    user_id = models.CharField(max_length=17, verbose_name="아이디", unique=True)                                              # 아이디
    passwordRegex = RegexValidator(
        regex=r'^(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,16}$',
        message="비밀번호는 영문, 숫자, 특수문자의 조합이어야 하고 8자리에서 16자리 사이여야 합니다."
    )                                                                                                                          # 비밀번호 검증
    password = models.CharField(max_length=300, verbose_name="비밀번호", validators=[passwordRegex])                            # 비밀번호
    name = models.CharField(max_length=10, verbose_name="이름", null=True)                                                      # 이름
    phoneNumberRegex = RegexValidator(regex = r'^01([0|1|6|7|8|9]?)-?([0-9]{3,4})-?([0-9]{4})$')                               # 핸드폰번호 검증
    hp = models.CharField(validators = [phoneNumberRegex], max_length = 11, unique = True, null=True, verbose_name="핸드폰번호") # 핸드폰 번호
    email = models.EmailField(max_length=128, verbose_name="이메일")                                                            # 이메일
    date_joined = models.DateField(default=timezone.now, verbose_name='가입일')

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False, verbose_name="관리자")
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'user_id'
    REQUIRED_FIELDS = ['email']

    objects = UserManager()

    def __str__(self):
        return self.user_id

    class Meta:
        db_table = "회원"
        verbose_name = "회원"
        verbose_name_plural = "회원"

class Terms_and_condition(models.Model):
    user_terms_and_conditions = models.TextField(verbose_name="회원가입 약관")
    privacy_policy = models.TextField(verbose_name="개인정보 취급방침")

    class Meta:
        verbose_name = "회원 약관"
        verbose_name_plural = "회원 약관 관리"

    def __str__(self):
        return f"{'회원 약관'}"