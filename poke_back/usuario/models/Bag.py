from django.db import models
from .Player import Player


class Bag(models.Model):
    player = models.OneToOneField(Player, on_delete=models.CASCADE, related_name='bag')
    pokeballs = models.IntegerField(default=5)  # Inicial: 5 pokeballs
    potions = models.IntegerField(default=2)  # Inicial: 2 pociones

    class Meta:
        db_table = 'bags'

    def __str__(self):
        return f"Bag of {self.player.user.username}"