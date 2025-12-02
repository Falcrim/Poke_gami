from django.db import models


class Pokemon(models.Model):
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

    pokedex_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=50)
    type1 = models.CharField(max_length=10, choices=POKEMON_TYPES)
    type2 = models.CharField(max_length=10, choices=POKEMON_TYPES, blank=True, null=True)

    base_hp = models.IntegerField()
    base_attack = models.IntegerField()
    base_defense = models.IntegerField()
    base_special_attack = models.IntegerField()
    base_special_defense = models.IntegerField()
    base_speed = models.IntegerField()

    experience_growth = models.IntegerField()

    evolves_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    evolution_level = models.IntegerField(null=True, blank=True)

    sprite_front = models.URLField()
    sprite_back = models.URLField()

    class Meta:
        db_table = 'pokemon'
        ordering = ['pokedex_id']

    def __str__(self):
        return f"{self.pokedex_id}: {self.name}"