from django.shortcuts import render
from django.http import HttpResponse

# Render the Home Page
def cover(request):
    return render(request, 'cover.html')
