from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from core.models import Customer
from django.contrib import messages


# Create your views here.
def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')  # This was missing
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/')
        messages.info(request, "Login Failed, Please Try Again")

    return render(request, 'accounts/login.html')


def user_register(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        phone = request.POST.get('phone')

        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                messages.info(request, "Username already exists")
                return redirect('user_register')
            elif User.objects.filter(email=email).exists():
                messages.info(request, "Email already exists")
                return redirect('user_register')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save()
                customer = Customer(user=user, phone_field=phone)
                customer.save()
                our_user = authenticate(username=username, password=password)
                if our_user is not None:
                    login(request, our_user)
                    return redirect('/')
        else:
            messages.info(request, "Password and Confirm Password Mismatch!")
            return redirect('user_register')
    return render(request, 'accounts/register.html')


def user_logout(request):
    logout(request)
    return redirect('/')
