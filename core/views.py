from django.shortcuts import render


# Render the Home Page
def cover(request):
    return render(request, "cover.html")
