from django.shortcuts import render

def memberships(request):
    return render(request, "memberships/memberships.html")
