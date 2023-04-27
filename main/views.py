from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'Контакты.html')

def about_us(request):
    return render(request, 'О-нас.html')

