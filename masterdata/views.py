# masterdata/views.py   
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *
from rest_framework import permissions


# ------------------ Machine ------------------
class MachineTypeViewSet(viewsets.ModelViewSet):
    queryset = MachineType.objects.all()
    serializer_class = MachineTypeSerializer
    permission_classes = [IsAuthenticated]

class MachineRegistrationListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = MachineRegistrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MachineRegistration.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MachineRegistrationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        return get_object_or_404(MachineRegistration, pk=pk, user=user)

    def get(self, request, pk):
        obj = self.get_object(pk, request.user)
        serializer = MachineRegistrationSerializer(obj, context={'request': request})
        return Response(serializer.data)

    def put(self, request, pk):
        obj = self.get_object(pk, request.user)
        serializer = MachineRegistrationSerializer(obj, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        obj = self.get_object(pk, request.user)
        serializer = MachineRegistrationSerializer(obj, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk, request.user)
        obj.delete()
        return Response({"detail": "Machine deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


# ------------------ Input ------------------


class InputCategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = InputCategory.objects.all()
    serializer_class = InputCategorySerializer
    permission_classes = [IsAuthenticated]
    
    
class InputSubCategoryListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = InputSubCategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        category_id = self.request.query_params.get('category_id')
        if category_id:
            return InputSubCategory.objects.filter(category_id=category_id)
        return InputSubCategory.objects.all()
    

class InputView(generics.ListCreateAPIView):
    serializer_class = InputSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Input.objects.all()
        category_id = self.request.query_params.get('category_id')
        subcategory_id = self.request.query_params.get('subcategory_id')
        form_type = self.request.query_params.get('form_type')
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if subcategory_id:
            queryset = queryset.filter(subcategory_id=subcategory_id)
        if form_type:
            queryset = queryset.filter(form_type=form_type)
            
        return queryset
   

class InputMasterListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = InputMasterSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = InputMaster.objects.filter(user=self.request.user)
        
        # Filter options
        category_id = self.request.query_params.get('category_id')
        subcategory_id = self.request.query_params.get('subcategory_id')
        form_type = self.request.query_params.get('form_type')
        
        if category_id:
            queryset = queryset.filter(name__category_id=category_id)
        if subcategory_id:
            queryset = queryset.filter(name__subcategory_id=subcategory_id)
        if form_type:
            queryset = queryset.filter(name__form_type=form_type)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class InputMasterDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get_object(self, pk, user):
        return get_object_or_404(InputMaster, pk=pk, user=user)
    
    def get(self, request, pk):
        input_obj = self.get_object(pk, request.user)
        serializer = InputMasterSerializer(input_obj, context={'request': request})
        return Response(serializer.data)
    
    def put(self, request, pk):
        input_obj = self.get_object(pk, request.user)
        serializer = InputMasterSerializer(input_obj, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def patch(self, request, pk):
        input_obj = self.get_object(pk, request.user)
        serializer = InputMasterSerializer(input_obj, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        input_obj = self.get_object(pk, request.user)
        input_obj.delete()
        return Response({"detail": "Input deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    
