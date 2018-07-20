from framework.models import Menu


def menus(request):
    menus = {}
    for menu in Menu.objects.all():
        menus[f'{menu.slug}_menu'] = menu.get_items(request)
    return menus
