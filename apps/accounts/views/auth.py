from django.urls import reverse_lazy
from django.views.generic import CreateView

from apps.accounts.forms import RegistrationForm
from apps.accounts.models import User


class SignUpView(CreateView):
    model = User
    form_class = RegistrationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("accounts:login")
