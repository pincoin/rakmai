import logging

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.db.models import Count
from django.http import (
    JsonResponse, Http404
)
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views import generic

from rakmai.helpers import get_sub_domain
from rakmai.viewmixins import (
    SuperuserRequiredMixin, PageableMixin, HostContextMixin
)
from shop import models
from shop.tasks import (
    send_sms, send_notification_line
)
from shop.viewmixins import StoreContextMixin
from . import forms
from . import settings as help_settings


class HomeView(HostContextMixin, StoreContextMixin, generic.RedirectView):
    permanent = False
    query_string = True
    pattern_name = 'help:faq-list'


class NoticeListView(PageableMixin, HostContextMixin, StoreContextMixin, generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'notice_messages'

    def get_queryset(self):
        sub_domain = get_sub_domain(self.request)

        self.block_size = help_settings.HELP_CHUNK_SIZE
        self.chunk_size = help_settings.HELP_BLOCK_SIZE

        cache_key = 'shop.viewmixins.NoticeListView.get_queryset({})'.format(sub_domain)
        cache_time = settings.CACHES['default']['TIMEOUT']

        queryset = cache.get(cache_key)

        if not queryset:
            if sub_domain and sub_domain == 'card':
                queryset = models.NoticeMessage.objects \
                    .filter(store__code=self.store.code, is_removed=False) \
                    .exclude(category=models.NoticeMessage.CATEGORY_CHOICES.price) \
                    .order_by('-created')
            else:
                queryset = models.NoticeMessage.objects \
                    .filter(store__code=self.store.code, is_removed=False) \
                    .order_by('-created')
            cache.set(cache_key, queryset, cache_time)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(NoticeListView, self).get_context_data(**kwargs)
        context['page_title'] = _('Notice')
        return context

    def get_template_names(self):
        return 'help/{}/notice_list.html'.format(self.store.theme)


class NoticeDetailView(HostContextMixin, StoreContextMixin, generic.DetailView):
    logger = logging.getLogger(__name__)
    context_object_name = 'notice_message'

    def get_queryset(self):
        cache_key = 'shop.viewmixins.NoticeDetailView.get_queryset()'
        cache_time = settings.CACHES['default']['TIMEOUT']

        queryset = cache.get(cache_key)

        if not queryset:
            queryset = models.NoticeMessage.objects \
                .filter(store__code=self.store.code, is_removed=False) \
                .order_by('-created')
            cache.set(cache_key, queryset, cache_time)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(NoticeDetailView, self).get_context_data(**kwargs)
        context['page_title'] = _('Notice : ') + self.object.title
        context['page_meta_description'] = self.object.content.replace('\r', '').replace('\n', '')
        return context

    def get_template_names(self):
        return 'help/{}/notice_detail.html'.format(self.store.theme)


class FaqListView(HostContextMixin, StoreContextMixin, generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'faq_messages'

    def get_queryset(self):
        cache_key = 'shop.viewmixins.FaqListView.get_queryset()'
        cache_time = settings.CACHES['default']['TIMEOUT']

        queryset = cache.get(cache_key)

        if not queryset:
            queryset = models.FaqMessage.objects \
                .filter(store__code=self.store.code, is_removed=False) \
                .order_by('position', '-created')
            cache.set(cache_key, queryset, cache_time)

        return queryset

    def get_context_data(self, **kwargs):
        context = super(FaqListView, self).get_context_data(**kwargs)
        context['page_title'] = _('Frequently Asked Questions')
        return context

    def get_template_names(self):
        return 'help/{}/faq_list.html'.format(self.store.theme)


class CustomerQuestionListView(PageableMixin, LoginRequiredMixin, HostContextMixin, StoreContextMixin,
                               generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'questions'

    def get_queryset(self):
        self.block_size = help_settings.HELP_CHUNK_SIZE
        self.chunk_size = help_settings.HELP_BLOCK_SIZE

        return models.CustomerQuestion.objects \
            .filter(store__code=self.store.code, is_removed=False, owner=self.request.user) \
            .annotate(answers_count=Count('answers')) \
            .order_by('-created')

    def get_context_data(self, **kwargs):
        context = super(CustomerQuestionListView, self).get_context_data(**kwargs)
        context['page_title'] = _('Customer Questions')
        return context

    def get_template_names(self):
        return 'help/{}/question_list.html'.format(self.store.theme)


class CustomerQuestionDetailView(LoginRequiredMixin, HostContextMixin, StoreContextMixin, generic.DetailView):
    logger = logging.getLogger(__name__)
    context_object_name = 'question'

    def get_queryset(self):
        return models.CustomerQuestion.objects \
            .select_related('order') \
            .filter(store__code=self.store.code, is_removed=False, owner=self.request.user) \
            .annotate(answers_count=Count('answers'))

    def get_context_data(self, **kwargs):
        context = super(CustomerQuestionDetailView, self).get_context_data(**kwargs)
        context['page_title'] = _('Customer Questions')
        return context

    def get_template_names(self):
        return 'help/{}/question_detail.html'.format(self.store.theme)


class CustomerQuestionCreateView(LoginRequiredMixin, HostContextMixin, StoreContextMixin, generic.CreateView):
    logger = logging.getLogger(__name__)
    model = models.CustomerQuestion
    context_object_name = 'question'
    form_class = forms.CustomerQuestionForm

    def get_context_data(self, **kwargs):
        context = super(CustomerQuestionCreateView, self).get_context_data(**kwargs)
        context['page_title'] = _('Customer Questions')
        return context

    def get_form_kwargs(self):
        kwargs = super(CustomerQuestionCreateView, self).get_form_kwargs()
        kwargs['store_code'] = self.store.code
        kwargs['page'] = self.request.GET['page'] if 'page' in self.request.GET else 1
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.store = self.store

        response = super(CustomerQuestionCreateView, self).form_valid(form)

        '''
        html_message = render_to_string('shop/{}/email/customer_question.html'.format('default'),
                                        {'question': self.object})
        send_notification_email.delay(
            _('[site] Customer Question'),
            'dummy',
            settings.EMAIL_NO_REPLY,
            [settings.EMAIL_CUSTOMER_SERVICE],
            html_message,
        )
        '''

        message = _('Customer Question')
        send_notification_line.delay(message)

        return response

    def get_success_url(self):
        return reverse('help:question-detail', args=(self.store.code, self.object.id,))

    def get_template_names(self):
        return 'help/{}/question_create.html'.format(self.store.theme)


class TestimonialsListView(PageableMixin, HostContextMixin, StoreContextMixin, generic.ListView):
    logger = logging.getLogger(__name__)
    context_object_name = 'testimonials'

    def get_queryset(self):
        self.block_size = help_settings.HELP_CHUNK_SIZE
        self.chunk_size = help_settings.HELP_BLOCK_SIZE

        return models.Testimonials.objects \
            .select_related('owner') \
            .filter(store__code=self.store.code, is_removed=False) \
            .order_by('-created')

    def get_context_data(self, **kwargs):
        context = super(TestimonialsListView, self).get_context_data(**kwargs)
        context['page_title'] = _('Testimonials')
        return context

    def get_template_names(self):
        return 'help/{}/testimonials_list.html'.format(self.store.theme)


class TestimonialsDetailView(HostContextMixin, StoreContextMixin, generic.DetailView):
    logger = logging.getLogger(__name__)
    context_object_name = 'testimonial'
    form_class = forms.TestimonialsAnswerForm

    def get_form_kwargs(self):
        return {
            'store_code': self.store.code,
            'testimonial': self.kwargs['pk'],
        }

    def get_queryset(self):
        return models.Testimonials.objects \
            .select_related('owner', 'owner__profile') \
            .filter(store__code=self.store.code, is_removed=False) \
            .annotate(answers_count=Count('answers')) \
            .order_by('-created')

    def get_context_data(self, **kwargs):
        context = super(TestimonialsDetailView, self).get_context_data(**kwargs)
        context['page_title'] = _('Testimonials : ') + self.object.title
        context['page_meta_description'] = self.object.content.replace('\r', '').replace('\n', '')
        context['store'] = self.store
        context['form'] = self.form_class(**self.get_form_kwargs())
        return context

    def get_template_names(self):
        return 'help/{}/testimonials_detail.html'.format(self.store.theme)


class TestimonialsCreateView(LoginRequiredMixin, HostContextMixin, StoreContextMixin, generic.CreateView):
    logger = logging.getLogger(__name__)
    model = models.Testimonials
    context_object_name = 'testimonial'
    form_class = forms.TestimonialsForm

    def get_context_data(self, **kwargs):
        context = super(TestimonialsCreateView, self).get_context_data(**kwargs)
        context['page_title'] = _('Testimonials')
        return context

    def get_form_kwargs(self):
        kwargs = super(TestimonialsCreateView, self).get_form_kwargs()
        kwargs['store_code'] = self.store.code
        kwargs['page'] = self.request.GET['page'] if 'page' in self.request.GET else 1
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.store = self.store

        return super(TestimonialsCreateView, self).form_valid(form)

    def get_success_url(self):
        return reverse('help:testimonials-detail', args=(self.store.code, self.object.id,))

    def get_template_names(self):
        return 'help/{}/testimonials_create.html'.format(self.store.theme)


class TestimonialsAnswerView(SuperuserRequiredMixin, HostContextMixin, StoreContextMixin, generic.FormView):
    form_class = forms.TestimonialsAnswerForm

    def form_valid(self, form):
        testimonial = models.Testimonials.objects.select_related('owner', 'owner__profile').get(pk=self.kwargs['pk'])
        form.instance.testimonial = testimonial
        form.save()

        code = '해피1천'

        if testimonial.owner.profile.phone:
            count = models.Voucher.objects \
                .select_related('product') \
                .filter(product__code=code,
                        status=models.Voucher.STATUS_CHOICES.purchased) \
                .count()

            if count > 0:
                vouchers = models.Voucher.objects \
                               .select_related('product') \
                               .filter(product__code=code, status=models.Voucher.STATUS_CHOICES.purchased) \
                               .order_by('pk')[:1]

                # Mark as sold
                # NOTE: Cannot update a query once a slice has been taken.
                voucher_pk = list(map(lambda x: x.id, vouchers))

                models.Voucher.objects.filter(pk__in=voucher_pk).update(status=models.Voucher.STATUS_CHOICES.sold)

                send_sms.delay(testimonial.owner.profile.phone, "[핀코인] [해피머니1천원] {} 발행일자 {}"
                               .format(vouchers[0].code, vouchers[0].remarks))

                form.instance.content = '{}\n\n해피머니 1천원: {}\n발행일자:{}'.format(form.instance.content,
                                                                             vouchers[0].code,
                                                                             vouchers[0].remarks)
            else:
                send_notification_line.delay(_('No giftcard'))

        return super(TestimonialsAnswerView, self).form_valid(form)

    def form_invalid(self, form):
        return JsonResponse({
            'status': 'false',
            'message': 'Bad Request'
        }, status=400)

    def get_success_url(self):
        return reverse('help:testimonials-detail', args=(self.store.code, self.kwargs['pk']))

    def get_template_names(self):
        return 'help/{}/error.html'.format(self.store.theme)


class CustomerQuestionCreateOrderView(CustomerQuestionCreateView):
    def dispatch(self, *args, **kwargs):
        if 'uuid' in self.kwargs:
            self.order = models.Order.objects.get(order_no=self.kwargs.get('uuid'))

            if self.order:
                return super(CustomerQuestionCreateOrderView, self).dispatch(*args, **kwargs)

        raise Http404

    def form_valid(self, form):
        form.instance.order = self.order

        return super(CustomerQuestionCreateOrderView, self).form_valid(form)


class GuideView(HostContextMixin, StoreContextMixin, generic.TemplateView):
    logger = logging.getLogger(__name__)

    def get_context_data(self, **kwargs):
        context = super(GuideView, self).get_context_data(**kwargs)
        return context

    def get_template_names(self):
        return 'help/{}/guide.html'.format(self.store.theme)
