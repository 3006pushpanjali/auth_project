import uuid

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.urls import reverse

from .models import UserProfile
from django.core.paginator import Paginator
from django.db.models import Q



def home(request):
    return HttpResponse("Welcome to the User Authentication System!")


def register(request):

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("register")

        try:
            validate_password(password)

        except ValidationError as e:

            for error in e.messages:
                messages.error(request, error)

            return redirect("register")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        profile = UserProfile.objects.create(user=user)

        verification_link = request.build_absolute_uri(
            reverse(
                "verify_email",
                args=[profile.email_verification_token]
            )
        )

        try:
            send_mail(
                subject="Verify Your Email",
                message=(
                    f"Click this link to verify your email:\n\n"
                    f"{verification_link}"
                ),
                from_email=None,
                recipient_list=[email],
                fail_silently=False,
            )

        except Exception as e:
            print("EMAIL ERROR:", str(e))
            raise

        messages.success(
            request,
            "Registration successful. Please check your email to verify your account."
        )

        return redirect("login")
    return render(request, "accounts/register.html")

def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            profile = UserProfile.objects.get(user=user)

            if not user.is_superuser and not profile.is_email_verified:
                messages.warning(
                    request,
                    "Please verify your email first."
                )
                return redirect("login")

            login(request, user)

            messages.success(
                request,
                f"Welcome back, {user.username}!"
            )

            return redirect("dashboard")

        messages.error(
            request,
            "Invalid username or password."
        )

        return redirect("login")

    return render(request, "accounts/login.html")


def dashboard(request):

    if not request.user.is_authenticated:
        return redirect("login")

    if request.user.is_superuser:
        message = "Admin Dashboard"
    else:
        message = "User Dashboard"

    return render(
        request,
        "accounts/dashboard.html",
        {
            "user": request.user,
            "message": message
        }
    )


def logout_view(request):

    logout(request)

    messages.success(
        request,
        "You have been logged out."
    )

    return redirect("login")


def admin_panel(request):

    if not request.user.is_authenticated:
        return redirect("login")

    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    search_query = request.GET.get("q", "")

    users = User.objects.exclude(id=request.user.id)

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    users = users.order_by("-date_joined")

    paginator = Paginator(users, 5)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "accounts/admin_panel.html",
        {
            "page_obj": page_obj,
            "search_query": search_query,
        }
    )


def delete_user(request, user_id):

    if not request.user.is_authenticated:
        return redirect("login")

    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect("dashboard")

    user = get_object_or_404(User, id=user_id)

    if user != request.user:
        user.delete()

        messages.success(
            request,
            "User deleted successfully."
        )

    return redirect("admin_panel")


def edit_profile(request):

    if not request.user.is_authenticated:
        return redirect("login")

    if request.method == "POST":

        username = request.POST.get("username")
        email = request.POST.get("email")

        request.user.username = username
        request.user.email = email

        request.user.save()

        messages.success(
            request,
            "Profile updated successfully."
        )

        return redirect("dashboard")

    return render(
        request,
        "accounts/edit_profile.html"
    )


def verify_email(request, token):

    profile = get_object_or_404(
        UserProfile,
        email_verification_token=token
    )

    profile.is_email_verified = True
    profile.email_verification_token = uuid.uuid4()

    profile.save()

    messages.success(
        request,
        "Email verified successfully. Please log in."
    )

    return redirect("login")


def forgot_password(request):

    if request.method == "POST":

        email = request.POST.get("email")

        try:
            user = User.objects.get(email=email)

            profile = user.userprofile

            profile.password_reset_token = uuid.uuid4()
            profile.save()

            reset_link = request.build_absolute_uri(
                reverse(
                    "reset_password",
                    args=[profile.password_reset_token]
                )
            )

            send_mail(
                subject="Password Reset",
                message=(
                    f"Click this link to reset your password:\n\n"
                    f"{reset_link}"
                ),
                from_email=None,
                recipient_list=[email],
                fail_silently=False,
            )

            messages.success(
                request,
                "Password reset email sent."
            )

            return redirect("login")

        except User.DoesNotExist:

            messages.error(
                request,
                "No user found with this email."
            )

            return redirect("forgot_password")

    return render(
        request,
        "accounts/forgot_password.html"
    )


def reset_password(request, token):

    profile = get_object_or_404(
        UserProfile,
        password_reset_token=token
    )

    user = profile.user

    if request.method == "POST":

        new_password = request.POST.get("password")

        try:
            validate_password(new_password, user)

        except ValidationError as e:

            for error in e.messages:
                messages.error(request, error)

            return redirect(
                "reset_password",
                token=token
            )

        user.set_password(new_password)
        user.save()

        profile.password_reset_token = None
        profile.save()

        messages.success(
            request,
            "Password reset successful. Please log in."
        )

        return redirect("login")

    return render(
        request,
        "accounts/reset_password.html"
    )