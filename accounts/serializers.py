from rest_framework import serializers
from .models import CustomUser
import re


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'name', 'phone_number', 'email', 'created_at', 'updated_at')


class BaseSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(required=True)
    mpin = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    confirm_mpin = serializers.CharField(write_only=True, style={'input_type': 'password'})
    email = serializers.EmailField(required=False)
    fcm_token = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = ['name', 'phone_number', 'email', 'fcm_token', 'user_type', 'mpin', 'confirm_mpin']

    def validate_phone_number(self, value):
        phone_number = value.replace(" ", "").replace("-", "")
        if not phone_number.startswith("+91"):
            phone_number = f"+91{phone_number}"

        if CustomUser.objects.filter(phone_number=phone_number, is_verified=True).exists():
            raise serializers.ValidationError("User with this phone number already exists and is verified.")

        if len(phone_number) != 13 or not phone_number[3:].isdigit():
            raise serializers.ValidationError("Invalid phone number format.")
        return phone_number

    def validate(self, attrs):
        mpin = attrs.get('mpin')
        confirm_mpin = attrs.get('confirm_mpin')

        if mpin != confirm_mpin:
            raise serializers.ValidationError("MPIN and Confirm MPIN do not match.")

        # You can add more MPIN rules here (e.g., length, digit-only)
        if len(mpin) < 4 or not mpin.isdigit():
            raise serializers.ValidationError("MPIN must be at least 4 digits.")

        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_mpin')
        mpin = validated_data.pop('mpin')
        user = CustomUser(**validated_data)
        user.set_password(mpin)  # still uses set_password internally
        user.save()
        return user


class ManagerSignUpSerializer(BaseSerializer):
    pass


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    mpin = serializers.CharField(style={'input_type': 'password'}, trim_whitespace=False)
    apk_type = serializers.CharField()
    fcm_token = serializers.CharField(required=False, allow_blank=True)

    def validate_phone_number(self, value):
        phone_number = value.replace(" ", "").replace("-", "")
        if not phone_number.startswith("+91"):
            phone_number = f"+91{phone_number}"

        if len(phone_number) != 13 or not phone_number[3:].isdigit():
            raise serializers.ValidationError("Invalid phone number format.")
        return phone_number

    def validate(self, attrs):
        phone_number = self.validate_phone_number(attrs.get('phone_number'))
        mpin = attrs.get('mpin')
        apk_type = attrs.get('apk_type')
        fcm_token = attrs.get('fcm_token', None)

        if not phone_number or not mpin:
            raise serializers.ValidationError("Phone number and MPIN are required.")

        try:
            user = CustomUser.objects.get(phone_number=phone_number)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError("Phone number does not exist.")

        if not user.check_password(mpin):
            raise serializers.ValidationError("Invalid MPIN.")

        if user.user_type != apk_type:
            raise serializers.ValidationError(f"Cannot log in as {user.user_type} on the {apk_type} APK.")

        if fcm_token:
            user.fcm_token = fcm_token
            user.save(update_fields=['fcm_token'])

        attrs['user'] = user
        return attrs


class RequestOTPForResetPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def validate_phone_number(self, value):
        phone_number = value.replace(" ", "").replace("-", "")
        if not phone_number.startswith("+91"):
            phone_number = f"+91{phone_number}"

        if len(phone_number) != 13 or not phone_number[3:].isdigit():
            raise serializers.ValidationError(
                "Invalid phone number. It must be a 10-digit number with the +91 country code.")
        return phone_number


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'name', 'phone_number', 'user_type']







