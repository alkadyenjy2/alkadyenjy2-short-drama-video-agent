from web_app import health as _health


def handler(request):
    return _health()
