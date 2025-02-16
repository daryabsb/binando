from django.contrib.auth.models import BaseUserManager

# from src.core.modules import generate_activation_code


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, name=None, terms=False,
                    **extra_fields):
        # Creates and save a new user
        if not email:
            raise ValueError('Users must have an email address!')

        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.name = name
        user.terms = terms
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        # Creates and save a new superuser
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
