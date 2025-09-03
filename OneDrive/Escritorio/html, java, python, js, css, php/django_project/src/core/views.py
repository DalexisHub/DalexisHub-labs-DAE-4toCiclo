from django.shortcuts import render
from .models import Item
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import ItemSerializer

def item_list(request):
    items = Item.objects.all()
    return render(request, 'core/item_list.html', {'items': items})

def api_test(request):
    return render(request, 'core/api_test.html')

@api_view(['GET'])
def item_api_list(request):
    items = Item.objects.all()
    serializer = ItemSerializer(items, many=True)
    return Response(serializer.data)