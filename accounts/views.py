from rest_framework.generics import ListAPIView
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from knox.auth import AuthToken
from knox.views import LoginView as KnoxLoginView
from knox.views import LogoutView as KnoxLogoutView
from django.contrib.auth import login
from django.utils import timezone
from .models import *
from .sendotp import send_otp_to_phone
from .serializers import *
import logging
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser


logger = logging.getLogger(__name__)


class ManagerSignUpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ManagerSignUpSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data.get('phone_number')
            mpin = serializer.validated_data.get('mpin')
            user_type = "farmer"

            unverified_user = CustomUser.objects.filter(unverified_phone_number=phone_number, is_verified=False).first()

            if unverified_user:
                if unverified_user.user_type != user_type:
                    return Response({
                        "error": f"This phone number is already registered with a different user type ({unverified_user.user_type})."
                    }, status=status.HTTP_400_BAD_REQUEST)

                unverified_user.set_password(mpin)
                otp = send_otp_to_phone(phone_number)
                if not otp:
                    return Response({"error": "Failed to send OTP."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                unverified_user.otp = otp
                unverified_user.otp_created_at = timezone.now()
                unverified_user.save(update_fields=['otp', 'otp_created_at', 'password'])

                return Response({"message": "OTP resent successfully. Please verify the OTP to complete sign-up."},
                                status=status.HTTP_200_OK)

            # New user signup
            otp = send_otp_to_phone(phone_number)
            if not otp:
                return Response({"error": "Failed to send OTP."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            user = serializer.save()
            user.user_type = user_type
            user.is_verified = False
            user.unverified_phone_number = phone_number
            user.phone_number = None
            user.set_password(mpin)
            user.otp = otp
            user.otp_created_at = timezone.now()
            user.save()

            return Response({
                "message": "OTP sent successfully. Please verify the OTP to complete sign-up.",
                "user_id": user.id
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPForManagerSignUpView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        otp = request.data.get('otp')
        phone_number = request.data.get('phone_number')

        if not phone_number:
            return Response({"error": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)

        phone_number = phone_number.replace(" ", "").replace("-", "")
        if not phone_number.startswith("+91"):
            phone_number = f"+91{phone_number}"

        try:
            user = CustomUser.objects.get(unverified_phone_number=phone_number, otp=otp, is_verified=False)

            if not user.is_otp_valid():
                return Response({"error": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)

            user.phone_number = user.unverified_phone_number
            user.unverified_phone_number = None
            user.is_verified = True
            user.otp = None
            user.otp_created_at = None
            user.save()

            _, token = AuthToken.objects.create(user)

            return Response({
                "message": "OTP verified successfully. Farmer account created.",
                "token": token,
                "user_id": user.id
            }, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({"error": "Invalid OTP or phone number."}, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(KnoxLoginView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            user = serializer.validated_data['user']
            if not user.is_verified:
                return Response({'error': 'User is not verified. Please verify OTP.'},
                                status=status.HTTP_400_BAD_REQUEST)

            login(request, user)
            response = super().post(request, format=None)
            return Response({'message': "Login successful", "user_id": user.id, **response.data},
                            status=status.HTTP_200_OK)

        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class RequestOTPForPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RequestOTPForResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data.get('phone_number')
            apk_type = request.data.get('apk_type')

            try:
                user = CustomUser.objects.get(phone_number=phone_number)

                if not user.is_verified:
                    return Response(
                        {'error': "User is not verified. Please verify your account before resetting MPIN."},
                        status=status.HTTP_403_FORBIDDEN)

                if user.user_type != "farmer":
                    return Response({'error': f"Cannot reset MPIN for user_type {user.user_type} in farmer app."},
                                    status=status.HTTP_400_BAD_REQUEST)

                otp = send_otp_to_phone(phone_number)
                logger.info(f"Generated OTP: {otp}")
                user.otp = otp
                user.otp_created_at = timezone.now()
                user.save(update_fields=['otp', 'otp_created_at'])

                return Response({'message': "OTP sent successfully."}, status=status.HTTP_200_OK)
            except CustomUser.DoesNotExist:
                return Response({'error': 'Phone number not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPForPasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        otp = request.data.get('otp')
        phone_number = request.data.get('phone_number')

        if not phone_number:
            return Response({'error': 'Phone number is required.'}, status=status.HTTP_400_BAD_REQUEST)

        phone_number = phone_number.replace(" ", "").replace("-", "")
        if not phone_number.startswith("+91"):
            phone_number = f"+91{phone_number}"

        try:
            user = CustomUser.objects.get(phone_number=phone_number)

            if not user.is_otp_valid():
                return Response({'error': "OTP has expired. Please request a new one."},
                                status=status.HTTP_400_BAD_REQUEST)

            if user.otp != otp:
                return Response({'error': 'Invalid OTP or phone number.'}, status=status.HTTP_400_BAD_REQUEST)

            user.otp_created_at = None
            user.otp = None
            user.save(update_fields=['otp', 'otp_created_at'])
            return Response({'message': 'OTP verified successfully.'}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'error': 'Invalid OTP or phone number.'}, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordAfterOTPVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        new_mpin = request.data.get('new_mpin')
        confirm_new_mpin = request.data.get('confirm_new_mpin')
        phone_number = request.data.get('phone_number')

        if not phone_number:
            return Response({'error': 'Phone number is required.'}, status=status.HTTP_400_BAD_REQUEST)

        phone_number = phone_number.replace(" ", "").replace("-", "")
        if not phone_number.startswith("+91"):
            phone_number = f"+91{phone_number}"

        if not new_mpin or not confirm_new_mpin:
            return Response({'error': 'New MPIN and Confirm MPIN are required.'},
                            status=status.HTTP_400_BAD_REQUEST)

        if new_mpin != confirm_new_mpin:
            return Response({'error': 'MPINs do not match.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(phone_number=phone_number)
            user.set_password(new_mpin)
            user.save()
            return Response({'message': 'MPIN reset successfully.'}, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)


class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone_number = request.data.get('phone_number')

        if not phone_number:
            return Response({'error': 'Phone number is required.'}, status=status.HTTP_400_BAD_REQUEST)

        phone_number = phone_number.replace(" ", "").replace("-", "")
        if not phone_number.startswith("+91"):
            phone_number = f"+91{phone_number}"

        user = CustomUser.objects.filter(phone_number=phone_number).first()
        if not user:
            user = CustomUser.objects.filter(unverified_phone_number=phone_number).first()

        if not user:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        otp = send_otp_to_phone(phone_number)
        if not otp:
            return Response({'error': 'Failed to send OTP.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        user.otp = otp
        user.otp_created_at = timezone.now()
        user.save(update_fields=['otp', 'otp_created_at'])

        return Response({'message': 'OTP resent successfully.'}, status=status.HTTP_200_OK)


class LogoutView(KnoxLogoutView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        super().post(request, *args, **kwargs)
        return Response({'message': 'Logged out successfully!'}, status=status.HTTP_200_OK)

