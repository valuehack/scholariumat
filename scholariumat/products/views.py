from django.contrib import messages

from .models import Item


class ItemRequestMixin():
    def post(self, request, *args, **kwargs):
        if 'requested_item' in request.POST:
            item = Item.objects.get(pk=request.POST['requested_item'])
            item.request()
            messages.info(request, 'Vielen Dank für Ihr Interesse. Wir werden Sie benachrichtigen, \
                sollte das Produkt verfügbar werden.')
        return super().post(request, *args, **kwargs)
