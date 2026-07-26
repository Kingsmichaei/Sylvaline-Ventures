from django.db.models import Sum
from django.utils import timezone
from .models import Sale, Expense, Income, Debt, Customer, Staff


def business_stats(request):
    """Global context for all templates."""
    today = timezone.now().date()
    month_start = today.replace(day=1)

    # Monthly totals
    monthly_sales = Sale.objects.filter(date__gte=month_start).aggregate(t=Sum('total'))['t'] or 0
    monthly_expenses = Expense.objects.filter(date__gte=month_start).aggregate(t=Sum('amount'))['t'] or 0
    total_unpaid_debts = Debt.objects.filter(is_paid=False).aggregate(t=Sum('amount'))['t'] or 0

    return {
        'business_name': 'Complete SYLVALINE Ventures',
        'business_currency': '₦',
        'monthly_sales': monthly_sales,
        'monthly_expenses': monthly_expenses,
        'total_unpaid_debts': total_unpaid_debts,
        'net_monthly': monthly_sales - monthly_expenses,
        'overdue_debts_count': Debt.objects.filter(is_paid=False, due_date__lt=today).count(),
        'active_staff_count': Staff.objects.filter(is_active=True).count(),
        'customers_count': Customer.objects.count(),
    }
