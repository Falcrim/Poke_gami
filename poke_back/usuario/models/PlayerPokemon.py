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

    just_evolved = models.BooleanField(default=False)

    class Meta:
        db_table = 'player_pokemons'

    def __str__(self):
        if self.nickname:
            return f"{self.nickname} ({self.pokemon.name}) Lv.{self.level}"
        return f"{self.pokemon.name} Lv.{self.level}"

    def clean(self):
        if self.in_team and self.player.pokemons.filter(in_team=True).count() >= 6:
            if not self.pk:  # Solo para nuevos Pokémon
                raise ValidationError('No puedes tener más de 6 Pokémon en el equipo')

        if self.in_team and (self.order < 0 or self.order > 5):
            raise ValidationError('El orden debe estar entre 0 y 5')

    def calculate_stats(self):
        self.hp = int((2 * self.pokemon.base_hp * self.level) / 100) + self.level + 10
        self.attack = int((2 * self.pokemon.base_attack * self.level) / 100) + 5
        self.defense = int((2 * self.pokemon.base_defense * self.level) / 100) + 5
        self.special_attack = int((2 * self.pokemon.base_special_attack * self.level) / 100) + 5
        self.special_defense = int((2 * self.pokemon.base_special_defense * self.level) / 100) + 5
        self.speed = int((2 * self.pokemon.base_speed * self.level) / 100) + 5

    def get_experience_required(self, level=None):
        if level is None:
            level = self.level + 1

        if level <= 1:
            return 0

        return level ** 3  # Fórmula Medium Fast: n³

    def add_experience(self, exp_amount):
        original_level = self.level
        self.experience += exp_amount

        leveled_up = False

        while self.level < 100 and self.experience >= self.get_experience_required():
            self.level_up()
            leveled_up = True

        update_fields = {
            'level': self.level,
            'experience': self.experience,
            'hp': self.hp,
            'current_hp': self.current_hp,
            'attack': self.attack,
            'defense': self.defense,
            'special_attack': self.special_attack,
            'special_defense': self.special_defense,
            'speed': self.speed,
            'just_evolved': self.just_evolved
        }

        # Si evolucionó, actualizar también el Pokémon
        if self.just_evolved:
            update_fields['pokemon'] = self.pokemon
            if not self.nickname:
                update_fields['nickname'] = None

        PlayerPokemon.objects.filter(pk=self.pk).update(**update_fields)

        # Resetear flag de evolución si es necesario
        if self.just_evolved:
            self.just_evolved = False
            PlayerPokemon.objects.filter(pk=self.pk).update(just_evolved=False)

        return leveled_up

    def level_up(self):
        """Sube de nivel y maneja evolución"""
        old_level = self.level
        self.level += 1

        print(f"¡{self.pokemon.name} subió al nivel {self.level}!")

        # Guardar HP actual para calcular la curación
        old_hp_percentage = self.current_hp / self.hp if self.hp > 0 else 0

        # Recalcular stats
        self.calculate_stats()

        # Calcular nueva HP manteniendo el porcentaje de salud
        self.current_hp = int(self.hp * old_hp_percentage)
        if self.current_hp <= 0 and self.hp > 0:
            self.current_hp = 1  # Asegurar que no quede en 0

        # Verificar evolución
        self.check_evolution()

        # Si evolucionó, curar completamente
        if self.just_evolved:
            self.current_hp = self.hp
            print(f"¡{self.pokemon.name} evolucionó!")

    def full_heal(self):
        """Cura completamente al Pokémon sin reordenar"""
        self.current_hp = self.hp
        PlayerPokemon.objects.filter(pk=self.pk).update(current_hp=self.hp)

    def check_evolution(self):
        """Verifica si el Pokémon puede evolucionar"""
        # Buscar evolución por nivel
        evolution = Pokemon.objects.filter(
            evolves_from=self.pokemon,
            evolution_level__lte=self.level
        ).first()

        if evolution:
            self.evolve(evolution)

    def evolve(self, new_pokemon):
        """Evoluciona el Pokémon a una nueva especie"""
        old_pokemon_name = self.pokemon.name
        self.pokemon = new_pokemon
        self.just_evolved = True

        # Recalcular stats con la nueva especie
        self.calculate_stats()

        # Curar completamente al evolucionar
        self.current_hp = self.hp

        # Mantener el nickname o usar el nombre de la nueva especie
        if not self.nickname or self.nickname == old_pokemon_name:
            self.nickname = None

    def get_experience_info(self):
        """Obtiene información detallada sobre la experiencia para la barra de progreso"""
        current_exp = self.experience

        # Experiencia requerida para el nivel ACTUAL
        current_level_exp = self.get_experience_required(self.level)
        # Experiencia requerida para el SIGUIENTE nivel
        next_level_exp = self.get_experience_required(self.level + 1)

        # Calcular experiencia en el nivel actual y para el siguiente nivel
        exp_in_current_level = current_exp - current_level_exp
        exp_needed_for_next_level = next_level_exp - current_level_exp
        exp_to_next_level = next_level_exp - current_exp

        # Calcular porcentaje de progreso
        if exp_needed_for_next_level > 0:
            progress_percentage = (exp_in_current_level / exp_needed_for_next_level) * 100
        else:
            progress_percentage = 100

        return {
            'current_level': self.level,
            'current_experience': current_exp,
            'experience_required_previous_level': current_level_exp,
            'experience_required_next_level': next_level_exp,
            'experience_to_next_level': max(0, exp_to_next_level),
            'progress_percentage': min(100, max(0, progress_percentage)),
            'exp_in_current_level': max(0, exp_in_current_level),
            'exp_needed_for_next_level': exp_needed_for_next_level,
            'can_level_up': current_exp >= next_level_exp
        }

    def save(self, *args, **kwargs):
        skip_reorder = kwargs.pop('skip_reorder', False)

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

        if not self.just_evolved and self.pk:
            # Si no acaba de evolucionar, asegurarse de que el flag esté en False
            current_just_evolved = PlayerPokemon.objects.filter(pk=self.pk).values_list('just_evolved',
                                                                                        flat=True).first()
            if current_just_evolved and not self.just_evolved:
                self.just_evolved = False

        super().save(*args, **kwargs)

        if self.in_team and not skip_reorder:
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


