"""
Management command to seed mock data for testing purposes.
Creates users per role, areas, personnel, and log entries.
"""
import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from security_system.firebase import (
    get_areas_ref, get_personnel_ref, get_logs_ref, get_shifts_ref
)
from security_system.auth import create_firebase_user, set_user_role, ALL_ROLES

class Command(BaseCommand):
    help = 'Seeds mock data for testing (users, areas, personnel, logs)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('\n🧪 Seeding Mock Data...\n'))

        # 1. Create Users
        self.stdout.write('👤 Creating users for each role (Password: Senati123!)...')
        for role in ALL_ROLES:
            for i in range(1, 3):
                email = f'{role}{i}@senati.pe'
                try:
                    user = create_firebase_user(
                        email=email,
                        password='Senati123!',
                        display_name=f'{role.capitalize()} {i}',
                        role=role,
                    )
                    self.stdout.write(self.style.SUCCESS(f'  ✅ Created: {email} (Role: {role})'))
                except Exception as e:
                    if 'ALREADY_EXISTS' in str(e) or 'EMAIL_EXISTS' in str(e):
                        self.stdout.write(self.style.WARNING(f'  ⏭️  Already exists: {email}'))
                    else:
                        self.stdout.write(self.style.ERROR(f'  ❌ Error creating {email}: {e}'))

        # 2. Create Areas
        self.stdout.write('\n📍 Creating areas...')
        areas_ref = get_areas_ref()
        area_names = ['Puerta Principal', 'Almacén General', 'Taller de Mecánica', 'Edificio Administrativo', 'Estacionamiento']
        area_ids = []
        for name in area_names:
            # Check if exists
            existing = list(areas_ref.where('name', '==', name).limit(1).get())
            if not existing:
                _, doc_ref = areas_ref.add({'name': name, 'description': f'Área de {name}', 'isActive': True})
                area_ids.append(doc_ref.id)
                self.stdout.write(self.style.SUCCESS(f'  ✅ Created area: {name}'))
            else:
                area_ids.append(existing[0].id)
                self.stdout.write(self.style.WARNING(f'  ⏭️  Already exists area: {name}'))

        # 3. Create Personnel
        self.stdout.write('\n🛡️ Creating personnel (Guards)...')
        personnel_ref = get_personnel_ref()
        guard_names = [
            ('Juan', 'Pérez', '71234567'), ('María', 'Gómez', '72345678'),
            ('Carlos', 'López', '73456789'), ('Ana', 'Martínez', '74567890'),
            ('Luis', 'Torres', '75678901'), ('Elena', 'Díaz', '76789012'),
        ]
        
        personnel_ids = []
        shifts = ['T-01', 'T-02', 'T-03']
        
        for i, (first, last, dni) in enumerate(guard_names):
            existing = list(personnel_ref.where('documentId', '==', dni).limit(1).get())
            if not existing:
                data = {
                    'firstName': first,
                    'lastName': last,
                    'documentId': dni,
                    'cargo': 'Guardia de Seguridad',
                    'assignedShift': shifts[i % len(shifts)],
                    'status': 'active',
                    'createdAt': datetime.now(),
                }
                _, doc_ref = personnel_ref.add(data)
                personnel_ids.append(doc_ref.id)
                self.stdout.write(self.style.SUCCESS(f'  ✅ Created guard: {first} {last}'))
            else:
                personnel_ids.append(existing[0].id)
                self.stdout.write(self.style.WARNING(f'  ⏭️  Already exists guard: {first} {last}'))

        # 4. Create Logs
        self.stdout.write('\n📝 Creating mock logs...')
        logs_ref = get_logs_ref()
        
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        
        reasons = ['Fin de turno', 'Ronda', 'Refrigerio', 'Otro']

        try:
            # Check if we already have logs to avoid duplicating
            existing_logs = list(logs_ref.limit(1).get())
            if not existing_logs:
                # Add historical logs (completed)
                for pid in personnel_ids[:4]:
                    entry_time = yesterday.replace(hour=random.randint(6, 10), minute=random.randint(0, 59))
                    exit_time = entry_time + timedelta(hours=random.randint(4, 9), minutes=random.randint(0, 59))
                    reason = random.choice(reasons)
                    
                    logs_ref.add({
                        'personnelId': pid,
                        'shiftId': random.choice(shifts),
                        'entryTime': entry_time,
                        'exitTime': exit_time,
                        'exitReason': reason,
                        'exitReasonDetail': 'Detalle de prueba' if reason == 'Otro' else None,
                        'destinationAreaId': random.choice(area_ids),
                        'operatorId': 'mock-operator-id',
                        'status': 'exited',
                    })
                
                # Add active logs (currently inside)
                for pid in personnel_ids[4:]:
                    entry_time = now.replace(hour=random.randint(6, max(7, now.hour-1)), minute=random.randint(0, 59))
                    
                    logs_ref.add({
                        'personnelId': pid,
                        'shiftId': random.choice(shifts),
                        'entryTime': entry_time,
                        'exitTime': None,
                        'exitReason': None,
                        'exitReasonDetail': None,
                        'destinationAreaId': None,
                        'operatorId': 'mock-operator-id',
                        'status': 'entered',
                    })
                self.stdout.write(self.style.SUCCESS(f'  ✅ Created 6 mock logs (4 exited, 2 active).'))
            else:
                self.stdout.write(self.style.WARNING(f'  ⏭️  Logs already exist, skipping.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error creating logs: {e}'))

        self.stdout.write(self.style.SUCCESS('\n✨ Mock data seeding complete!\n'))
        self.stdout.write('Users created with password: Senati123!')
