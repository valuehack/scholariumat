from framework.models import Menu


def menu(request):
    return {'menu': Menu.objects.get(slug='main')}
