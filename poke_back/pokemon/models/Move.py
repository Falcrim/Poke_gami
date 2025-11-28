from django.db import models


class Move(models.Model):
    POKEMON_TYPES = (
        ('normal', 'Normal'),
        ('fire', 'Fuego'),
        ('water', 'Agua'),
        ('electric', 'Eléctrico'),
        ('grass', 'Planta'),
        ('ice', 'Hielo'),
        ('fighting', 'Lucha'),
        ('poison', 'Veneno'),
        ('ground', 'Tierra'),
        ('flying', 'Volador'),
        ('psychic', 'Psíquico'),
        ('bug', 'Bicho'),
        ('rock', 'Roca'),
        ('ghost', 'Fantasma'),
        ('dragon', 'Dragón'),
        ('dark', 'Siniestro'),
        ('steel', 'Acero'),
        ('fairy', 'Hada'),
    )

    DAMAGE_CLASS = (
        ('physical', 'Físico'),
        ('special', 'Especial'),
        ('status', 'Estado'),
    )

    name = models.CharField(max_length=50)
    type = models.CharField(max_length=10, choices=POKEMON_TYPES)
    power = models.IntegerField(null=True, blank=True)
    accuracy = models.IntegerField(null=True, blank=True)
    pp = models.IntegerField()
    damage_class = models.CharField(max_length=10, choices=DAMAGE_CLASS)

    class Meta:
        db_table = 'moves'

    def __str__(self):
        return self.name