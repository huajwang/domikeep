from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class WwwRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()
        if host == "www.domikeep.com":
            return HttpResponsePermanentRedirect(
                "https://domikeep.com" + request.get_full_path()
            )
        return self.get_response(request)


class HostSiteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(":")[0].lower()
        if host in settings.SHOP_HOSTS:
            request.urlconf = "domikeep.shop_urls"
            request.site_kind = "shop"
        else:
            request.urlconf = "domikeep.company_urls"
            request.site_kind = "company"
        return self.get_response(request)
