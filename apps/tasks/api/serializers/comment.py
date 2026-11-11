from typing import Any

from rest_framework import serializers

from apps.tasks.models import Comment
from apps.tasks.services import add_comment


class CommentSerializer(serializers.ModelSerializer):
    task: serializers.PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(
        read_only=True
    )
    author: serializers.PrimaryKeyRelatedField = serializers.PrimaryKeyRelatedField(
        read_only=True
    )

    class Meta:
        model = Comment
        fields = ("id", "task", "author", "text", "created_at")
        read_only_fields = ("id", "task", "author", "created_at")

    def create(self, validated_data: dict[str, Any]) -> Comment:
        return add_comment(**validated_data)
