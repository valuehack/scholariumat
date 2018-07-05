from django.http import HttpResponse
from django.contrib.auth.decorators import login_required


@login_required
def list(request):
    return HttpResponse('Test')


def detail(request):
    pass


def collection(request):
    pass
