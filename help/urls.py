from django.urls import path

from . import views

app_name = 'help'

urlpatterns = [
    path('<str:store>/',
         views.HomeView.as_view(), name='home'),

    path('<str:store>/notice/',
         views.NoticeListView.as_view(), name='notice-list'),

    path('<str:store>/notice/<int:pk>/',
         views.NoticeDetailView.as_view(), name='notice-detail'),

    path('<str:store>/faq/',
         views.FaqListView.as_view(), name='faq-list'),

    path('<str:store>/qna/',
         views.CustomerQuestionListView.as_view(), name='question-list'),

    path('<str:store>/qna/<int:pk>/',
         views.CustomerQuestionDetailView.as_view(), name='question-detail'),

    path('<str:store>/qna/create/',
         views.CustomerQuestionCreateView.as_view(), name='question-create'),

    path('<str:store>/qna/create/<uuid:uuid>/',
         views.CustomerQuestionCreateOrderView.as_view(), name='question-create-order'),

    path('<str:store>/testimonials/',
         views.TestimonialsListView.as_view(), name='testimonials-list'),

    path('<str:store>/testimonials/<int:pk>/',
         views.TestimonialsDetailView.as_view(), name='testimonials-detail'),

    path('<str:store>/testimonials/create/',
         views.TestimonialsCreateView.as_view(), name='testimonials-create'),

    path('<str:store>/testimonials/<int:pk>/answer',
         views.TestimonialsAnswerView.as_view(), name='testimonials-answer'),

    path('<str:store>/guide/',
         views.GuideView.as_view(), name='guide'),
]
