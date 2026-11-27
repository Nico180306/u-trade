"""Django Admin de vendedores. Ningún cambio de estado se hace con save() directo: las acciones
invocan sellers.services (Regla 1)."""

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.template.response import TemplateResponse

from apps.core.exceptions import DomainError
from apps.sellers import services
from apps.sellers.models import SellerApplication, SellerProfile


class RejectionReasonForm(forms.Form):
    rejection_reason = forms.CharField(
        label="Motivo del rechazo",
        widget=forms.Textarea(attrs={"rows": 4, "cols": 80}),
        max_length=1000,
        help_text="Se enviará por correo a cada solicitante.",
    )


def _report(modeladmin, request, done: int, errors: list[str], verb: str) -> None:
    if done:
        modeladmin.message_user(request, f"{done} solicitud(es) {verb}.", messages.SUCCESS)
    for error in errors:
        modeladmin.message_user(request, error, messages.ERROR)


@admin.register(SellerApplication)
class SellerApplicationAdmin(admin.ModelAdmin):
    list_display = ("venture_name", "user", "status", "created_at", "reviewed_by", "reviewed_at")
    list_filter = ("status",)
    search_fields = ("venture_name", "user__email")
    ordering = ("-created_at",)
    list_select_related = ("user", "reviewed_by")
    actions = ("approve_applications", "reject_applications")
    readonly_fields = (
        "user",
        "venture_name",
        "description",
        "contact_phone",
        "instagram_handle",
        "status",
        "reviewed_by",
        "reviewed_at",
        "rejection_reason",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description="Aprobar solicitudes seleccionadas", permissions=["change"])
    def approve_applications(self, request, queryset):
        done, errors = 0, []
        for application in queryset:
            try:
                services.approve_seller_application(application.id, request.user)
                done += 1
            except DomainError as exc:
                errors.append(f"{application.venture_name}: {exc.message}")
        _report(self, request, done, errors, "aprobada(s)")

    @admin.action(description="Rechazar solicitudes seleccionadas…", permissions=["change"])
    def reject_applications(self, request, queryset):
        if "apply" in request.POST:
            form = RejectionReasonForm(request.POST)
            if form.is_valid():
                reason = form.cleaned_data["rejection_reason"]
                done, errors = 0, []
                for application in queryset:
                    try:
                        services.reject_seller_application(application.id, request.user, reason)
                        done += 1
                    except DomainError as exc:
                        errors.append(f"{application.venture_name}: {exc.message}")
                _report(self, request, done, errors, "rechazada(s)")
                return None  # vuelve al listado
        else:
            form = RejectionReasonForm()

        context = {
            **self.admin_site.each_context(request),
            "title": "Rechazar solicitudes de vendedor",
            "opts": self.model._meta,
            "queryset": queryset,
            "form": form,
            "action_checkbox_name": ACTION_CHECKBOX_NAME,
        }
        return TemplateResponse(
            request, "admin/sellers/sellerapplication/reject_reason.html", context
        )


@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    """Solo lectura: el perfil nace de approve_seller_application; las métricas las calculan
    servicios de reseñas/reservas y la (des)activación se hará vía services en otra rama."""

    list_display = ("venture_name", "user", "is_active", "avg_rating", "reviews_count")
    list_filter = ("is_active",)
    search_fields = ("venture_name", "user__email")
    ordering = ("-created_at",)
    list_select_related = ("user",)
    readonly_fields = (
        "user",
        "venture_name",
        "description",
        "contact_phone",
        "logo_url",
        "logo_public_id",
        "avg_rating",
        "reviews_count",
        "releases_count",
        "is_active",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
