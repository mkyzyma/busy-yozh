from rest_framework.generics import ListAPIView

from apps.accounts.api.serializers import UserSerializer
from apps.accounts.models import User


class UserListAPIView(ListAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.filter(is_active=True).order_by("username")
