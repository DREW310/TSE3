from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from . import views

# This helps Django identify our app in URL patterns
app_name = 'accounts'

# URL patterns for the accounts app
# Each pattern maps a URL to a view function
urlpatterns = [
    # Authentication URLs
    path('register/', views.student_register, name='register'),
    path('register/staff/', login_required(views.staff_register), name='staff_register'),
    path('login/', auth_views.LoginView.as_view(
        template_name='accounts/login.html',
        redirect_authenticated_user=True
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        next_page='accounts:login'
    ), name='logout'),
    
    # Profile management
    path('profile/', views.profile, name='profile'),
    
    # Dashboard
    path('dashboard/', views.student_dashboard, name='dashboard'),
    path('dashboard/staff/', views.staff_dashboard, name='staff_dashboard'),
    
    # Password reset URLs (using Django's built-in views)
    path('password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
            success_url=reverse_lazy('accounts:password_reset_done')
        ),
        name='password_reset'
    ),
    path('password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path('password-reset-confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url=reverse_lazy('accounts:password_reset_complete')
        ),
        name='password_reset_confirm'
    ),
    path('password-reset-complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),
] 