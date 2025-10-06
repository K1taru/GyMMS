from django.db import models

class PaymentSummary(models.Model):
    month = models.CharField(max_length=20)
    total_income = models.DecimalField(max_digits=10, decimal_places=2)
    total_transactions = models.PositiveIntegerField()
    generated_at = models.DateTimeField(auto_now_add=True)
