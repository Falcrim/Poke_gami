# usuario/models/Battle.py - MODIFICADO
from django.db import models
from .Player import Player
from .PlayerPokemon import PlayerPokemon
from pokemon.models.Pokemon import Pokemon
from pokemon.models.Move import Move
import json


class Battle(models.Model):
    BATTLE_TYPES = (
        ('wild', 'Salvaje'),
        ('trainer', 'Entrenador'),
        ('pvp', 'PvP'),
    )
    BATTLE_STATES = (
        ('waiting', 'Esperando'),
        ('active', 'Activa'),
        ('won', 'Ganada'),
        ('lost', 'Perdida'),
        ('fled', 'Huyó'),
        ('draw', 'Empate'),
    )
    BATTLE_FORMATS = (
        ('1vs1', '1 Pokémon por jugador'),
        ('2vs2', '2 Pokémon por jugador'),
    )

    battle_type = models.CharField(max_length=10, choices=BATTLE_TYPES, default='wild')
    battle_format = models.CharField(max_length=5, choices=BATTLE_FORMATS, null=True, blank=True)

    # Jugadores
    player1 = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='pvp_battles_as_player1', null=True,
                                blank=True)
    player2 = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='pvp_battles_as_player2', null=True,
                                blank=True)
    current_turn = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='current_turn_battles')
    winner = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='won_battles')

    # Para batallas salvajes/entrenador (mantener compatibilidad)
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='battles', null=True, blank=True)
    wild_pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE, null=True, blank=True)
    wild_level = models.IntegerField(null=True, blank=True)
    wild_current_hp = models.IntegerField(null=True, blank=True)
    wild_max_hp = models.IntegerField(null=True, blank=True)

    trainer_name = models.CharField(max_length=100, blank=True, null=True)
    trainer_sprite = models.URLField(blank=True, null=True)
    trainer_dialogue = models.TextField(blank=True, null=True)
    trainer_money_reward = models.IntegerField(default=0)
    trainer_team = models.JSONField(default=list)
    current_trainer_pokemon = models.IntegerField(default=0)

    # Equipos PvP (almacenado como JSON)
    player1_team = models.JSONField(default=list)
    player2_team = models.JSONField(default=list)
    player1_current_pokemon = models.IntegerField(default=0)
    player2_current_pokemon = models.IntegerField(default=0)

    # Pokémon actual del jugador (para compatibilidad)
    player_pokemon = models.ForeignKey(PlayerPokemon, on_delete=models.CASCADE, related_name='active_battles',
                                       null=True, blank=True)

    # Estado del combate
    state = models.CharField(max_length=10, choices=BATTLE_STATES, default='active')
    turn = models.IntegerField(default=0)

    # Información de la sala
    room_code = models.CharField(max_length=8, unique=True, null=True, blank=True)
    is_private = models.BooleanField(default=False)
    password = models.CharField(max_length=50, blank=True, null=True)

    # Movimientos disponibles del Pokémon salvaje
    wild_moves = models.ManyToManyField(Move, related_name='wild_battles', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'battles'
        indexes = [
            models.Index(fields=['room_code']),
            models.Index(fields=['state', 'battle_type']),
        ]

    def __str__(self):
        if self.battle_type == 'pvp':
            return f"PvP Battle {self.id}: {self.player1.user.username} vs {self.player2.user.username if self.player2 else '...'}"
        elif self.battle_type == 'wild':
            return f"Wild Battle {self.id}: {self.player.user.username} vs {self.wild_pokemon.name}"
        else:
            return f"Trainer Battle {self.id}: {self.player.user.username} vs {self.trainer_name}"

    @property
    def is_active(self):
        return self.state == 'active'

    @property
    def is_waiting(self):
        return self.state == 'waiting'

    @property
    def is_full(self):
        return self.player1 is not None and self.player2 is not None

    def get_current_player_team(self, player):
        """Obtiene el equipo del jugador actual"""
        if player == self.player1:
            return self.player1_team
        elif player == self.player2:
            return self.player2_team
        return []

    def get_current_opponent_team(self, player):
        """Obtiene el equipo del oponente"""
        if player == self.player1:
            return self.player2_team
        elif player == self.player2:
            return self.player1_team
        return []

    def get_current_pokemon_index(self, player):
        """Obtiene el índice del Pokémon actual del jugador"""
        if player == self.player1:
            return self.player1_current_pokemon
        elif player == self.player2:
            return self.player2_current_pokemon
        return 0

    def get_current_pokemon(self, player):
        """Obtiene el Pokémon actual del jugador"""
        team = self.get_current_player_team(player)
        index = self.get_current_pokemon_index(player)
        if 0 <= index < len(team):
            return team[index]
        return None

    def get_opponent_current_pokemon(self, player):
        """Obtiene el Pokémon actual del oponente"""
        opponent = self.player2 if player == self.player1 else self.player1
        return self.get_current_pokemon(opponent)

    def is_player_turn(self, player):
        """Verifica si es el turno del jugador"""
        return self.current_turn == player

    def switch_to_next_pokemon(self, player):
        """Cambia al siguiente Pokémon del jugador"""
        team = self.get_current_player_team(player)

        if player == self.player1:
            for i in range(len(team)):
                next_index = (self.player1_current_pokemon + i + 1) % len(team)
                if team[next_index]['current_hp'] > 0:
                    self.player1_current_pokemon = next_index
                    return True
        else:
            for i in range(len(team)):
                next_index = (self.player2_current_pokemon + i + 1) % len(team)
                if team[next_index]['current_hp'] > 0:
                    self.player2_current_pokemon = next_index
                    return True
        return False

    def check_team_defeated(self, team):
        """Verifica si todo un equipo está derrotado"""
        return all(pokemon['current_hp'] <= 0 for pokemon in team)

    def end_battle(self, winner):
        """Termina la batalla y actualiza estadísticas"""
        self.state = 'won' if winner else 'draw'
        self.winner = winner

        if winner:
            # Actualizar estadísticas de los jugadores
            winner.user.battles_won += 1
            loser = self.player2 if winner == self.player1 else self.player1
            loser.user.battles_lost += 1

            # Actualizar rating (sistema Elo simple)
            self.update_ratings(winner, loser)

            winner.user.save()
            loser.user.save()

        self.save()

    def update_ratings(self, winner, loser):
        """Actualiza el rating PvP de los jugadores (sistema Elo simple)"""
        K = 32  # Factor K para ajuste

        # Calcular probabilidad esperada
        expected_winner = 1 / (1 + 10 ** ((loser.user.pvp_rating - winner.user.pvp_rating) / 400))
        expected_loser = 1 - expected_winner

        # Actualizar ratings
        winner.user.pvp_rating += int(K * (1 - expected_winner))
        loser.user.pvp_rating += int(K * (0 - expected_loser))

        # Asegurar rating mínimo
        if loser.user.pvp_rating < 0:
            loser.user.pvp_rating = 0

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