from django.db import migrations, models
from django.db.models import F
from django.utils import timezone


def release_existing_staff_cancellations(apps, schema_editor):
    attempts = apps.get_model('payments', 'OnlinePaymentAttempt')
    attempts.objects.using(schema_editor.connection.alias).filter(
        status__in=('preparing', 'ready', 'processing', 'cancel_requested', 'needs_review'),
        cancel_reason='staff', payment__isnull=True, provider_payment_id='',
    ).update(staff_cancelled_at=F('updated_at'), next_retry_at=timezone.now())


class Migration(migrations.Migration):
    dependencies = [('payments', '0002_onlinepaymentattempt_stored_processor_id_and_more')]

    operations = [
        migrations.AddField(
            model_name='onlinepaymentattempt', name='staff_cancelled_at',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.RunPython(release_existing_staff_cancellations, migrations.RunPython.noop),
        migrations.RemoveConstraint(model_name='onlinepaymentattempt', name='one_unresolved_qrph_per_staff'),
        migrations.AddConstraint(
            model_name='onlinepaymentattempt',
            constraint=models.UniqueConstraint(
                fields=('created_by',),
                condition=models.Q(status__in=('preparing', 'ready', 'processing', 'cancel_requested', 'needs_review'), staff_cancelled_at__isnull=True),
                name='one_unresolved_qrph_per_staff',
            ),
        ),
    ]
