from django.db import models
from common.models import TimeStampedModel


class Budget(TimeStampedModel):
    """Budget model"""
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='budgets')
    name = models.CharField(max_length=200)
    department = models.CharField(max_length=100)
    allocated_amount = models.DecimalField(max_digits=15, decimal_places=2)
    spent_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    period = models.CharField(max_length=20, choices=[
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual')
    ], default='monthly')
    year = models.IntegerField()
    month = models.IntegerField(null=True, blank=True)  # null for annual/quarterly
    
    class Meta:
        db_table = 'budgets'
        verbose_name = 'Budget'
        verbose_name_plural = 'Budgets'
        ordering = ['-year', '-month']
    
    def __str__(self):
        return f"{self.name} - {self.allocated_amount}"
    
    @property
    def remaining_amount(self):
        return self.allocated_amount - self.spent_amount
    
    @property
    def utilization_percentage(self):
        if self.allocated_amount > 0:
            return (self.spent_amount / self.allocated_amount) * 100
        return 0
