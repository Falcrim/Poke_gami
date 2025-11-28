from django.db import models
from .Pokemon import Pokemon
from .Move import Move


class PokemonMove(models.Model):
    pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE, related_name='moves_by_level')
    move = models.ForeignKey(Move, on_delete=models.CASCADE)
    level = models.IntegerField()

    class Meta:
        db_table = 'pokemon_moves'
        ordering = ['level']

    def __str__(self):
        return f"{self.pokemon.name} aprende {self.move.name} al nivel {self.level}"