import pytest

from tests.factories import UserFactory


@pytest.fixture
def author():
    return UserFactory()


@pytest.fixture
def assignee():
    return UserFactory()


@pytest.fixture
def other():
    return UserFactory()
