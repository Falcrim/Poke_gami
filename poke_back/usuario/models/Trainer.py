from django.db import models
from pokemon.models.Pokemon import Pokemon
from pokemon.models.Location import Location


class Trainer(models.Model):
    TRAINER_TYPES = (
        ('beginner', 'Principiante'),
        ('intermediate', 'Intermedio'),
        ('advanced', 'Avanzado'),
        ('gym_leader', 'Líder de Gimnasio'),
        ('elite_four', 'Alto Mando'),
        ('champion', 'Campeón'),
    )

    name = models.CharField(max_length=50)
    trainer_type = models.CharField(max_length=20, choices=TRAINER_TYPES)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='trainers')
    sprite = models.URLField(blank=True, null=True)
    dialogue_before = models.TextField(blank=True, null=True)
    dialogue_after = models.TextField(blank=True, null=True)
    money_reward = models.IntegerField(default=100)
    min_level = models.IntegerField(default=1)
    max_level = models.IntegerField(default=10)
    team_size = models.IntegerField(default=1)

    class Meta:
        db_table = 'trainers'

    def __str__(self):
        return f"{self.name} ({self.get_trainer_type_display()})"

    def generate_team(self):
        """Genera un equipo de Pokémon basado en los Pokémon salvajes de la ubicación"""
        from pokemon.models.WildPokemonEncounter import WildPokemonEncounter

        # Obtener todos los encuentros salvajes de esta ubicación
        encounters = WildPokemonEncounter.objects.filter(location=self.location)

        if not encounters:
            return []

        team = []
        for _ in range(self.team_size):
            # Seleccionar un Pokémon basado en la rareza
            encounter = self._weighted_random_encounter(encounters)

            # Determinar nivel (puede ser aleatorio o basado en el tipo de entrenador)
            level = self._calculate_trainer_level()

            # Calcular stats
            hp = self._calculate_hp(encounter.pokemon.base_hp, level)
            attack = self._calculate_stat(encounter.pokemon.base_attack, level)
            defense = self._calculate_stat(encounter.pokemon.base_defense, level)
            special_attack = self._calculate_stat(encounter.pokemon.base_special_attack, level)
            special_defense = self._calculate_stat(encounter.pokemon.base_special_defense, level)
            speed = self._calculate_stat(encounter.pokemon.base_speed, level)

            # Obtener movimientos (hasta 4)
            from pokemon.models.PokemonMove import PokemonMove
            available_moves = PokemonMove.objects.filter(
                pokemon=encounter.pokemon,
                level__lte=level
            ).order_by('-level')[:4]

            moves = [pm.move for pm in available_moves]

            team.append({
                'pokemon': encounter.pokemon,
                'level': level,
                'current_hp': hp,
                'max_hp': hp,
                'attack': attack,
                'defense': defense,
                'special_attack': special_attack,
                'special_defense': special_defense,
                'speed': speed,
                'moves': moves,
                'type1': encounter.pokemon.type1,
                'type2': encounter.pokemon.type2,
            })

        return team

    def _weighted_random_encounter(self, encounters):
        """Selecciona un encuentro basado en la rareza"""
        import random

        rarity_weights = {
            'common': 60,
            'uncommon': 30,
            'rare': 9,
            'very_rare': 1
        }

        weighted_encounters = []
        for encounter in encounters:
            weighted_encounters.extend([encounter] * rarity_weights.get(encounter.rarity, 1))

        return random.choice(weighted_encounters)

    def _calculate_trainer_level(self):
        """Calcula el nivel basado en el tipo de entrenador"""
        import random

        level_modifiers = {
            'beginner': (0.7, 0.9),
            'intermediate': (0.9, 1.1),
            'advanced': (1.1, 1.3),
            'gym_leader': (1.3, 1.5),
            'elite_four': (1.5, 1.8),
            'champion': (1.8, 2.2),
        }

        modifier_range = level_modifiers.get(self.trainer_type, (0.8, 1.0))
        base_level = random.randint(self.min_level, self.max_level)
        modifier = random.uniform(*modifier_range)

        return max(1, min(100, int(base_level * modifier)))

    def _calculate_hp(self, base_hp, level):
        return int((2 * base_hp * level) / 100) + level + 10

    def _calculate_stat(self, base_stat, level):
        return int((2 * base_stat * level) / 100) + 5