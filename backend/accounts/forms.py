from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import User


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].label = "Email Address"
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:outline-none',
            'placeholder': 'Enter your registered email'
        })

        self.fields['password'].widget.attrs.update({
            'class': 'w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-orange-500 focus:outline-none',
            'placeholder': '••••••••'
        })


class CitizenRegisterForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True, label="First Name")
    last_name = forms.CharField(max_length=150, required=True, label="Last Name")
    email = forms.EmailField(required=True, label="Email Address")
    phone = forms.CharField(max_length=15, required=True, label="Mobile Number")

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style password fields to match the theme
        if 'password1' in self.fields:
            self.fields['password1'].label = "Create Password"
            self.fields['password1'].widget.attrs.update({
                'placeholder': '••••••••',
                'class': 'w-full pl-12 pr-12 py-4 rounded-2xl bg-gray-50 dark:bg-gray-800 border-2 border-transparent focus:border-eco-500 focus:bg-white dark:focus:bg-gray-700 outline-none transition-all font-bold text-gray-700 dark:text-white'
            })
        if 'password2' in self.fields:
            self.fields['password2'].label = "Confirm Password"
            self.fields['password2'].widget.attrs.update({
                'placeholder': '••••••••',
                'class': 'w-full pl-12 pr-12 py-4 rounded-2xl bg-gray-50 dark:bg-gray-800 border-2 border-transparent focus:border-eco-500 focus:bg-white dark:focus:bg-gray-700 outline-none transition-all font-bold text-gray-700 dark:text-white'
            })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and not email.lower().endswith('@gmail.com'):
            raise forms.ValidationError("Only @gmail.com addresses are allowed.")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        user.role = 'citizen'
        if commit:
            user.save()
        return user