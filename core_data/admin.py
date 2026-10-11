from django.contrib import admin

from .models import Club, ClubEvent, Department, UserMember


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    search_fields = ['title']


@admin.register(ClubEvent)
class ClubEventAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent_id']
    list_filter = ['parent_id']
    search_fields = ['name', 'description']


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ['name', 'department', 'head']
    list_filter = ['department']
    search_fields = ['name']


@admin.register(UserMember)
class UserMemberAdmin(admin.ModelAdmin):
    list_display = ['username', 'department_id', 'club_id', 'role', 'event_date']
    list_filter = ['department_id', 'club_id', 'role']
    search_fields = ['username']
