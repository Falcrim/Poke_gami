from django.db import models

from .Trainer import Trainer
from .Player import Player
from .PlayerPokemon import PlayerPokemon
from pokemon.models.Pokemon import Pokemon
from pokemon.models.Move import Move


class Battle(models.Model):
    BATTLE_TYPES = (
        ('wild', 'Salvaje'),
        ('trainer', 'Entrenador'),
    )
    BATTLE_STATES = (
        ('active', 'Activa'),
        ('won', 'Ganada'),
        ('lost', 'Perdida'),
        ('fled', 'Huyó'),
    )
    battle_type = models.CharField(max_length=10, choices=BATTLE_TYPES, default='wild')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='battles')
    wild_pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE, null=True, blank=True)
    wild_level = models.IntegerField(null=True, blank=True)
    wild_current_hp = models.IntegerField(null=True, blank=True)
    wild_max_hp = models.IntegerField(null=True, blank=True)
    wild_moves = models.ManyToManyField(Move, related_name='wild_battles', blank=True)

    trainer_name = models.CharField(max_length=100, blank=True, null=True)
    trainer_sprite = models.URLField(blank=True, null=True)
    trainer_dialogue = models.TextField(blank=True, null=True)
    trainer_money_reward = models.IntegerField(default=0)

    # Equipo del entrenador (almacenado como JSON)
    trainer_team = models.JSONField(default=list)
    current_trainer_pokemon = models.IntegerField(default=0)  # Índice del Pokémon actual

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
        if self.battle_type == 'wild':
            return f"Battle {self.id}: {self.player.user.username} vs {self.wild_pokemon.name}"
        else:
            return f"Battle {self.id}: {self.player.user.username} vs {self.trainer.name}"

    @property
    def is_active(self):
        return self.state == 'active'

    @property
    def current_opponent_pokemon(self):
        """Devuelve el Pokémon actual del oponente"""
        if self.battle_type == 'wild':
            return {
                'pokemon': self.wild_pokemon,
                'level': self.wild_level,
                'current_hp': self.wild_current_hp,
                'max_hp': self.wild_max_hp
            }
        else:
            if self.trainer_team and self.current_trainer_pokemon < len(self.trainer_team):
                return self.trainer_team[self.current_trainer_pokemon]
            return None

    def is_trainer_defeated(self):
        """Verifica si todos los Pokémon del entrenador están derrotados"""
        if self.battle_type != 'trainer':
            return False

        for pokemon in self.trainer_team:
            if pokemon['current_hp'] > 0:
                return False
        return True
