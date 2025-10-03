from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password

User = get_user_model()

class CustomAuthBackend(BaseBackend):
    """
    Allows login with:
    - The actual password set during registration
    - OR the local part of the email (before @)
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        # If password matches the one user set
        if check_password(password, user.password):
            return user

        # If password matches the email local-part (xyz in xyz@gmail.com)
        if user.email and user.email.split('@')[0] == password:
            return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
