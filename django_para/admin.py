from django.contrib import admin
from django_para.models import Para, ParaItem

class ParaItemInline(admin.TabularInline):
    model = ParaItem

class ParaAdmin(admin.ModelAdmin):
    inlines = [ParaItemInline,]

admin.site.register(Para, ParaAdmin)
