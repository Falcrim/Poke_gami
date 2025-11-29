from django.db import models
from .Pokemon import Pokemon
from .Location import Location


class WildPokemonEncounter(models.Model):
    RARITY_CHOICES = (
        ('common', 'Común'),
        ('uncommon', 'Poco Común'),
        ('rare', 'Raro'),
        ('very_rare', 'Muy Raro'),
    )

    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='wild_pokemons')
    pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE)
    min_level = models.IntegerField()
    max_level = models.IntegerField()
    rarity = models.CharField(max_length=10, choices=RARITY_CHOICES)

    class Meta:
        db_table = 'wild_pokemon_encounters'
        unique_together = ['location', 'pokemon']

    def __str__(self):
        return f"{self.pokemon.name} en {self.location.name} (Lv.{self.min_level}-{self.max_level})"

    def get_rarity_display(self):
        rarity_display = {
            'common': 'Común',
            'uncommon': 'Poco Común',
            'rare': 'Raro',
            'very_rare': 'Muy Raro'
        }
        return rarity_display.get(self.rarity, self.rarity)
