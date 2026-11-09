from django.contrib import admin

from .models import UATCase, UATPlan, UATResult, UATSection


class SectionInline(admin.TabularInline):
    model = UATSection
    extra = 0
    fields = ('order', 'key', 'name')


@admin.register(UATPlan)
class UATPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'status', 'due_date', 'created_at')
    filter_horizontal = ('testers',)
    inlines = [SectionInline]


@admin.register(UATCase)
class UATCaseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'section')
    list_filter = ('section__plan',)
    search_fields = ('code', 'title')


@admin.register(UATResult)
class UATResultAdmin(admin.ModelAdmin):
    list_display = ('case', 'tester', 'status', 'fix_status', 'updated_at')
    list_filter = ('status', 'fix_status', 'case__section__plan')
