from django.db import models
from .User import User


class Player(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='player_profile')
    current_location = models.ForeignKey('pokemon.Location', on_delete=models.SET_NULL, null=True)
    money = models.IntegerField(default=3000)

    starter_chosen = models.BooleanField(default=False)

    class Meta:
        db_table = 'players'

    def __str__(self):
        return f"Player: {self.user.username}"