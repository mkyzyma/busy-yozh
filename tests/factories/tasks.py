import factory

from apps.tasks.models import Comment, Task
from tests.factories import UserFactory


class TaskFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Task

    title = factory.Sequence(lambda number: f"Task {number}")
    description = "Test task description"
    author = factory.SubFactory(UserFactory)


class CommentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Comment

    task = factory.SubFactory(TaskFactory)
    author = factory.SubFactory(UserFactory)
    text = factory.Sequence(lambda number: f"Comment {number}")
