from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'email', 'name', 'role', 'student_type', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model  = User
        fields = ['id', 'email', 'name', 'role', 'student_type', 'password']
        read_only_fields = ['id']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    password     = serializers.CharField(write_only=True, min_length=6, required=False)
    old_password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model  = User
        fields = ['name', 'password', 'old_password']

    def validate(self, data):
        if 'password' in data:
            if 'old_password' not in data:
                raise serializers.ValidationError({'old_password': 'Required when changing password.'})
            if not self.instance.check_password(data['old_password']):
                raise serializers.ValidationError({'old_password': 'Incorrect current password.'})
        return data

    def update(self, instance, validated_data):
        validated_data.pop('old_password', None)
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class AdminPasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(min_length=6)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Returns JWT pair + full user object in a single login response."""
    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data
