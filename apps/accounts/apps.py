from django.apps import AppConfig


class AccountsConfig(AppConfig):
    # Full Python path to the application
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'
    
    # Human-readable name for the application
    verbose_name = 'User Accounts'
    
    def ready(self):
        """
        Import signal handlers when the app is ready
        This makes sure our custom user model works correctly
        """
        import apps.accounts.signals  # noqa
