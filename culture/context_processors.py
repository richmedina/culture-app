from django.conf import settings

def google_analytics(request):
    return {
        'GA_MEASUREMENT_ID': getattr(settings, 'GA_MEASUREMENT_ID', None)
    }