from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:outline-none'
        })

        self.fields['password'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:outline-none'
        })


class CitizenRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'citizen'   # 👈 IMPORTANT
        if commit:
            user.save()
        return user