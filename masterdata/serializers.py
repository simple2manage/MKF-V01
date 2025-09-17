# masterdata/serializers.py
from rest_framework import serializers
from .models import MachineRegistration, MachineType, Input, InputMaster


# ------------------ Machine ------------------
class MachineTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MachineType
        fields = ['id', 'name']


class MachineRegistrationSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    user = serializers.ReadOnlyField(source='user.username')
    name = serializers.StringRelatedField(read_only=True)
    name_id = serializers.PrimaryKeyRelatedField(
        queryset=MachineType.objects.all(), source='name', write_only=True)

    class Meta:
        model = MachineRegistration
        fields = [
            'id', 'user', 'name', 'name_id',
            'registration_number', 'image', 'image_url', 'created_at',
        ]

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url)
        return None


# ------------------ Input ------------------
class InputSerializer(serializers.ModelSerializer):
    class Meta:
        model = Input
        fields = ['id', 'name']


class InputMasterSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    username = serializers.ReadOnlyField(source='user.username')
    name = serializers.StringRelatedField(read_only=True)
    name_id = serializers.PrimaryKeyRelatedField(
        queryset=Input.objects.all(), source='name', write_only=True
    )
    class Meta:
        model = InputMaster
        fields = [
            'id', 'user', 'username',
            'name', 'name_id', 'created_at',
        ]
        read_only_fields = ['id', 'user', 'username', 'created_at']
