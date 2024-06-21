# attendance/admin.py

from django.contrib import admin
from .models import Student, AttendanceRecord

admin.site.site_header="Attendance_System"
admin.site.site_title="Attendance_System"
admin.site.index_title="Manage Attendance System"
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'time')
    list_filter = ('date', 'student')
