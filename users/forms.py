from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

from .models import User
from .validators import normalize_phone, validate_github_url


class RegisterForm(forms.ModelForm):
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("name", "surname", "email")

    def clean_email(self):
        return self.cleaned_data["email"].lower()

    def _post_clean(self):
        super()._post_clean()
        password = self.cleaned_data.get("password")
        if password:
            try:
                validate_password(password, self.instance)
            except forms.ValidationError as error:
                self.add_error("password", error)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")
        if email and password:
            self.user = authenticate(self.request, email=email.lower(), password=password)
            if self.user is None:
                raise forms.ValidationError("Неверный email или пароль")
        return cleaned_data

    def get_user(self):
        return self.user


class EditProfileForm(forms.ModelForm):
    # Длиннее 12 символов, чтобы принять номер с пробелами и скобками до нормализации.
    phone = forms.CharField(label="Телефон", max_length=20, required=False)

    class Meta:
        model = User
        fields = ("name", "surname", "avatar", "about", "phone", "github_url")
        widgets = {"avatar": forms.FileInput(attrs={"accept": "image/*"})}

    def clean_phone(self):
        phone = self.cleaned_data["phone"]
        if not phone:
            return None
        phone = normalize_phone(phone)
        if User.objects.filter(phone=phone).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Этот номер телефона уже используется.")
        return phone

    def clean_github_url(self):
        github_url = self.cleaned_data["github_url"]
        if github_url:
            validate_github_url(github_url)
        return github_url
