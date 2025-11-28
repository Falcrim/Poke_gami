from django.db import models


class Location(models.Model):
    LOCATION_TYPES = (
        ('town', 'Pueblo'),
        ('route', 'Ruta'),
    )

    name = models.CharField(max_length=50)
    location_type = models.CharField(max_length=10, choices=LOCATION_TYPES)
    connected_locations = models.ManyToManyField('self', symmetrical=False, blank=True)

    class Meta:
        db_table = 'locations'

    def __str__(self):
        return f"{self.name} ({self.get_location_type_display()})"