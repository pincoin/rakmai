from django.urls import path

from . import views

app_name = 'rabop'

urlpatterns = [
    path('<str:store>/',
         views.HomeView.as_view(), name='home'),

    path('<str:store>/orders/',
         views.OrderListView.as_view(), name='order-list'),

    path('<str:store>/orders/<int:pk>/',
         views.OrderDetailView.as_view(), name='order-detail'),

    path('<str:store>/orders/<int:pk>/verify',
         views.OrderVerifyView.as_view(), name='order-verify'),

    path('<str:store>/orders/<int:pk>/unverify',
         views.OrderUnverifyView.as_view(), name='order-unverify'),

    path('<str:store>/orders/<int:pk>/send',
         views.OrderSendView.as_view(), name='order-send'),

    path('<str:store>/orders/<int:pk>/refund',
         views.OrderRefundView.as_view(), name='order-refund'),

    path('<str:store>/orders/<int:order>/payments/add',
         views.OrderPaymentAddView.as_view(), name='payment-add'),

    path('<str:store>/orders/<int:order>/payments/<int:pk>/delete',
         views.OrderPaymentDeleteView.as_view(), name='payment-delete'),

    path('<str:store>/naver-orders/',
         views.NaverOrderListView.as_view(), name='naver-order-list'),

    path('<str:store>/naver-orders/<int:pk>',
         views.NaverOrderDetailView.as_view(), name='naver-order-detail'),

    path('<str:store>/naver-orders/create',
         views.NaverOrderCreateView.as_view(), name='naver-order-create'),

    path('<str:store>/naver-orders/<int:pk>/delete',
         views.NaverOrderDeleteView.as_view(), name='naver-order-delete'),

    path('<str:store>/naver-orders/<int:pk>/send',
         views.NaverOrderSendView.as_view(), name='naver-order-send'),

    path('<str:store>/naver-orders/<int:pk>/revoke',
         views.NaverOrderRevokeView.as_view(), name='naver-order-revoke'),

    path('<str:store>/naver-orders/<int:pk>/resend',
         views.NaverOrderResendView.as_view(), name='naver-order-resend'),

    path('<str:store>/naver-orders/<int:pk>/refund',
         views.NaverOrderRefundView.as_view(), name='naver-order-refund'),

    path('<str:store>/questions/',
         views.CustomerQuestionListView.as_view(), name='question-list'),

    path('<str:store>/questions/<int:pk>/',
         views.CustomerQuestionDetailView.as_view(), name='question-detail'),

    path('<str:store>/customers/',
         views.CustomerListView.as_view(), name='customer-list'),

    path('<str:store>/customers/<int:pk>/',
         views.CustomerDetailView.as_view(), name='customer-detail'),

    path('<str:store>/customers/<int:pk>/verify-document',
         views.CustomerDocumentVerifyView.as_view(), name='customer-verify-document'),

    path('<str:store>/customers/<int:pk>/unverify-document',
         views.CustomerDocumentUnverifyView.as_view(), name='customer-unverify-document'),

    path('<str:store>/customers/<int:pk>/verify-email',
         views.CustomerEmailVerifyView.as_view(), name='customer-verify-email'),

    path('<str:store>/customers/<int:pk>/unverify-email',
         views.CustomerEmailUnverifyView.as_view(), name='customer-unverify-email'),

    path('<str:store>/sms/',
         views.SmsListView.as_view(), name='sms-list'),

    path('<str:store>/sms/send/',
         views.SmsCreateView.as_view(), name='sms-send'),

    path('<str:store>/stock/status/',
         views.StockStatusListView.as_view(), name='stock-status'),

    path('<str:store>/stock/bulk-upload',
         views.StockBulkUploadView.as_view(), name='stock-bulk-upload'),

    path('<str:store>/report/monthly/',
         views.MonthlySalesReportView.as_view(), name='sales-report-monthly'),

    path('<str:store>/report/daily/',
         views.DailySalesReportView.as_view(), name='sales-report-daily'),

    path('<str:store>/report/best-customers/',
         views.BestCustomersReportView.as_view(), name='best-customers-report'),

    path('<str:store>/report/best-sellers/',
         views.BestSellersReportView.as_view(), name='best-sellers-report'),

    path('<str:store>/report/best-sellers-by-category/',
         views.BestSellersByCategoryReportView.as_view(), name='best-sellers-by-category-report'),

    path('<str:store>/report/daily-payments/',
         views.DailyPaymentReportView.as_view(), name='daily-payments-report'),

    path('<str:store>/report/bank-account-balance/',
         views.CurrentBankAccountBalanceTemplateView.as_view(), name='bank-account-balance-report'),

    path('<str:store>/legacy/customers/',
         views.LegacyCustomerListView.as_view(), name='legacy-customer-list'),

    path('<str:store>/legacy/customers/<int:pk>/',
         views.LegacyCustomerDetailView.as_view(), name='legacy-customer-detail'),

    path('<str:store>/legacy/customers/<str:cellphone>/mms',
         views.LegacyCustomerMmsListView.as_view(), name='legacy-customer-mms-list'),
]
