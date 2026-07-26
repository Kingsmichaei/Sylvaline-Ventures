from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db.models import Sum


class Staff(models.Model):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('manager', 'Manager'),
        ('cashier', 'Cashier'),
        ('salesperson', 'Sales Person'),
        ('accountant', 'Accountant'),
        ('other', 'Other'),
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='staff_profile')
    name = models.CharField(max_length=200)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='other')
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Staff'

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"


class Customer(models.Model):
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def total_debt(self):
        result = self.debts.filter(is_paid=False).aggregate(total=Sum('amount'))
        return result['total'] or 0

    @property
    def total_purchases(self):
        result = self.sales.aggregate(total=Sum('total'))
        return result['total'] or 0

    @property
    def whatsapp_number(self):
        phone = self.phone.strip().replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        if phone.startswith('0'):
            phone = '234' + phone[1:]
        elif phone.startswith('+'):
            phone = phone[1:]
        return phone


class Sale(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Cash'),
        ('transfer', 'Bank Transfer'),
        ('pos', 'POS/Card'),
        ('credit', 'Credit (Debt)'),
    ]
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    product = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='cash')
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product} — ₦{self.total} ({self.date})"


class Debt(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='debts')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    paid_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        status = "PAID" if self.is_paid else "UNPAID"
        return f"{self.customer.name} — ₦{self.amount} [{status}]"

    @property
    def is_overdue(self):
        if self.due_date and not self.is_paid:
            return self.due_date < timezone.now().date()
        return False


class Expense(models.Model):
    CATEGORY_CHOICES = [
        ('rent', 'Rent'),
        ('utilities', 'Utilities/Bills'),
        ('salary', 'Staff Salary'),
        ('stock', 'Stock / Inventory'),
        ('transport', 'Transport / Logistics'),
        ('marketing', 'Marketing / Adverts'),
        ('maintenance', 'Maintenance / Repairs'),
        ('equipment', 'Equipment'),
        ('tax', 'Tax / Government'),
        ('other', 'Other'),
    ]
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    description = models.CharField(max_length=300)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    receipt_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.get_category_display()} — ₦{self.amount} ({self.date})"


class Income(models.Model):
    CATEGORY_CHOICES = [
        ('sales', 'Sales Revenue'),
        ('investment', 'Investment'),
        ('loan', 'Loan Received'),
        ('refund', 'Refund / Return'),
        ('other', 'Other Income'),
    ]
    description = models.CharField(max_length=300)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='sales')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def __str__(self):
        return f"{self.description} — ₦{self.amount} ({self.date})"
