from django.contrib import admin

from .models import (
    User,
    Organisation,
    UserOrganisation,
    Patient,
    OrganisationInvite
)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass

@admin.register(Organisation)
class OrganisationAdmin(admin.ModelAdmin):
    pass

@admin.register(UserOrganisation)
class UserOrganisationAdmin(admin.ModelAdmin):
    pass

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    pass

@admin.register(OrganisationInvite)
class OrganisationInviteAdmin(admin.ModelAdmin):
    pass