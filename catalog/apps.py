from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "catalog"

    def ready(self) -> None:
        from django.contrib import admin

        admin.site.site_header = "Domikeep"
        admin.site.site_title = "Domikeep"
        admin.site.index_title = "Catalog"
