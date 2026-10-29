from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import (
    password_validators_help_text_html,
    validate_password,
)

from .models import User
from .validators import normalize_phone, validate_github_url


class RegisterForm(forms.ModelForm):
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    class Meta:
        model = User
        fields = ("name", "surname", "email")
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "surname": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Требования к паролю зависят от DEBUG, поэтому подсказку берём из валидаторов.
        self.fields["password"].help_text = password_validators_help_text_html()

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
    email = forms.EmailField(
        label="Email", widget=forms.EmailInput(attrs={"autocomplete": "email"})
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

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
    phone = forms.CharField(
        label="Телефон",
        max_length=20,
        required=False,
        widget=forms.TextInput(
            attrs={"autocomplete": "tel", "inputmode": "tel", "placeholder": "+7XXXXXXXXXX"}
        ),
    )

    class Meta:
        model = User
        fields = ("name", "surname", "avatar", "about", "phone", "github_url")
        widgets = {
            "name": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "surname": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "avatar": forms.FileInput(attrs={"accept": "image/*"}),
            "github_url": forms.URLInput(
                attrs={"autocomplete": "url", "placeholder": "https://github.com/username"}
            ),
        }

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
