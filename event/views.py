from django.views import generic


class LotteCardPCView(generic.TemplateView):
    template_name = 'event/lotte_card_pc.html'


class LotteCardMobileView(generic.TemplateView):
    template_name = 'event/lotte_card_mobile.html'
