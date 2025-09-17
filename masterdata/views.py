# masterdata/views.py   
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import MachineRegistration, Input, InputMaster, MachineType
from .serializers import MachineRegistrationSerializer, InputSerializer, InputMasterSerializer, MachineTypeSerializer


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
class InputViewSet(viewsets.ModelViewSet):
    queryset = Input.objects.all()
    serializer_class = InputSerializer
    permission_classes = [IsAuthenticated]


class InputMasterListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = InputMasterSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return InputMaster.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class InputMasterDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        return get_object_or_404(InputMaster, pk=pk, user=user)

    def get(self, request, pk):
        obj = self.get_object(pk, request.user)
        serializer = InputMasterSerializer(obj, context={'request': request})
        return Response(serializer.data)

    def put(self, request, pk):
        obj = self.get_object(pk, request.user)
        serializer = InputMasterSerializer(obj, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        obj = self.get_object(pk, request.user)
        serializer = InputMasterSerializer(obj, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk, request.user)
        obj.delete()
        return Response({"detail": "Input deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
