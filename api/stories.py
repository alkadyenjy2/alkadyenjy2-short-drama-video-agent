from web_app import get_stories as _stories


def handler(request):
    return _stories()
