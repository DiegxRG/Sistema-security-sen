"""
Management command to seed initial data into Firestore.
Creates default shifts and an initial admin user.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Seeds initial data into Firestore: shifts and admin user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-email',
            type=str,
            default='admin@senati.pe',
            help='Email for the initial admin user (default: admin@senati.pe)',
        )
        parser.add_argument(
            '--admin-password',
            type=str,
            default='Admin123!',
            help='Password for the initial admin user (default: Admin123!)',
        )

    def handle(self, *args, **options):
        from security_system.firebase import seed_shifts
        from security_system.auth import create_firebase_user, ROLE_ADMIN, set_user_role

        self.stdout.write(self.style.MIGRATE_HEADING('\n📦 Seeding Firestore data...\n'))

        # 1. Seed shifts
        self.stdout.write('🕐 Creating default shifts...')
        seed_shifts()

        # 2. Create admin user
        admin_email = options['admin_email']
        admin_password = options['admin_password']

        self.stdout.write(f'\n👤 Creating admin user: {admin_email}')
        try:
            user = create_firebase_user(
                email=admin_email,
                password=admin_password,
                display_name='Administrador SENATI',
                role=ROLE_ADMIN,
            )
            self.stdout.write(self.style.SUCCESS(
                f'  ✅ Admin user created: {admin_email} (uid: {user.uid})'
            ))
        except Exception as e:
            if 'ALREADY_EXISTS' in str(e) or 'EMAIL_EXISTS' in str(e):
                self.stdout.write(self.style.WARNING(
                    f'  ⏭️  Admin user {admin_email} already exists.'
                ))
                # Make sure they have admin role
                try:
                    from security_system.firebase import get_auth
                    auth = get_auth()
                    user = auth.get_user_by_email(admin_email)
                    set_user_role(user.uid, ROLE_ADMIN)
                    self.stdout.write(f'  ✅ Admin role verified for {admin_email}')
                except Exception:
                    pass
            else:
                self.stdout.write(self.style.ERROR(f'  ❌ Error: {e}'))

        self.stdout.write(self.style.SUCCESS('\n✨ Seed complete!\n'))
        self.stdout.write(f'   Login: {admin_email} / {admin_password}')
        self.stdout.write('   URL:   http://localhost:8000/security/login/\n')
