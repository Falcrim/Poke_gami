from django.db import models
from .Player import Player


class Pokedex(models.Model):
    PLAYER_STATES = (
        ('seen', 'Visto'),
        ('caught', 'Capturado'),
    )

    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='pokedex_entries')
    pokemon = models.ForeignKey('pokemon.Pokemon', on_delete=models.CASCADE)
    state = models.CharField(max_length=10, choices=PLAYER_STATES, default='seen')
    date_registered = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'pokedex_entries'
        unique_together = ['player', 'pokemon']

    def __str__(self):
        return f"{self.player.user.username} - {self.pokemon.name} ({self.state})"