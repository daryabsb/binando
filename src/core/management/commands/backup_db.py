import os
import subprocess
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Backup or restore the PostgreSQL database'

    def add_arguments(self, parser):
        parser.add_argument('action', choices=['backup', 'restore'])
        parser.add_argument('--backup-dir', default='backups', help='Directory to store backups')

    def handle(self, *args, **options):
        action = options['action']
        backup_dir = os.path.join(settings.BASE_DIR, options['backup_dir'])
        db_name = settings.DATABASES['default']['NAME']
        db_user = settings.DATABASES['default']['USER']
        db_password = settings.DATABASES['default']['PASSWORD']
        db_host = settings.DATABASES['default']['HOST']
        db_port = settings.DATABASES['default']['PORT']
        backup_file = os.path.join(backup_dir, 'db_backup.sql')

        # Set environment variable for password to avoid command-line exposure
        env = os.environ.copy()
        env['PGPASSWORD'] = db_password

        if action == 'backup':
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)
            # Use --clean and --create for a full dump
            cmd = f'pg_dump -U {db_user} -h {db_host} -p {db_port} --clean --create {db_name} > {backup_file}'
            subprocess.run(cmd, shell=True, check=True, env=env)
            self.stdout.write(self.style.SUCCESS(f'Backup created: {backup_file}'))
        elif action == 'restore':
            if not os.path.exists(backup_file):
                self.stdout.write(self.style.ERROR(f'Backup file not found: {backup_file}'))
                return
            # Restore the full dump
            cmd = f'psql -U {db_user} -h {db_host} -p {db_port} -d postgres -c "DROP DATABASE IF EXISTS {db_name};"'
            subprocess.run(cmd, shell=True, check=True, env=env)
            cmd = f'psql -U {db_user} -h {db_host} -p {db_port} -d postgres -c "CREATE DATABASE {db_name};"'
            subprocess.run(cmd, shell=True, check=True, env=env)
            cmd = f'psql -U {db_user} -h {db_host} -p {db_port} -d {db_name} -f {backup_file}'
            subprocess.run(cmd, shell=True, check=True, env=env)
            self.stdout.write(self.style.SUCCESS(f'Database restored from: {backup_file}'))