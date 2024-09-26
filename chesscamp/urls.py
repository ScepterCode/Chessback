"""
URL configuration for chesscamp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""


# chess_platform/urls.py (Project URLs)

from django.contrib import admin
from django.urls import path, include
from chess import views
from django.views.generic import RedirectView
from django.urls import get_resolver
from django.http import HttpResponse

def list_urls(request):
    url_list = []
    resolver = get_resolver()
    for url_pattern in resolver.url_patterns:
        if hasattr(url_pattern, 'url_patterns'):
            for sub_pattern in url_pattern.url_patterns:
                url_list.append(str(sub_pattern.pattern))
        else:
            url_list.append(str(url_pattern.pattern))
    
    return HttpResponse('<br>'.join(url_list))

urlpatterns = [
    path('admin/', admin.site.urls),
    path('chess/', include('chess.urls')),
    path('forum/', include('forum.urls')),
    path('notifications/', include('notifications.urls')),
    path('', RedirectView.as_view(url='/chess/', permanent=False)),
]

