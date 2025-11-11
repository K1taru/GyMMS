from django.core.management.base import BaseCommand
from payments.models import MembershipPricing


class Command(BaseCommand):
    help = 'Seeds initial membership pricing options'

    def handle(self, *args, **kwargs):
        pricing_data = [
            {
                'duration_days': 30,
                'duration_label': '1 Month',
                'price': 500.00
            },
            {
                'duration_days': 90,
                'duration_label': '3 Months',
                'price': 1400.00
            },
            {
                'duration_days': 180,
                'duration_label': '6 Months',
                'price': 2700.00
            },
            {
                'duration_days': 365,
                'duration_label': '1 Year',
                'price': 5000.00
            },
        ]

        created_count = 0
        updated_count = 0

        for data in pricing_data:
            pricing, created = MembershipPricing.objects.update_or_create(
                duration_days=data['duration_days'],
                defaults={
                    'duration_label': data['duration_label'],
                    'price': data['price'],
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created pricing: {pricing.duration_label} - ₱{pricing.price}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated pricing: {pricing.duration_label} - ₱{pricing.price}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Seeding complete! Created: {created_count}, Updated: {updated_count}')
        )
