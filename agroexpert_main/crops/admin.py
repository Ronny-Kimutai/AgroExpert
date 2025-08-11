from django.contrib import admin
from .models import Crop

# Register your models here.
@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "pH_range", "rainfall_range", "planting_months", "soil_types", "priority")
