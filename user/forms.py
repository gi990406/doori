from .models import User
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password
from django import forms
import re
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm

User = get_user_model()

PASSWORD_RE = re.compile(r'^(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,16}$')

class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label="비밀번호",
        widget=forms.PasswordInput(attrs={"class": "m_text", "maxlength": "16"}),
        help_text="영문/숫자/특수문자 조합, 8~16자"
    )
    password2 = forms.CharField(
        label="비밀번호 확인",
        widget=forms.PasswordInput(attrs={"class": "m_text", "maxlength": "16"})
    )

    class Meta:
        model = User
        fields = ["user_id", "name", "email", "hp"]  # password는 제외
        widgets = {
            "user_id": forms.TextInput(attrs={"class": "m_text mb_id", "maxlength": "20"}),
            "name": forms.TextInput(attrs={"class": "m_text"}),
            "email": forms.EmailInput(attrs={"class": "m_text", "maxlength": "100"}),
            "hp": forms.TextInput(attrs={"class": "m_text", "maxlength": "11"}),
        }
        labels = {
            "user_id": "아이디",
            "name": "이름",
            "email": "E-mail",
            "hp": "핸드폰번호",
        }

    def clean_user_id(self):
        uid = self.cleaned_data["user_id"].strip()
        if len(uid) < 3:
            raise ValidationError("아이디는 3자 이상이어야 합니다.")
        # 영문/숫자 만 허용
        if not re.fullmatch(r'[A-Za-z0-9]+', uid):
            raise ValidationError("아이디는 영문, 숫자만 입력 가능합니다.")
        return uid

    def clean_password1(self):
        pw = self.cleaned_data["password1"]
        if not PASSWORD_RE.match(pw):
            raise ValidationError("비밀번호는 영문, 숫자, 특수문자의 조합, 8~16자여야 합니다.")
        return pw

    def clean(self):
        cleaned = super().clean()
        pw1 = cleaned.get("password1")
        pw2 = cleaned.get("password2")
        if pw1 and pw2 and pw1 != pw2:
            self.add_error("password2", "비밀번호가 일치하지 않습니다.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])  # 해시 저장
        if commit:
            user.save()
        return user

class LoginForm(forms.Form):
    """로그인 forms"""
    user_id = forms.CharField(
        widget = forms.TextInput(
        attrs = {'class': 'form-control','autocomplete' : 'off',}),
        error_messages = {'required': '아이디를 입력해주세요.'},
        max_length = 17,
        label = '아이디'
    )
    password = forms.CharField(
        widget = forms.PasswordInput(
        attrs = {'class': 'form-control',}),
        error_messages = {'required': '비밀번호를 입력해주세요.'},
        label = '비밀번호'
    )

    def clean(self):
        cleaned_data = super().clean()
        user_id = cleaned_data.get('user_id')
        password = cleaned_data.get('password')

        if user_id and password:
            try:
                user = User.objects.get(user_id=user_id)
            except User.DoesNotExist:
                self.add_error('user_id', '아이디가 존재하지 않습니다.')
                return

            if not check_password(password, user.password): # 해시화된 비밀번호 검사
                # from django.contrib.auth.hashers import check_password
                self.add_error('password', '비밀번호가 틀렸습니다.')

class ProfileEditForm(forms.ModelForm):
    # 비밀번호는 옵션: 입력하면 변경됨
    password1 = forms.CharField(
        label="새 비밀번호",
        widget=forms.PasswordInput(attrs={"class": "m_text", "maxlength": "16"}),
        required=False,
        help_text="영문/숫자/특수문자 조합, 8~16자 (변경 시에만 입력)"
    )
    password2 = forms.CharField(
        label="새 비밀번호 확인",
        widget=forms.PasswordInput(attrs={"class": "m_text", "maxlength": "16"}),
        required=False
    )

    class Meta:
        model = User
        fields = ["email", "hp"]  # user_id, name 은 읽기전용 표시만
        widgets = {
            "email": forms.EmailInput(attrs={"class": "m_text", "maxlength": "100", "size": "38"}),
            "hp": forms.TextInput(attrs={"class": "m_text", "maxlength": "11"}),
        }
        labels = {
            "email": "E-mail",
            "hp": "핸드폰번호",
        }

    def clean(self):
        cleaned = super().clean()
        pw1, pw2 = cleaned.get("password1"), cleaned.get("password2")
        if pw1 or pw2:
            if not pw1 or not pw2:
                raise ValidationError("새 비밀번호와 확인을 모두 입력해주세요.")
            if pw1 != pw2:
                raise ValidationError("새 비밀번호가 일치하지 않습니다.")
            if not PASSWORD_RE.match(pw1):
                raise ValidationError("비밀번호는 영문/숫자/특수문자 조합, 8~16자여야 합니다.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        pw = self.cleaned_data.get("password1")
        if pw:
            user.set_password(pw)
        if commit:
            user.save()
        return user

class FindIDForm(forms.Form):
    name  = forms.CharField(label="이름", max_length=50)
    email = forms.EmailField(label="이메일")

class PasswordResetMatchForm(forms.Form):
    user_id = forms.CharField(label="아이디", max_length=17)
    name    = forms.CharField(label="이름", max_length=10)
    email   = forms.EmailField(label="이메일", max_length=128)
    hp      = forms.CharField(label="휴대폰", max_length=11, help_text="01012345678")

class PasswordResetNewForm(forms.Form):
    new_password1 = forms.CharField(label="새 비밀번호", widget=forms.PasswordInput, min_length=8)
    new_password2 = forms.CharField(label="새 비밀번호 확인", widget=forms.PasswordInput, min_length=8)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("new_password1") != cleaned.get("new_password2"):
            self.add_error("new_password2", "비밀번호가 일치하지 않습니다.")
        return cleaned
