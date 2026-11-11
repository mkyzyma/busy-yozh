import factory
from django.contrib.auth import get_user_model

DEFAULT_PASSWORD = "Strong-pass-123"


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()
        skip_postgeneration_save = True

    username = factory.Sequence(lambda number: f"user{number}")
    password = factory.PostGenerationMethodCall("set_password", DEFAULT_PASSWORD)

    @classmethod
    def _after_postgeneration(cls, instance, create, results=None):
        if create:
            instance.save(update_fields=["password"])
