from django.db import models
from .Player import Player
from .PlayerPokemon import PlayerPokemon
from pokemon.models.Pokemon import Pokemon
from pokemon.models.Move import Move


class Battle(models.Model):
    BATTLE_STATES = (
        ('active', 'Activa'),
        ('won', 'Ganada'),
        ('lost', 'Perdida'),
        ('fled', 'Huyó'),
    )

    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='battles')
    wild_pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE)
    wild_level = models.IntegerField()
    wild_current_hp = models.IntegerField()
    wild_max_hp = models.IntegerField()

    # Pokémon actual del jugador en combate
    player_pokemon = models.ForeignKey(PlayerPokemon, on_delete=models.CASCADE, related_name='active_battles')

    # Estado del combate
    state = models.CharField(max_length=10, choices=BATTLE_STATES, default='active')
    turn = models.IntegerField(default=0)  # 0 = jugador, 1 = salvaje

    # Movimientos disponibles del Pokémon salvaje
    wild_moves = models.ManyToManyField(Move, related_name='wild_battles')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'battles'

    def __str__(self):
        return f"Battle {self.id}: {self.player.user.username} vs {self.wild_pokemon.name}"

    @property
    def is_active(self):
        return self.state == 'active'