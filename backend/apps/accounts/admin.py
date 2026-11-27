from django.contrib import admin

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Solo lectura en esta rama: los cambios de estado de negocio sobre usuarios se agregarán
    como acciones que invoquen services.py (Regla 1). Superusuarios: `createsuperuser`."""

    list_display = (
        "email",
        "full_name",
        "is_active",
        "is_staff",
        "email_verified_at",
        "created_at",
    )
    list_filter = ("is_active", "is_staff")
    search_fields = ("email", "full_name")
    ordering = ("-created_at",)
    exclude = ("password",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
