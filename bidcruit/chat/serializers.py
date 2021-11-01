from rest_framework import serializers
from accounts.models import User
from .models import Messages


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SlugRelatedField(many=False, slug_field='email', queryset=User.objects.all())
    receiver_name = serializers.SlugRelatedField(many=False, slug_field='email', queryset=User.objects.all())

    class Meta:
        model = Messages
        fields = ['sender_name', 'receiver_name', 'description', 'time']