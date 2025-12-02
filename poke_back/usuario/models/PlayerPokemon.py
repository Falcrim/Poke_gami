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

    in_team = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    moves = models.ManyToManyField(Move, related_name='player_pokemons')

    hp = models.IntegerField(default=0)
    attack = models.IntegerField(default=0)
    defense = models.IntegerField(default=0)
    special_attack = models.IntegerField(default=0)
    special_defense = models.IntegerField(default=0)
    speed = models.IntegerField(default=0)
    moves_pp = models.JSONField(default=dict, blank=True)
    just_evolved = models.BooleanField(default=False)

    class Meta:
        db_table = 'player_pokemons'

    def __str__(self):
        if self.nickname:
            return f"{self.nickname} ({self.pokemon.name}) Lv.{self.level}"
        return f"{self.pokemon.name} Lv.{self.level}"

    def clean(self):
        if self.in_team and self.player.pokemons.filter(in_team=True).count() >= 6:
            if not self.pk:
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

        if self.just_evolved:
            update_fields['pokemon'] = self.pokemon
            if not self.nickname:
                update_fields['nickname'] = None

        PlayerPokemon.objects.filter(pk=self.pk).update(**update_fields)

        if self.just_evolved:
            self.just_evolved = False
            PlayerPokemon.objects.filter(pk=self.pk).update(just_evolved=False)

        return leveled_up

    def level_up(self):
        old_level = self.level
        self.level += 1

        print(f"¡{self.pokemon.name} subió al nivel {self.level}!")

        old_hp_percentage = self.current_hp / self.hp if self.hp > 0 else 0

        self.calculate_stats()

        self.current_hp = int(self.hp * old_hp_percentage)
        if self.current_hp <= 0 and self.hp > 0:
            self.current_hp = 1

        self.check_evolution()

        if self.just_evolved:
            self.current_hp = self.hp
            print(f"¡{self.pokemon.name} evolucionó!")

            from usuario.models.Pokedex import Pokedex
            Pokedex.objects.get_or_create(
                player=self.player,
                pokemon=self.pokemon,
                defaults={'state': 'caught'}
            )

    def full_heal(self):
        self.current_hp = self.hp
        PlayerPokemon.objects.filter(pk=self.pk).update(current_hp=self.hp)

    def check_evolution(self):
        evolution = Pokemon.objects.filter(
            evolves_from=self.pokemon,
            evolution_level__lte=self.level
        ).first()

        if evolution:
            self.evolve(evolution)

    def evolve(self, new_pokemon):
        old_pokemon_name = self.pokemon.name
        self.pokemon = new_pokemon
        self.just_evolved = True

        self.calculate_stats()

        self.current_hp = self.hp

        if not self.nickname or self.nickname == old_pokemon_name:
            self.nickname = None

        if not self.moves_pp:
            self.moves_pp = {}

        for move in self.moves.all():
            move_id_str = str(move.id)
            if move_id_str not in self.moves_pp:
                self.moves_pp[move_id_str] = move.pp

        from usuario.models.Pokedex import Pokedex
        pokedex_entry, created = Pokedex.objects.get_or_create(
            player=self.player,
            pokemon=new_pokemon,
            defaults={'state': 'caught'}
        )

        if not created and pokedex_entry.state != 'caught':
            pokedex_entry.state = 'caught'
            pokedex_entry.save()

    def get_experience_info(self):
        current_exp = self.experience

        current_level_exp = self.get_experience_required(self.level)
        next_level_exp = self.get_experience_required(self.level + 1)

        exp_in_current_level = current_exp - current_level_exp
        exp_needed_for_next_level = next_level_exp - current_level_exp
        exp_to_next_level = next_level_exp - current_exp

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
            current_just_evolved = PlayerPokemon.objects.filter(pk=self.pk).values_list('just_evolved',
                                                                                        flat=True).first()
            if current_just_evolved and not self.just_evolved:
                self.just_evolved = False

        super().save(*args, **kwargs)

        if not self.moves_pp:
            self.moves_pp = {}

        for move in self.moves.all():
            move_id_str = str(move.id)
            if move_id_str not in self.moves_pp:
                self.moves_pp[move_id_str] = move.pp

        if self.pk:
            current_move_ids = set(str(move.id) for move in self.moves.all())

            keys_to_remove = []
            for move_id_str in self.moves_pp.keys():
                if move_id_str not in current_move_ids:
                    keys_to_remove.append(move_id_str)

            for key in keys_to_remove:
                del self.moves_pp[key]

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
        if not self.pk:
            return True
        try:
            old = PlayerPokemon.objects.get(pk=self.pk)
            return old.level != self.level
        except PlayerPokemon.DoesNotExist:
            return True

    def get_available_moves(self):
        from pokemon.models.PokemonMove import PokemonMove
        return PokemonMove.objects.filter(
            pokemon=self.pokemon,
            level__lte=self.level
        ).select_related('move')

    def can_learn_move(self, move):
        return self.get_available_moves().filter(move=move).exists()

    def teach_move(self, move):
        if not self.can_learn_move(move):
            raise ValidationError(f"{self.pokemon.name} no puede aprender {move.name}")

        if self.moves.count() >= 4:
            raise ValidationError(f"{self.pokemon.name} ya tiene 4 movimientos")

        if self.moves.filter(id=move.id).exists():
            raise ValidationError(f"{self.pokemon.name} ya conoce {move.name}")

        self.moves.add(move)

        if not self.moves_pp:
            self.moves_pp = {}

        self.moves_pp[str(move.id)] = move.pp
        self.save(update_fields=['moves_pp'])

        return True

    def forget_move(self, move):
        if not self.moves.filter(id=move.id).exists():
            raise ValidationError(f"{self.pokemon.name} no conoce {move.name}")

        if self.moves.count() <= 1:
            raise ValidationError(f"{self.pokemon.name} debe tener al menos 1 movimiento")

        self.moves.remove(move)

        if self.moves_pp and str(move.id) in self.moves_pp:
            del self.moves_pp[str(move.id)]
            self.save(update_fields=['moves_pp'])

        return True

    def replace_move(self, old_move, new_move):
        self.forget_move(old_move)

        self.teach_move(new_move)

        return True
