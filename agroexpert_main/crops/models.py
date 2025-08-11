from django.db import models


class Crop(models.Model):
    name = models.CharField(max_length=100, unique=True)
    pH_range = models.CharField(max_length=50)  # e.g., "6.0-7.5"
    rainfall_range = models.CharField(max_length=50)  # e.g., "500-1500"
    planting_months = models.TextField(blank=True)  # e.g., "January, February, March"
    soil_types = models.TextField(blank=True)  # e.g., "Loamy, Sandy"
    priority = models.IntegerField(default=1)

    def __str__(self):
        return self.name

