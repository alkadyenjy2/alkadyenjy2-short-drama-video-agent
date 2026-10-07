from web_app import publisher_status as _status


def handler(request):
    return _status()
