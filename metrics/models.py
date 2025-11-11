from django.db import models

class PaymentSummary(models.Model):
    month = models.DateField(unique=True, help_text='First day of the month')
    total_income = models.DecimalField(max_digits=10, decimal_places=2)
    total_transactions = models.PositiveIntegerField()
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-month']
        verbose_name = 'Payment Summary'
        verbose_name_plural = 'Payment Summaries'
        indexes = [
            models.Index(fields=['month']),
        ]
    
    def __str__(self):
        return f"Summary for {self.month.strftime('%B %Y')}"
