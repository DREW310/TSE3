from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

# Get our custom User model
User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal handler that runs when a User is created or saved
    This is where we can add any additional setup needed for new users
    
    Args:
        sender: The model class (User)
        instance: The actual user instance being saved
        created: Boolean; True if this is a new user
        **kwargs: Additional arguments
    """
    if created and instance.user_type == User.ADMIN:
        # If this is a new admin user, automatically set is_staff to True
        instance.is_staff = True
        instance.save() 