from .models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.hashers import check_password
from django import forms

class RegisterForm(UserCreationForm):
    """회원가입 폼 클래스"""
    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)

        self.fields['user_id'].label = '아이디'
        self.fields['user_id'].widget.attrs.update({     
            'class': 'form-control',
            'autofocus': False,
            'autocomplete': 'off',
        })
        self.fields['password1'].label = '비밀번호'
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
        })
        self.fields['password2'].label = '비밀번호 확인'
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
        })
        self.fields['name'].label = '이름'
        self.fields['name'].widget.attrs.update({
            'class': 'form-control',
            'autocomplete' : 'off',
        })
        self.fields['hp'].label = '핸드폰번호'
        self.fields['hp'].widget.attrs.update({
            'class': 'form-control',
            'autocomplete': 'off',
        })
    terms_and_conditions = forms.BooleanField(
        label='약관에 동의합니다.',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={'required': '회원가입 약관에 동의해야 합니다.'}
    )

    privacy_policy = forms.BooleanField(
        label='약관에 동의합니다.',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={'required': '개인정보 취급방침에 동의해야 합니다.'}
    )

    class Meta:
        model = User
        fields = ['user_id', 'password1', 'password2', 'name', 'hp', 'terms_and_conditions']
    
    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if not any(char.isdigit() for char in password1):
            raise forms.ValidationError("비밀번호는 숫자를 포함해야 합니다.")
        if not any(char.isalpha() for char in password1):
            raise forms.ValidationError("비밀번호는 영문을 포함해야 합니다.")
        if not any(char in '!@#$%^&*()' for char in password1):
            raise forms.ValidationError("비밀번호는 특수문자를 포함해야 합니다.")
        if len(password1) < 8:
            raise forms.ValidationError("비밀번호는 최소 8자 이상입니다.")
        if len(password1) > 20:
            raise forms.ValidationError("비밀번호는 최대 20자 이하입니다.")
        return password1
    
    def clean_terms_agreement(self):
        terms_agreement = self.cleaned_data.get('terms_and_conditions')
        if not terms_agreement:
            raise forms.ValidationError("이용약관에 동의해야 합니다.")
        return terms_agreement
    
    def clean_privacy_policy_agreement(self):
        privacy_policy_agreement = self.cleaned_data.get('privacy_policy')
        if not privacy_policy_agreement:
            raise forms.ValidationError("개인정보 취급방침에 동의해야 합니다.")
        return privacy_policy_agreement
    
    def save(self, commit=True):
        user = super(RegisterForm, self).save(commit=False)
        user.set_password(self.cleaned_data['password1'])  # 비밀번호를 해싱하여 저장
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