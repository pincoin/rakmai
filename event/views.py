from django.views import generic

from shop.viewmixins import StoreContextMixin


class LotteCardPCView(StoreContextMixin, generic.TemplateView):
    template_name = 'event/lotte_card_pc.html'


class LotteCardMobileView(StoreContextMixin, generic.TemplateView):
    template_name = 'event/lotte_card_mobile.html'
