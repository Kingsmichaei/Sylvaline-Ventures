from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Customer, Sale, Staff


class ExportViewsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='tester', password='secret123')
        self.customer = Customer.objects.create(name='Ada', phone='08012345678')
        self.sale = Sale.objects.create(
            customer=self.customer,
            product='Rice bag',
            description='Wholesale sale',
            quantity=2,
            unit_price=2500,
            payment_method='cash',
            date='2026-07-25',
        )

    def test_sales_export_returns_csv(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('sales_export'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('product', response.content.decode('utf-8').lower())
        self.assertIn('rice bag', response.content.decode('utf-8').lower())


class StaffAuthenticationTests(TestCase):
    def test_staff_can_create_login_account(self):
        self.admin = get_user_model().objects.create_user(username='admin', password='secret123')
        self.client.force_login(self.admin)

        response = self.client.post(reverse('staff_add'), {
            'name': 'Jane Staff',
            'role': 'cashier',
            'phone': '08012345678',
            'email': 'jane@example.com',
            'address': 'Lagos',
            'salary': '15000',
            'is_active': 'on',
            'date_joined': '2026-07-26',
            'username': 'jane',
            'password': 'staffpass123',
            'confirm_password': 'staffpass123',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(username='jane').exists())
        self.assertTrue(self.client.login(username='jane', password='staffpass123'))
        self.assertTrue(Staff.objects.filter(name='Jane Staff', user__username='jane').exists())
