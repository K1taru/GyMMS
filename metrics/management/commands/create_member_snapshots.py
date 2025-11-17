from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from metrics.models import ActiveMemberSnapshot


class Command(BaseCommand):
    help = 'Create daily snapshots of active member counts for metrics tracking'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Number of days to create snapshots for (default: 1 for today only)'
        )
        parser.add_argument(
            '--backfill',
            type=int,
            help='Backfill snapshots for the last N days'
        )

    def handle(self, *args, **options):
        days = options['days']
        backfill = options.get('backfill')
        
        if backfill:
            # Backfill mode: create snapshots for the last N days
            self.stdout.write(self.style.WARNING(f'Backfilling snapshots for the last {backfill} days...'))
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=backfill - 1)
            
            created_count = 0
            updated_count = 0
            
            current_date = start_date
            while current_date <= end_date:
                existing = ActiveMemberSnapshot.objects.filter(date=current_date).exists()
                snapshot = ActiveMemberSnapshot.create_snapshot(current_date)
                
                if existing:
                    updated_count += 1
                    self.stdout.write(f'  Updated snapshot for {current_date}')
                else:
                    created_count += 1
                    self.stdout.write(f'  Created snapshot for {current_date}')
                
                current_date += timedelta(days=1)
            
            self.stdout.write(self.style.SUCCESS(
                f'\nBackfill complete: {created_count} created, {updated_count} updated'
            ))
        else:
            # Normal mode: create snapshot for today or last N days
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=days - 1)
            
            created_count = 0
            updated_count = 0
            
            current_date = start_date
            while current_date <= end_date:
                existing = ActiveMemberSnapshot.objects.filter(date=current_date).exists()
                snapshot = ActiveMemberSnapshot.create_snapshot(current_date)
                
                if existing:
                    updated_count += 1
                else:
                    created_count += 1
                
                current_date += timedelta(days=1)
            
            if days == 1:
                self.stdout.write(self.style.SUCCESS(
                    f'Snapshot for {end_date}: {snapshot.active_count} active members'
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'Created/updated {created_count + updated_count} snapshots '
                    f'({created_count} new, {updated_count} updated)'
                ))
