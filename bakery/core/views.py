from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def cover(request):
    return render(request, 'cover.html')
