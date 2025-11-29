from django.db import models
from django.core.exceptions import ValidationError
from .Player import Player
from pokemon.models.Pokemon import Pokemon
from pokemon.models.Move import Move


class PlayerPokemon(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='pokemons')
    pokemon = models.ForeignKey(Pokemon, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=50, blank=True, null=True)
    level = models.IntegerField(default=1)
    current_hp = models.IntegerField(default=0)
    experience = models.IntegerField(default=0)

    # Nuevo campo para equipo/reserva
    in_team = models.BooleanField(default=True)  # True = en equipo, False = en reserva
    order = models.IntegerField(default=0)  # NUEVO: Orden en el equipo (0-5)
    moves = models.ManyToManyField(Move, related_name='player_pokemons')

    # Stats actuales
    hp = models.IntegerField(default=0)
    attack = models.IntegerField(default=0)
    defense = models.IntegerField(default=0)
    special_attack = models.IntegerField(default=0)
    special_defense = models.IntegerField(default=0)
    speed = models.IntegerField(default=0)

    class Meta:
        db_table = 'player_pokemons'

    def __str__(self):
        if self.nickname:
            return f"{self.nickname} ({self.pokemon.name}) Lv.{self.level}"
        return f"{self.pokemon.name} Lv.{self.level}"

    def clean(self):
        # Validación: máximo 6 Pokémon en equipo
        if self.in_team and self.player.pokemons.filter(in_team=True).count() >= 6:
            if not self.pk:  # Solo para nuevos Pokémon
                raise ValidationError('No puedes tener más de 6 Pokémon en el equipo')

        # Validación: orden debe estar entre 0-5
        if self.in_team and (self.order < 0 or self.order > 5):
            raise ValidationError('El orden debe estar entre 0 y 5')

    def calculate_stats(self):
        """Calcula los stats sin llamar a save()"""
        self.hp = int((2 * self.pokemon.base_hp * self.level) / 100) + self.level + 10
        self.attack = int((2 * self.pokemon.base_attack * self.level) / 100) + 5
        self.defense = int((2 * self.pokemon.base_defense * self.level) / 100) + 5
        self.special_attack = int((2 * self.pokemon.base_special_attack * self.level) / 100) + 5
        self.special_defense = int((2 * self.pokemon.base_special_defense * self.level) / 100) + 5
        self.speed = int((2 * self.pokemon.base_speed * self.level) / 100) + 5

    def save(self, *args, **kwargs):
        if self.in_team:
            if not self.pk or self.order == 0:
                max_order = PlayerPokemon.objects.filter(
                    player=self.player,
                    in_team=True
                ).exclude(pk=self.pk).aggregate(models.Max('order'))['order__max'] or -1
                self.order = max_order + 1

            if self.order > 5:
                self.order = 5
        else:
            self.order = 0

        if not self.pk or self.has_changed_level():
            self.calculate_stats()
            if not self.current_hp or self.current_hp > self.hp:
                self.current_hp = self.hp

        super().save(*args, **kwargs)

        if self.in_team:
            self._reorder_team()

    def _reorder_team(self):
        team_pokemons = PlayerPokemon.objects.filter(
            player=self.player,
            in_team=True
        ).order_by('order', 'id')

        for new_order, pokemon in enumerate(team_pokemons):
            if pokemon.order != new_order:
                PlayerPokemon.objects.filter(pk=pokemon.pk).update(order=new_order)

    def has_changed_level(self):
        """Verifica si el nivel cambió"""
        if not self.pk:
            return True
        try:
            old = PlayerPokemon.objects.get(pk=self.pk)
            return old.level != self.level
        except PlayerPokemon.DoesNotExist:
            return True

    def get_available_moves(self):
        """Obtiene todos los movimientos que puede aprender por nivel"""
        from pokemon.models.PokemonMove import PokemonMove
        return PokemonMove.objects.filter(
            pokemon=self.pokemon,
            level__lte=self.level
        ).select_related('move')

    def can_learn_move(self, move):
        """Verifica si puede aprender un movimiento"""
        return self.get_available_moves().filter(move=move).exists()

    def teach_move(self, move):
        """Enseña un movimiento nuevo (maneja el límite de 4)"""
        if not self.can_learn_move(move):
            raise ValidationError(f"{self.pokemon.name} no puede aprender {move.name}")

        if self.moves.count() >= 4:
            raise ValidationError(f"{self.pokemon.name} ya tiene 4 movimientos")

        if self.moves.filter(id=move.id).exists():
            raise ValidationError(f"{self.pokemon.name} ya conoce {move.name}")

        self.moves.add(move)
        return True

    def full_heal(self):
        self.current_hp = self.hp
        PlayerPokemon.objects.filter(pk=self.pk).update(current_hp=self.hp)
