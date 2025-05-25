from django.contrib.auth.backends import ModelBackend
from .models import User

class StudentIDAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        # username here will be the student_id from the login form
        try:
            user = User.objects.get(student_id__iexact=username)
        except User.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None 