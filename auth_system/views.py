from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from chat.models import *
from .models import *

def register_user(request):
    if request.user.is_authenticated:
        return redirect("post:index")
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            name = request.POST.get('first_name')
            surname = request.POST.get('last_name')
            email = request.POST.get('email')
            bio = request.POST.get('bio')
            password = request.POST.get('password')
            
            new_user = CustomUser.objects.create_user(username=username, first_name=name, last_name=surname, email=email ,password=password, bio=bio)
            new_user.save()
            user = authenticate(username=username, first_name=name, last_name=surname, email=email, password=password)
            login(request, user)

            return redirect("post:index")
        else:
            return render(request, "auth_system/register.html")

def login_user(request):
    if request.user.is_authenticated:
        return redirect("post:index")
    else:
        if request.method == "POST":
            username = request.POST.get("username")
            password = request.POST.get("password")

            user = authenticate(username=username,password=password)
            
            if user is not None:
                login(request, user)
                return redirect("post:index")
            else:
                messages.error(request, ("There was an error logging in, try again!"))
                return redirect("login")
            
        else:
            return render(request, "auth_system/login.html")

@login_required
def logout_user(request):
    logout(request)
    messages.success(request, ("You were logged out"))
    return redirect("post:index")

@login_required
def user_info(request, pk):
    try:
        user = CustomUser.objects.get(id=pk)
        context = {
            'user': user, 
            'following': request.user.following.values_list('user_to_id', flat=True),
        }
        return render(request, 'auth_system/user_info.html', context=context)

    except CustomUser.DoesNotExist:
        return HttpResponse (
            "User doesn't exist!",
            status=404
        )

@login_required
def edit_user(request, user_id):
    if request.user.id == user_id:
        if request.method == 'POST':
            username = request.POST.get("username")
            name = request.POST.get('first_name')
            surname = request.POST.get('last_name')
            email = request.POST.get('email')
            bio = request.POST.get('bio')
            avatar = request.FILES.get('avatar')

            user = CustomUser.objects.get(id=user_id)
            user.username=username 
            user.email=email
            user.first_name=name
            user.last_name=surname
            user.bio = bio
            if avatar != None:
                user.avatar=avatar
            user.save()

            messages.success(request, "Profile info has been updated")
            return redirect(f"/user-info/{user_id}")
        else:
            return render(request, "auth_system/edit_user.html")
    else:
        return HttpResponse ("Access denied", status=400)

@login_required
def change_password(request, user_id):
    if request.user.id == user_id:
        if request.method == 'POST':
            user = CustomUser.objects.get(id=user_id)
            password = request.POST.get('current_password')
            new_password = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')
            validated = check_password(password, user.password)
            if validated:
                if new_password == new_password2:
                    user.set_password(new_password)
                    user.save()
                    login(request, user)
                    messages.success(request, ("Password has been changed"))
                else:
                    messages.error(request, ("Passwords do not match"))
                    return redirect(f'/change-password/{user_id}')
            else:
                messages.error(request, ("Incorrect password"))
                return redirect(f'/change-password/{user_id}')
            return redirect(f"/user-info/{user_id}")
        else:
            return render(request, "auth_system/change_password.html")
    else:
        return HttpResponse ("Access denied", status=400)
    
@login_required
def toggle_follow(request, pk):
    user_to = get_object_or_404(CustomUser, id=pk)
    # Унеможливлюємо підписку на самого себе
    if request.user == user_to:
        return JsonResponse({'error': 'You cannot follow yourself.'}, status=400)

    subscription = Subscription.objects.filter(user_from=request.user,user_to=user_to)

    if subscription.exists():
        subscription.delete()
        following = False
    else:
        Subscription.objects.create(user_from=request.user,user_to=user_to)
        following = True
    
    return JsonResponse({
        'following': following,
        'followers_count': user_to.followers.count(),
        'following_count': user_to.following.count(),
    })
