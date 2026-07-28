from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from datetime import timedelta, date
import csv
import json

from .models import Customer, Sale, Debt, Expense, Income, Staff
from .forms import CustomerForm, SaleForm, DebtForm, ExpenseForm, IncomeForm, StaffForm


# ─── Dashboard ────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    today = timezone.now().date()
    month_start = today.replace(day=1)
    year_start = today.replace(month=1, day=1)

    # This month
    monthly_sales = Sale.objects.filter(date__gte=month_start).aggregate(t=Sum('total'))['t'] or 0
    monthly_expenses = Expense.objects.filter(date__gte=month_start).aggregate(t=Sum('amount'))['t'] or 0
    monthly_income = Income.objects.filter(date__gte=month_start).aggregate(t=Sum('amount'))['t'] or 0

    # All time
    total_debts = Debt.objects.filter(is_paid=False).aggregate(t=Sum('amount'))['t'] or 0
    total_sales_ever = Sale.objects.aggregate(t=Sum('total'))['t'] or 0

    # Recent records
    recent_sales = Sale.objects.select_related('customer').order_by('-date', '-created_at')[:5]
    recent_debts = Debt.objects.filter(is_paid=False).select_related('customer').order_by('-created_at')[:5]
    recent_expenses = Expense.objects.order_by('-date')[:5]
    overdue_debts = Debt.objects.filter(is_paid=False, due_date__lt=today).select_related('customer')

    # Last 7 days sales chart
    chart_labels = []
    chart_sales = []
    chart_expenses = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_sales = Sale.objects.filter(date=day).aggregate(t=Sum('total'))['t'] or 0
        day_expenses = Expense.objects.filter(date=day).aggregate(t=Sum('amount'))['t'] or 0
        chart_labels.append(day.strftime('%a %d'))
        chart_sales.append(float(day_sales))
        chart_expenses.append(float(day_expenses))

    # Last 6 months chart
    monthly_labels = []
    monthly_sales_data = []
    monthly_expense_data = []
    for i in range(5, -1, -1):
        m_date = today.replace(day=1) - timedelta(days=i * 30)
        m_start = m_date.replace(day=1)
        next_month = (m_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        ms = Sale.objects.filter(date__gte=m_start, date__lt=next_month).aggregate(t=Sum('total'))['t'] or 0
        me = Expense.objects.filter(date__gte=m_start, date__lt=next_month).aggregate(t=Sum('amount'))['t'] or 0
        monthly_labels.append(m_start.strftime('%b'))
        monthly_sales_data.append(float(ms))
        monthly_expense_data.append(float(me))

    context = {
        'monthly_sales': monthly_sales,
        'monthly_expenses': monthly_expenses,
        'monthly_income': monthly_income,
        'net_profit': monthly_sales + monthly_income - monthly_expenses,
        'total_debts': total_debts,
        'total_sales_ever': total_sales_ever,
        'recent_sales': recent_sales,
        'recent_debts': recent_debts,
        'recent_expenses': recent_expenses,
        'overdue_debts': overdue_debts,
        'overdue_count': overdue_debts.count(),
        'total_customers': Customer.objects.count(),
        'total_staff': Staff.objects.filter(is_active=True).count(),
        'chart_labels': json.dumps(chart_labels),
        'chart_sales': json.dumps(chart_sales),
        'chart_expenses': json.dumps(chart_expenses),
        'monthly_labels': json.dumps(monthly_labels),
        'monthly_sales_data': json.dumps(monthly_sales_data),
        'monthly_expense_data': json.dumps(monthly_expense_data),
    }
    return render(request, 'core/dashboard.html', context)


# ─── Customers ────────────────────────────────────────────────────────────────

@login_required
def customers_list(request):
    q = request.GET.get('q', '')
    customers = Customer.objects.all()
    if q:
        customers = customers.filter(Q(name__icontains=q) | Q(phone__icontains=q))
    return render(request, 'core/customers_list.html', {'customers': customers, 'q': q})


@login_required
def customer_add(request):
    form = CustomerForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Customer added successfully.')
        return redirect('customers_list')
    return render(request, 'core/customer_form.html', {'form': form, 'title': 'Add Customer'})


@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if form.is_valid():
        form.save()
        messages.success(request, 'Customer updated.')
        return redirect('customer_detail', pk=pk)
    return render(request, 'core/customer_form.html', {'form': form, 'title': 'Edit Customer', 'customer': customer})


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    sales = customer.sales.order_by('-date')
    debts = customer.debts.order_by('-created_at')
    return render(request, 'core/customer_detail.html', {
        'customer': customer,
        'sales': sales,
        'debts': debts,
    })


@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == 'POST':
        name = customer.name
        customer.delete()
        messages.success(request, f'Customer "{name}" deleted.')
        return redirect('customers_list')
    return render(request, 'core/confirm_delete.html', {'object': customer, 'type': 'Customer'})


# ─── Sales ────────────────────────────────────────────────────────────────────

@login_required
def sales_list(request):
    q = request.GET.get('q', '')
    sales = Sale.objects.select_related('customer').all()
    if q:
        sales = sales.filter(Q(product__icontains=q) | Q(customer__name__icontains=q))
    total = sales.aggregate(t=Sum('total'))['t'] or 0
    return render(request, 'core/sales_list.html', {'sales': sales, 'q': q, 'total': total})


@login_required
def sales_export(request):
    q = request.GET.get('q', '')
    sales = Sale.objects.select_related('customer').all()
    if q:
        sales = sales.filter(Q(product__icontains=q) | Q(customer__name__icontains=q))

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Product', 'Customer', 'Quantity', 'Unit Price', 'Total', 'Payment Method', 'Notes'])

    for sale in sales.order_by('-date', '-created_at'):
        writer.writerow([
            sale.date,
            sale.product,
            sale.customer.name if sale.customer else 'Walk-in',
            sale.quantity,
            sale.unit_price,
            sale.total,
            sale.get_payment_method_display(),
            sale.notes,
        ])

    return response


@login_required
def sale_add(request):
    form = SaleForm(request.POST or None)
    if request.POST:
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save()
            # Auto-create debt if payment is credit
            if sale.payment_method == 'credit' and sale.customer:
                Debt.objects.create(
                    customer=sale.customer,
                    amount=sale.total,
                    description=f"Credit sale: {sale.product}",
                )
                messages.info(request, 'Debt record auto-created for credit sale.')
            messages.success(request, 'Sale recorded successfully.')
            return redirect('sales_list')
    return render(request, 'core/sale_form.html', {'form': form, 'title': 'Record Sale'})


@login_required
def sale_edit(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    form = SaleForm(request.POST or None, instance=sale)
    if form.is_valid():
        form.save()
        messages.success(request, 'Sale updated.')
        return redirect('sales_list')
    return render(request, 'core/sale_form.html', {'form': form, 'title': 'Edit Sale', 'sale': sale})


@login_required
def sale_delete(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == 'POST':
        sale.delete()
        messages.success(request, 'Sale record deleted.')
        return redirect('sales_list')
    return render(request, 'core/confirm_delete.html', {'object': sale, 'type': 'Sale'})


# ─── Debts ────────────────────────────────────────────────────────────────────

@login_required
def debts_list(request):
    filter_type = request.GET.get('filter', 'unpaid')
    debts = Debt.objects.select_related('customer').all()
    if filter_type == 'unpaid':
        debts = debts.filter(is_paid=False)
    elif filter_type == 'paid':
        debts = debts.filter(is_paid=True)
    elif filter_type == 'overdue':
        debts = debts.filter(is_paid=False, due_date__lt=timezone.now().date())

    total = debts.aggregate(t=Sum('amount'))['t'] or 0
    return render(request, 'core/debts_list.html', {
        'debts': debts,
        'filter_type': filter_type,
        'total': total,
    })


@login_required
def debt_add(request):
    form = DebtForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Debt recorded.')
        return redirect('debts_list')
    return render(request, 'core/debt_form.html', {'form': form, 'title': 'Record Debt'})


@login_required
def debt_edit(request, pk):
    debt = get_object_or_404(Debt, pk=pk)
    form = DebtForm(request.POST or None, instance=debt)
    if form.is_valid():
        form.save()
        messages.success(request, 'Debt updated.')
        return redirect('debts_list')
    return render(request, 'core/debt_form.html', {'form': form, 'title': 'Edit Debt', 'debt': debt})


@login_required
def debt_mark_paid(request, pk):
    debt = get_object_or_404(Debt, pk=pk)
    debt.is_paid = True
    debt.paid_date = timezone.now().date()
    debt.save()
    messages.success(request, f'Debt of ₦{debt.amount} for {debt.customer.name} marked as paid.')
    return redirect('debts_list')


@login_required
def debt_delete(request, pk):
    debt = get_object_or_404(Debt, pk=pk)
    if request.method == 'POST':
        debt.delete()
        messages.success(request, 'Debt record deleted.')
        return redirect('debts_list')
    return render(request, 'core/confirm_delete.html', {'object': debt, 'type': 'Debt'})


# ─── Expenses ─────────────────────────────────────────────────────────────────

@login_required
def expenses_list(request):
    q = request.GET.get('q', '')
    expenses = Expense.objects.all()
    if q:
        expenses = expenses.filter(Q(description__icontains=q) | Q(category__icontains=q))
    total = expenses.aggregate(t=Sum('amount'))['t'] or 0
    by_category = expenses.values('category').annotate(total=Sum('amount')).order_by('-total')
    return render(request, 'core/expenses_list.html', {
        'expenses': expenses,
        'q': q,
        'total': total,
        'by_category': by_category,
    })


@login_required
def expense_add(request):
    form = ExpenseForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Expense recorded.')
        return redirect('expenses_list')
    return render(request, 'core/expense_form.html', {'form': form, 'title': 'Record Expense'})


@login_required
def expense_edit(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    form = ExpenseForm(request.POST or None, instance=expense)
    if form.is_valid():
        form.save()
        messages.success(request, 'Expense updated.')
        return redirect('expenses_list')
    return render(request, 'core/expense_form.html', {'form': form, 'title': 'Edit Expense', 'expense': expense})


@login_required
def expense_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        expense.delete()
        messages.success(request, 'Expense deleted.')
        return redirect('expenses_list')
    return render(request, 'core/confirm_delete.html', {'object': expense, 'type': 'Expense'})


# ─── Income ───────────────────────────────────────────────────────────────────

@login_required
def income_list(request):
    income = Income.objects.all()
    total = income.aggregate(t=Sum('amount'))['t'] or 0
    return render(request, 'core/income_list.html', {'income': income, 'total': total})


@login_required
def income_add(request):
    form = IncomeForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Income recorded.')
        return redirect('income_list')
    return render(request, 'core/income_form.html', {'form': form, 'title': 'Record Income'})


@login_required
def income_edit(request, pk):
    income = get_object_or_404(Income, pk=pk)
    form = IncomeForm(request.POST or None, instance=income)
    if form.is_valid():
        form.save()
        messages.success(request, 'Income updated.')
        return redirect('income_list')
    return render(request, 'core/income_form.html', {'form': form, 'title': 'Edit Income', 'income': income})


@login_required
def income_delete(request, pk):
    income = get_object_or_404(Income, pk=pk)
    if request.method == 'POST':
        income.delete()
        messages.success(request, 'Income record deleted.')
        return redirect('income_list')
    return render(request, 'core/confirm_delete.html', {'object': income, 'type': 'Income'})


# ─── Staff ────────────────────────────────────────────────────────────────────

@login_required
def staff_list(request):
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access staff management.')
        return redirect('dashboard')
    staff = Staff.objects.all()
    return render(request, 'core/staff_list.html', {'staff': staff})


@login_required
def staff_add(request):
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access staff management.')
        return redirect('dashboard')
    form = StaffForm(request.POST or None)
    if form.is_valid():
        staff = form.save(commit=False)
        user_model = get_user_model()
        user = None
        if staff.user:
            user = staff.user
        else:
            user = user_model.objects.create_user(
                username=form.cleaned_data['username'],
                email=staff.email or '',
                password=form.cleaned_data['password'] or 'changeme123',
                is_staff=True,
                is_active=staff.is_active,
            )

        if form.cleaned_data.get('password'):
            user.set_password(form.cleaned_data['password'])
        user.email = staff.email or ''
        user.is_active = staff.is_active
        user.is_staff = True
        user.save()

        staff.user = user
        staff.save()
        messages.success(request, 'Staff member added and can now sign in.')
        return redirect('staff_list')
    return render(request, 'core/staff_form.html', {'form': form, 'title': 'Add Staff Member'})


@login_required
def staff_edit(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access staff management.')
        return redirect('dashboard')
    staff = get_object_or_404(Staff, pk=pk)
    form = StaffForm(request.POST or None, instance=staff)
    if form.is_valid():
        staff = form.save(commit=False)
        user_model = get_user_model()
        if staff.user is None:
            user = user_model.objects.create_user(
                username=form.cleaned_data['username'],
                email=staff.email or '',
                password=form.cleaned_data['password'] or 'changeme123',
                is_staff=True,
                is_active=staff.is_active,
            )
            staff.user = user
        else:
            user = staff.user
            user.username = form.cleaned_data['username']
            user.email = staff.email or ''
            user.is_active = staff.is_active
            user.is_staff = True
            if form.cleaned_data.get('password'):
                user.set_password(form.cleaned_data['password'])
            user.save()

        if not form.cleaned_data.get('password') and staff.user is not None:
            staff.user.is_active = staff.is_active
            staff.user.is_staff = True
            staff.user.email = staff.email or ''
            staff.user.save()

        staff.save()
        messages.success(request, 'Staff record updated.')
        return redirect('staff_list')
    return render(request, 'core/staff_form.html', {'form': form, 'title': 'Edit Staff', 'staff_obj': staff})


@login_required
def staff_delete(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access staff management.')
        return redirect('dashboard')
    staff = get_object_or_404(Staff, pk=pk)
    if request.method == 'POST':
        name = staff.name
        staff.delete()
        messages.success(request, f'Staff member "{name}" removed.')
        return redirect('staff_list')
    return render(request, 'core/confirm_delete.html', {'object': staff, 'type': 'Staff Member'})
