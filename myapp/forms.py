from django import forms
from django.contrib.auth import get_user_model
from .models import CustomUser, Profile
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2"]
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Enter Username", "class": "form-control"}),
            "email": forms.EmailInput(attrs={"placeholder": "Enter Email", "class": "form-control"}),
            "password1": forms.PasswordInput(attrs={"placeholder": "Enter Password", "class": "form-control"}),
            "password2": forms.PasswordInput(attrs={"placeholder": "Confirm Password", "class": "form-control"}),
        }
        help_texts = {f: None for f in fields}

User = get_user_model()
# ---------------- User Profile Form ----------------
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['display_name', 'avatar', 'preferences',]
        widgets = {
            'display_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Display Name'
            }),
            'preferences': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Your preferences',
                'rows': 4
            }),
            'avatar': forms.ClearableFileInput(attrs={
                'class': 'form-control-file'
            }),
        }

# ---------------- Optional: User Update Form ----------------
# Use this if you want to allow updating username separately
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Username'
            }),
        }
