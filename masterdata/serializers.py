# masterdata/serializers.py
from rest_framework import serializers
from .models import *


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
class InputCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = InputCategory
        fields = ['id', 'name', 'description', 'created_at']
        
        
class InputSubCategorySerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    
    class Meta:
        model = InputSubCategory
        fields = ['id', 'category', 'category_name', 'name', 'description', 'created_at']


class InputSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    subcategory_name = serializers.ReadOnlyField(source='subcategory.name')
    unit_display = serializers.ReadOnlyField(source='get_unit_display')
    form_type_display = serializers.ReadOnlyField(source='get_form_type_display')
    
    class Meta:
        model = Input
        fields = [
            'id', 'name', 'category', 'category_name', 
            'subcategory', 'subcategory_name', 'form_type', 
            'form_type_display', 'unit', 'unit_display', 
            'description', 'created_at'
        ]



class InputMasterSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    username = serializers.ReadOnlyField(source='user.username')
    name = serializers.PrimaryKeyRelatedField(queryset=Input.objects.all())
    name_display = serializers.StringRelatedField(source='name', read_only=True)
    
    # Additional display fields
    unit_display = serializers.ReadOnlyField()
    form_type_display = serializers.ReadOnlyField()
    category_name = serializers.ReadOnlyField()
    subcategory_name = serializers.ReadOnlyField()
    
    class Meta:
        model = InputMaster
        fields = [
            'id', 'user', 'username', 'name', 'name_display',
            'description', 'image', 'image_url',
            'unit_display', 'form_type_display',
            'category_name', 'subcategory_name',
            'is_active','created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'username', 'image_url', 
            'unit_display', 'form_type_display',
            'category_name', 'subcategory_name',
            'created_at', 'updated_at'
        ]
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url)
        return None