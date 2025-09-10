from django.urls import path
from .views import *

urlpatterns = [
    path('signup/farmer/', ManagerSignUpView.as_view()),
    path('signup/farmer/verify/', VerifyOTPForManagerSignUpView.as_view()),
    path('login/', LoginAPIView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('otp/request-password/', RequestOTPForPasswordResetView.as_view()),
    path('otp/verify-password/', VerifyOTPForPasswordResetView.as_view()),
    path('reset-password/', ResetPasswordAfterOTPVerificationView.as_view()),
    path('resend-otp/', ResendOTPView.as_view()),

]