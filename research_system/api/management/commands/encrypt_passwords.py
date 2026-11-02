"""Encrypt plaintext passwords in api.User table using Django make_password.

Run once: python manage.py encrypt_passwords
After this, plaintext passwords are replaced with PBKDF2-SHA256 hashes.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password, is_password_usable

from api.models import User


class Command(BaseCommand):
    help = 'Encrypt all plaintext passwords in api.User'

    def handle(self, *args, **options):
        total = User.objects.count()
        encrypted = 0
        skipped = 0

        for user in User.objects.all():
            if is_password_usable(user.password) and not user.password.startswith('pbkdf2_sha256$'):
                user.password = make_password(user.password)
                user.save(update_fields=['password'])
                encrypted += 1
                self.stdout.write(f'  Encrypted: {user.username}')
            else:
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Done. Total={total}, Encrypted={encrypted}, AlreadyHashed/Skipped={skipped}'
            )
        )
