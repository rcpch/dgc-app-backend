from django.contrib import admin

from .models import User, Patient, UserPatient, SharePatient

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    pass

@admin.register(UserPatient)
class UserPatientAdmin(admin.ModelAdmin):
    pass

@admin.register(SharePatient)
class SharePatientAdmin(admin.ModelAdmin):
    pass