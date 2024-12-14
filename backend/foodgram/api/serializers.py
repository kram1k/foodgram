from django.utils.crypto import get_random_string
from rest_framework import serializers

from users.models import User

from .contsants import MAX_CODE_LENGHT


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True, validators=[])
    email = serializers.EmailField(required=True, validators=[])

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'username',
            'email',
            'role',
        )

    def create(self, validated_data):
        user, created = User.objects.get_or_create(
            email=validated_data['email'], defaults=validated_data
        )
        if created:
            confirmation_code = get_random_string(length=MAX_CODE_LENGHT)
            user.confirmation_code = confirmation_code
            user.save()
        return user

    def validate(self, data):
        email = data.get('email')
        username = data.get('username')
        existing_user = User.objects.filter(
            email=email, username=username
        ).first()
        if existing_user:
            return data
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                'Адрес электронной почты уже существует.'
            )
        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                'Имя пользователя уже существует.'
            )
        return data
