from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

# Customize how our User model appears in the admin interface
class CustomUserAdmin(UserAdmin):
    # Fields to display in the user list
    list_display = (
        'username', 'email', 'student_id', 'user_type',
        'is_staff'
    )
    
    # Fields to filter users by
    list_filter = (
        'user_type', 'is_staff',
        'is_superuser', 'is_active'
    )
    
    # Fields to search through
    search_fields = (
        'username', 'email', 'student_id',
        'first_name', 'last_name'
    )
    
    # How to order users in the list
    ordering = ('username',)
    
    # Fields to show when adding/editing a user
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal Info', {
            'fields': (
                'first_name', 'last_name', 'email',
                'student_id', 'phone_number', 'emergency_contact',
                'student_type'
            )
        }),
        ('Permissions', {
            'fields': (
                'user_type', 'is_active', 'is_staff',
                'is_superuser', 'groups', 'user_permissions'
            )
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    # Fields to show when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'email', 'password1', 'password2',
                'user_type', 'is_staff', 'is_active'
            )
        }),
    )

# Register our custom User model with its admin configuration
admin.site.register(User, CustomUserAdmin)
