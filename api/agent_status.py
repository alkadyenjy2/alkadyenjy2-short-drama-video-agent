from web_app import agent_status as _status


def handler(request):
    return _status()
