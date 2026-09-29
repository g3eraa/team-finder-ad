from django import forms
from django.contrib.auth import authenticate

from .models import User
from .validators import normalize_phone, validate_github_url
