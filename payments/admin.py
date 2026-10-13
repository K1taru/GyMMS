from django.contrib import admin, messages
from django.utils import timezone
from .models import OnlinePaymentAttempt, PayMongoWebhookEvent


class ReadOnlyPaymentAuditAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and (request.user.is_superuser or getattr(request.user, 'role', '') == 'Owner')


@admin.register(OnlinePaymentAttempt)
class AttemptAdmin(ReadOnlyPaymentAuditAdmin):
    list_display = ('id', 'customer_name', 'amount', 'mode', 'status', 'created_at')
    list_filter = ('mode', 'status')
    search_fields = ('stored_member_id', 'customer_name', 'payment_intent_id', 'provider_payment_id')
    actions = ('safe_cancel', 'retry_reconciliation', 'acknowledge_paid_review')

    @admin.action(description='Request safe provider cancellation', permissions=['view'])
    def safe_cancel(self, request, queryset):
        from .services.qrph import request_cancel
        count = 0
        for attempt in queryset:
            if attempt.is_unresolved and not attempt.payment_id and not attempt.provider_payment_id:
                request_cancel(attempt.pk)
                count += 1
        self.message_user(request, f'Queued {count} cancellation requests. Unknown provider outcomes remain unresolved.', messages.INFO)

    @admin.action(description='Retry verification of known provider intents', permissions=['view'])
    def retry_reconciliation(self, request, queryset):
        count = queryset.exclude(payment_intent_id='').filter(payment__isnull=True).update(next_retry_at=timezone.now(), retry_count=0)
        self.message_user(request, f'Queued {count} provider reconciliations. Unknown creation requests will not be repeated.', messages.INFO)

    @admin.action(description='Acknowledge paid receipt after manual owner review', permissions=['view'])
    def acknowledge_paid_review(self, request, queryset):
        from django.db import transaction
        count = 0
        with transaction.atomic():
            for attempt in queryset.select_for_update().filter(status='completed', payment__isnull=False, review_required=True):
                attempt.review_required = False
                attempt.message += f' Owner {request.user.username} acknowledged manual resolution at {timezone.now().isoformat()}; no additional membership fulfillment.'
                attempt.save(update_fields=['review_required', 'message', 'updated_at'])
                count += 1
        self.message_user(request, f'Acknowledged {count} paid reviews. Receipts and membership dates were preserved.', messages.INFO)


@admin.register(PayMongoWebhookEvent)
class WebhookEventAdmin(ReadOnlyPaymentAuditAdmin):
    list_display = ('event_id', 'mode', 'event_type', 'status', 'retry_count', 'received_at')
    list_filter = ('mode', 'status', 'event_type')
    search_fields = ('event_id',)
    actions = ('retry_events',)

    @admin.action(description='Retry pending webhook verification', permissions=['view'])
    def retry_events(self, request, queryset):
        count = queryset.filter(status='pending').update(next_retry_at=timezone.now(), retry_count=0)
        self.message_user(request, f'Queued {count} pending webhook verifications.', messages.INFO)
