from django.contrib import admin
from .models import Song, Myrating, MyList

# Register your models here.
admin.site.register(Song)
admin.site.register(Myrating)
admin.site.register(MyList)