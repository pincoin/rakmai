def get_sub_domain(request):
    host = request.META.get('HTTP_HOST', '').split('.', 1)

    if len(host) == 2:
        return host[0]


def get_domain(request):
    host = request.META.get('HTTP_HOST', '').split('.', 1)

    if len(host) == 2:
        return host[1]


def get_domains(request):
    host = request.META.get('HTTP_HOST', '').split('.', 1)

    if len(host) == 2:
        return {
            'sub_domain': host[0],
            'domain': host[1]
        }
