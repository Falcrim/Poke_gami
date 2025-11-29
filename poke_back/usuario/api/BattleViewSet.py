from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
import random
from django.db import transaction
from usuario.models.Battle import Battle
from usuario.models.Player import Player
from usuario.models.PlayerPokemon import PlayerPokemon
from usuario.models.Bag import Bag
from pokemon.models.Pokemon import Pokemon
from pokemon.models.Move import Move
from pokemon.models.PokemonMove import PokemonMove
from pokemon.models.WildPokemonEncounter import WildPokemonEncounter


class BattleSerializer(serializers.ModelSerializer):
    wild_pokemon_name = serializers.CharField(source='wild_pokemon.name', read_only=True)
    wild_pokemon_types = serializers.SerializerMethodField()
    wild_sprite_front = serializers.URLField(source='wild_pokemon.sprite_front', read_only=True)
    player_pokemon_name = serializers.CharField(source='player_pokemon.pokemon.name', read_only=True)
    player_pokemon_types = serializers.SerializerMethodField()
    player_sprite_front = serializers.URLField(source='player_pokemon.pokemon.sprite_front', read_only=True)
    player_sprite_back = serializers.URLField(source='player_pokemon.pokemon.sprite_back', read_only=True)

    class Meta:
        model = Battle
        fields = ('id', 'player', 'wild_pokemon', 'wild_pokemon_name', 'wild_pokemon_types',
                  'wild_sprite_front', 'wild_level', 'wild_current_hp', 'wild_max_hp',
                  'player_pokemon', 'player_pokemon_name', 'player_pokemon_types',
                  'player_sprite_front', 'player_sprite_back', 'state', 'turn')

    def get_wild_pokemon_types(self, obj):
        types = [obj.wild_pokemon.type1]
        if obj.wild_pokemon.type2:
            types.append(obj.wild_pokemon.type2)
        return types

    def get_player_pokemon_types(self, obj):
        types = [obj.player_pokemon.pokemon.type1]
        if obj.player_pokemon.pokemon.type2:
            types.append(obj.player_pokemon.pokemon.type2)
        return types


class BattleViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    # TABLA DE EFECTIVIDAD DE TIPOS (simplificada)
    TYPE_EFFECTIVENESS = {
        'normal': {'rock': 0.5, 'ghost': 0, 'steel': 0.5},
        'fire': {'fire': 0.5, 'water': 0.5, 'grass': 2, 'ice': 2, 'bug': 2, 'rock': 0.5, 'dragon': 0.5, 'steel': 2},
        'water': {'fire': 2, 'water': 0.5, 'grass': 0.5, 'ground': 2, 'rock': 2, 'dragon': 0.5},
        'electric': {'water': 2, 'electric': 0.5, 'grass': 0.5, 'ground': 0, 'flying': 2, 'dragon': 0.5},
        'grass': {'fire': 0.5, 'water': 2, 'grass': 0.5, 'poison': 0.5, 'ground': 2, 'flying': 0.5, 'bug': 0.5,
                  'rock': 2, 'dragon': 0.5, 'steel': 0.5},
        'ice': {'fire': 0.5, 'water': 0.5, 'grass': 2, 'ice': 0.5, 'ground': 2, 'flying': 2, 'dragon': 2, 'steel': 0.5},
        'fighting': {'normal': 2, 'ice': 2, 'poison': 0.5, 'flying': 0.5, 'psychic': 0.5, 'bug': 0.5, 'rock': 2,
                     'ghost': 0, 'dark': 2, 'steel': 2, 'fairy': 0.5},
        'poison': {'grass': 2, 'poison': 0.5, 'ground': 0.5, 'rock': 0.5, 'ghost': 0.5, 'steel': 0, 'fairy': 2},
        'ground': {'fire': 2, 'electric': 2, 'grass': 0.5, 'poison': 2, 'flying': 0, 'bug': 0.5, 'rock': 2, 'steel': 2},
        'flying': {'electric': 0.5, 'grass': 2, 'fighting': 2, 'bug': 2, 'rock': 0.5, 'steel': 0.5},
        'psychic': {'fighting': 2, 'poison': 2, 'psychic': 0.5, 'dark': 0, 'steel': 0.5},
        'bug': {'fire': 0.5, 'grass': 2, 'fighting': 0.5, 'poison': 0.5, 'flying': 0.5, 'psychic': 2, 'ghost': 0.5,
                'dark': 2, 'steel': 0.5, 'fairy': 0.5},
        'rock': {'fire': 2, 'ice': 2, 'fighting': 0.5, 'ground': 0.5, 'flying': 2, 'bug': 2, 'steel': 0.5},
        'ghost': {'normal': 0, 'psychic': 2, 'ghost': 2, 'dark': 0.5},
        'dragon': {'dragon': 2, 'steel': 0.5, 'fairy': 0},
        'dark': {'fighting': 0.5, 'psychic': 2, 'ghost': 2, 'dark': 0.5, 'fairy': 0.5},
        'steel': {'fire': 0.5, 'water': 0.5, 'electric': 0.5, 'ice': 2, 'rock': 2, 'steel': 0.5, 'fairy': 2},
        'fairy': {'fire': 0.5, 'fighting': 2, 'poison': 0.5, 'dragon': 2, 'dark': 2, 'steel': 0.5}
    }

    @action(detail=False, methods=['post'])
    def start_wild_battle(self, request):
        """Iniciar un combate contra un Pokémon salvaje"""
        player = request.user.player_profile

        # CORRECCIÓN: Usar la ubicación actual del jugador automáticamente
        if not player.current_location:
            return Response({'error': 'No estás en ninguna ubicación'}, status=400)

        # CORRECCIÓN: Solo permitir combates en rutas, no en pueblos
        if player.current_location.location_type != 'route':
            return Response({'error': 'Solo puedes encontrar Pokémon salvajes en rutas'}, status=400)

        # CORRECCIÓN: Tomar el primer Pokémon del equipo (orden 0) como activo
        active_pokemon = player.pokemons.filter(in_team=True, current_hp__gt=0).order_by('order').first()
        if not active_pokemon:
            return Response({'error': 'No tienes Pokémon disponibles para combatir'}, status=400)

        # Usar la ubicación actual del jugador automáticamente
        location_id = player.current_location.id

        # Buscar un encuentro salvaje en la ubicación
        try:
            encounter = self.get_wild_encounter(location_id)
            if not encounter:
                return Response({'error': 'No hay Pokémon salvajes en esta ruta'}, status=400)
        except Exception as e:
            return Response({'error': f'Error al buscar Pokémon: {str(e)}'}, status=400)

        # El resto del método permanece igual...
        wild_level = random.randint(encounter.min_level, encounter.max_level)

        # Calcular stats del Pokémon salvaje
        wild_hp = self.calculate_hp(encounter.pokemon.base_hp, wild_level)
        wild_attack = self.calculate_stat(encounter.pokemon.base_attack, wild_level)
        wild_defense = self.calculate_stat(encounter.pokemon.base_defense, wild_level)
        wild_special_attack = self.calculate_stat(encounter.pokemon.base_special_attack, wild_level)
        wild_special_defense = self.calculate_stat(encounter.pokemon.base_special_defense, wild_level)
        wild_speed = self.calculate_stat(encounter.pokemon.base_speed, wild_level)

        # Obtener movimientos del Pokémon salvaje (por nivel)
        wild_moves = PokemonMove.objects.filter(
            pokemon=encounter.pokemon,
            level__lte=wild_level
        ).select_related('move')[:4]

        if not wild_moves:
            return Response({'error': 'El Pokémon salvaje no tiene movimientos'}, status=400)

        # Crear el combate
        with transaction.atomic():
            battle = Battle.objects.create(
                player=player,
                wild_pokemon=encounter.pokemon,
                wild_level=wild_level,
                wild_current_hp=wild_hp,
                wild_max_hp=wild_hp,
                player_pokemon=active_pokemon,
                state='active',
                turn=0  # Empieza el jugador
            )

            # Agregar movimientos del Pokémon salvaje
            for pokemon_move in wild_moves:
                battle.wild_moves.add(pokemon_move.move)

        # Registrar en la Pokédex como visto
        from usuario.models.Pokedex import Pokedex
        Pokedex.objects.get_or_create(
            player=player,
            pokemon=encounter.pokemon,
            defaults={'state': 'seen'}
        )

        return Response({
            'battle_id': battle.id,
            'message': f'¡Un {encounter.pokemon.name} salvaje apareció!',
            'wild_pokemon': {
                'id': encounter.pokemon.id,
                'name': encounter.pokemon.name,
                'level': wild_level,
                'types': [encounter.pokemon.type1, encounter.pokemon.type2] if encounter.pokemon.type2 else [
                    encounter.pokemon.type1],
                'sprite_front': encounter.pokemon.sprite_front,
                'current_hp': wild_hp,
                'max_hp': wild_hp,
                'moves': [{'id': move.move.id, 'name': move.move.name, 'type': move.move.type} for move in wild_moves]
            },
            'player_pokemon': {
                'id': active_pokemon.id,
                'name': active_pokemon.pokemon.name,
                'level': active_pokemon.level,
                'types': [active_pokemon.pokemon.type1,
                          active_pokemon.pokemon.type2] if active_pokemon.pokemon.type2 else [
                    active_pokemon.pokemon.type1],
                'sprite_front': active_pokemon.pokemon.sprite_front,
                'sprite_back': active_pokemon.pokemon.sprite_back,
                'current_hp': active_pokemon.current_hp,
                'max_hp': active_pokemon.hp,
                'moves': [{'id': move.id, 'name': move.name, 'type': move.type, 'power': move.power,
                           'accuracy': move.accuracy, 'pp': move.pp} for move in active_pokemon.moves.all()]
            }
        })

    @action(detail=False, methods=['get'])
    def can_start_battle(self, request):
        """Verificar si el jugador puede iniciar un combate en su ubicación actual"""
        player = request.user.player_profile

        if not player.current_location:
            return Response({
                'can_battle': False,
                'reason': 'No estás en ninguna ubicación'
            })

        if player.current_location.location_type != 'route':
            return Response({
                'can_battle': False,
                'reason': 'Solo puedes combatir en rutas'
            })

        # Verificar que hay Pokémon disponibles en esta ruta
        encounters = WildPokemonEncounter.objects.filter(location=player.current_location)
        if not encounters.exists():
            return Response({
                'can_battle': False,
                'reason': 'No hay Pokémon salvajes en esta ruta'
            })

        # Verificar que el jugador tiene Pokémon vivos
        active_pokemon = player.pokemons.filter(in_team=True, current_hp__gt=0).exists()
        if not active_pokemon:
            return Response({
                'can_battle': False,
                'reason': 'No tienes Pokémon disponibles para combatir'
            })

        return Response({
            'can_battle': True,
            'location': player.current_location.name,
            'location_type': player.current_location.location_type,
            'available_pokemon': encounters.count()
        })

    def get_wild_encounter(self, location_id):
        """Obtener un encuentro salvaje basado en la rareza"""
        encounters = WildPokemonEncounter.objects.filter(location_id=location_id)
        if not encounters:
            return None

        # Sistema de rareza
        rarity_weights = {
            'common': 60,
            'uncommon': 30,
            'rare': 9,
            'very_rare': 1
        }

        weighted_encounters = []
        for encounter in encounters:
            weighted_encounters.extend([encounter] * rarity_weights[encounter.rarity])

        return random.choice(weighted_encounters)

    def calculate_hp(self, base_hp, level):
        """Calcular HP basado en stat base y nivel"""
        return int((2 * base_hp * level) / 100) + level + 10

    def calculate_stat(self, base_stat, level):
        """Calcular stat basado en stat base y nivel"""
        return int((2 * base_stat * level) / 100) + 5

    @action(detail=True, methods=['post'])
    def attack(self, request, pk=None):
        """Atacar con un movimiento"""
        battle = self.get_battle(pk, request.user)
        if not battle or not battle.is_active:
            return Response({'error': 'Combate no encontrado o ya terminado'}, status=404)

        move_id = request.data.get('move_id')
        if not move_id:
            return Response({'error': 'Se requiere move_id'}, status=400)

        # Verificar que el movimiento pertenece al Pokémon del jugador
        try:
            player_move = battle.player_pokemon.moves.get(id=move_id)
        except Move.DoesNotExist:
            return Response({'error': 'Movimiento no válido'}, status=400)

        with transaction.atomic():
            # Turno del jugador
            damage = self.calculate_damage(
                battle.player_pokemon,
                battle.wild_pokemon,
                player_move,
                battle.wild_level
            )
            battle.wild_current_hp -= damage
            battle.wild_current_hp = max(0, battle.wild_current_hp)

            message = f'{battle.player_pokemon.pokemon.name} usó {player_move.name}. '
            if damage > 0:
                message += f'Causó {damage} de daño.'

            # Verificar si el Pokémon salvaje fue derrotado
            if battle.wild_current_hp <= 0:
                battle.state = 'won'
                battle.save()
                return self.handle_battle_win(battle, message)

            # Turno del Pokémon salvaje
            wild_damage, wild_move = self.wild_attack(battle)
            battle.player_pokemon.current_hp -= wild_damage
            battle.player_pokemon.current_hp = max(0, battle.player_pokemon.current_hp)
            battle.player_pokemon.save()

            message += f' {battle.wild_pokemon.name} usó {wild_move.name}. '
            if wild_damage > 0:
                message += f'Causó {wild_damage} de daño.'

            # Verificar si el Pokémon del jugador fue derrotado
            if battle.player_pokemon.current_hp <= 0:
                # Buscar siguiente Pokémon
                next_pokemon = self.get_next_available_pokemon(battle.player)
                if next_pokemon:
                    battle.player_pokemon = next_pokemon
                    battle.save()
                    message += f' {battle.player_pokemon.pokemon.name} fue derrotado. ¡{next_pokemon.pokemon.name} entra al combate!'
                else:
                    battle.state = 'lost'
                    battle.save()
                    return self.handle_battle_loss(battle, message)
            else:
                battle.save()

        return Response({
            'message': message,
            'battle_state': self.get_battle_state(battle)
        })

    def get_battle(self, battle_id, user):
        """Obtener combate activo del jugador"""
        try:
            return Battle.objects.get(id=battle_id, player__user=user, state='active')
        except Battle.DoesNotExist:
            return None

    def calculate_damage(self, attacker, defender, move, defender_level):
        """Calcular daño del movimiento"""
        if move.damage_class == 'status':
            return 0

        # Determinar stat de ataque y defensa
        if move.damage_class == 'physical':
            attack_stat = attacker.attack
            defense_stat = self.calculate_stat(defender.base_defense, defender_level)
        else:  # special
            attack_stat = attacker.special_attack
            defense_stat = self.calculate_stat(defender.base_special_defense, defender_level)

        # Fórmula de daño simplificada
        level_factor = (2 * attacker.level) / 5 + 2
        power_factor = move.power if move.power else 0
        stat_factor = attack_stat / defense_stat

        base_damage = (level_factor * power_factor * stat_factor) / 50 + 2

        # Modificador de tipo
        type_effectiveness = self.get_type_effectiveness(move.type, [defender.type1, defender.type2])
        base_damage *= type_effectiveness

        # Modificador aleatorio (0.85 - 1.0)
        base_damage *= random.uniform(0.85, 1.0)

        return int(max(1, base_damage))

    def get_type_effectiveness(self, move_type, defender_types):
        """Calcular efectividad del tipo"""
        effectiveness = 1.0
        for defender_type in defender_types:
            if defender_type and move_type in self.TYPE_EFFECTIVENESS:
                if defender_type in self.TYPE_EFFECTIVENESS[move_type]:
                    effectiveness *= self.TYPE_EFFECTIVENESS[move_type][defender_type]
        return effectiveness

    def wild_attack(self, battle):
        """El Pokémon salvaje ataca"""
        available_moves = list(battle.wild_moves.all())
        if not available_moves:
            return 0, Move.objects.first()  # Movimiento por defecto

        wild_move = random.choice(available_moves)

        # Calcular stats del Pokémon salvaje
        wild_attack = self.calculate_stat(battle.wild_pokemon.base_attack, battle.wild_level)
        wild_special_attack = self.calculate_stat(battle.wild_pokemon.base_special_attack, battle.wild_level)

        if wild_move.damage_class == 'status':
            damage = 0
        else:
            # Determinar stat de ataque
            if wild_move.damage_class == 'physical':
                attack_stat = wild_attack
                defense_stat = battle.player_pokemon.defense
            else:  # special
                attack_stat = wild_special_attack
                defense_stat = battle.player_pokemon.special_defense

            level_factor = (2 * battle.wild_level) / 5 + 2
            power_factor = wild_move.power if wild_move.power else 0
            stat_factor = attack_stat / defense_stat

            base_damage = (level_factor * power_factor * stat_factor) / 50 + 2

            # Modificador de tipo
            type_effectiveness = self.get_type_effectiveness(
                wild_move.type,
                [battle.player_pokemon.pokemon.type1, battle.player_pokemon.pokemon.type2]
            )
            base_damage *= type_effectiveness

            # Modificador aleatorio
            base_damage *= random.uniform(0.85, 1.0)

            damage = int(max(1, base_damage))

        return damage, wild_move

    def get_next_available_pokemon(self, player):
        return player.pokemons.filter(
            in_team=True,
            current_hp__gt=0
        ).order_by('order').first()

    @action(detail=True, methods=['post'])
    def use_item(self, request, pk=None):
        """Usar un item de la mochila en combate"""
        battle = self.get_battle(pk, request.user)
        if not battle or not battle.is_active:
            return Response({'error': 'Combate no encontrado o ya terminado'}, status=404)

        item_type = request.data.get('item_type')
        if not item_type:
            return Response({'error': 'Se requiere item_type'}, status=400)

        bag = Bag.objects.get(player=battle.player)

        if item_type in ['potion', 'super_potion', 'hyper_potion']:
            return self.use_potion(battle, bag, item_type)
        elif item_type in ['pokeball', 'ultra_ball']:
            return self.use_pokeball(battle, bag, item_type)
        else:
            return Response({'error': 'Item no válido'}, status=400)

    def use_potion(self, battle, bag, potion_type):
        """Usar una poción en combate"""
        heal_amounts = {
            'potion': 20,
            'super_potion': 50,
            'hyper_potion': 200
        }

        # Verificar que hay pociones disponibles
        if getattr(bag, f'{potion_type}s', 0) <= 0:
            return Response({'error': f'No tienes {potion_type}s'}, status=400)

        # Aplicar curación
        heal_amount = heal_amounts[potion_type]
        new_hp = min(battle.player_pokemon.current_hp + heal_amount, battle.player_pokemon.hp)
        actual_heal = new_hp - battle.player_pokemon.current_hp

        with transaction.atomic():
            # Usar poción
            setattr(bag, f'{potion_type}s', getattr(bag, f'{potion_type}s') - 1)
            bag.save()

            battle.player_pokemon.current_hp = new_hp
            battle.player_pokemon.save()

            # Turno del Pokémon salvaje
            wild_damage, wild_move = self.wild_attack(battle)
            battle.player_pokemon.current_hp -= wild_damage
            battle.player_pokemon.current_hp = max(0, battle.player_pokemon.current_hp)
            battle.player_pokemon.save()

            message = f'Usaste una {potion_type}. Curaste {actual_heal} HP. '
            message += f'{battle.wild_pokemon.name} usó {wild_move.name}. Causó {wild_damage} de daño.'

            # Verificar si el Pokémon fue derrotado
            if battle.player_pokemon.current_hp <= 0:
                next_pokemon = self.get_next_available_pokemon(battle.player)
                if next_pokemon:
                    battle.player_pokemon = next_pokemon
                    battle.save()
                    message += f' {battle.player_pokemon.pokemon.name} fue derrotado. ¡{next_pokemon.pokemon.name} entra al combate!'
                else:
                    battle.state = 'lost'
                    battle.save()
                    return self.handle_battle_loss(battle, message)
            else:
                battle.save()

        return Response({
            'message': message,
            'battle_state': self.get_battle_state(battle)
        })

    def use_pokeball(self, battle, bag, ball_type):
        """Intentar capturar al Pokémon salvaje usando fórmula de captura de Pokémon"""
        # Tasas de captura base por tipo de pokéball
        ball_rates = {
            'pokeball': 1.0,
            'ultra_ball': 2.0
        }

        # Verificar que hay pokéballs disponibles
        if getattr(bag, f'{ball_type}s', 0) <= 0:
            return Response({'error': f'No tienes {ball_type}s'}, status=400)

        # FÓRMULA MEJORADA DE CAPTURA (basada en juegos Pokémon)

        # 1. Obtener tasa de captura base del Pokémon
        # En Pokémon reales, cada especie tiene una tasa de captura base
        # Para simplificar, usaremos una tasa base según la rareza del encuentro
        base_catch_rate = 255  # Tasa alta para Pokémon comunes (como en Pokémon Rojo/Azul)

        # 2. Modificador por HP actual (cuanto menos HP, más fácil capturar)
        hp_max = battle.wild_max_hp
        hp_current = battle.wild_current_hp
        hp_factor = (3 * hp_max - 2 * hp_current) * base_catch_rate / (3 * hp_max)

        # 3. Modificador por tipo de pokéball
        ball_modifier = ball_rates[ball_type]

        # 4. Modificador por estado (no implementamos estados, pero podríamos agregar)
        status_modifier = 1.0  # Normal

        # 5. Cálculo final de probabilidad
        catch_rate = (hp_factor * ball_modifier * status_modifier) / 255

        # Asegurar un mínimo de probabilidad
        min_catch_chance = 0.1  # 10% mínimo
        max_catch_chance = 0.9  # 90% máximo
        catch_chance = max(min_catch_chance, min(max_catch_chance, catch_rate))

        # Para debugging: mostrar la probabilidad (puedes quitar esto después)
        print(f"Captura: HP={hp_current}/{hp_max}, Ball={ball_type}, Chance={catch_chance:.2%}")

        with transaction.atomic():
            # Usar pokéball
            setattr(bag, f'{ball_type}s', getattr(bag, f'{ball_type}s') - 1)
            bag.save()

            if random.random() < catch_chance:
                # Captura exitosa
                battle.state = 'won'
                battle.save()
                return self.handle_capture(battle, ball_type)
            else:
                # El Pokémon escapa
                shake_check = random.random() < (catch_chance * 0.5)  # Simular "sacudidas" de la pokéball
                if shake_check:
                    message = f'Usaste una {ball_type}. ¡Casi lo atrapas! El Pokémon escapó del intento.'
                else:
                    message = f'Usaste una {ball_type}. ¡El Pokémon escapó!'

                # Turno del Pokémon salvaje
                wild_damage, wild_move = self.wild_attack(battle)
                battle.player_pokemon.current_hp -= wild_damage
                battle.player_pokemon.current_hp = max(0, battle.player_pokemon.current_hp)
                battle.player_pokemon.save()

                message += f' {battle.wild_pokemon.name} usó {wild_move.name}.'

                if wild_damage > 0:
                    message += f' Causó {wild_damage} de daño.'

                if battle.player_pokemon.current_hp <= 0:
                    next_pokemon = self.get_next_available_pokemon(battle.player)
                    if next_pokemon:
                        battle.player_pokemon = next_pokemon
                        battle.save()
                        message += f' {battle.player_pokemon.pokemon.name} fue derrotado. ¡{next_pokemon.pokemon.name} entra al combate!'
                    else:
                        battle.state = 'lost'
                        battle.save()
                        return self.handle_battle_loss(battle, message)
                else:
                    battle.save()

                return Response({
                    'message': message,
                    'battle_state': self.get_battle_state(battle),
                    'capture_attempt': True,
                    'almost_caught': shake_check
                })

    @action(detail=True, methods=['post'])
    def switch_pokemon(self, request, pk=None):
        """Cambiar de Pokémon durante el combate"""
        battle = self.get_battle(pk, request.user)
        if not battle or not battle.is_active:
            return Response({'error': 'Combate no encontrado o ya terminado'}, status=404)

        pokemon_id = request.data.get('pokemon_id')
        if not pokemon_id:
            return Response({'error': 'Se requiere pokemon_id'}, status=400)

        try:
            new_pokemon = PlayerPokemon.objects.get(
                id=pokemon_id,
                player=battle.player,
                in_team=True,
                current_hp__gt=0
            )
        except PlayerPokemon.DoesNotExist:
            return Response({'error': 'Pokémon no válido'}, status=400)

        with transaction.atomic():
            battle.player_pokemon = new_pokemon
            battle.save()

            # Turno del Pokémon salvaje
            wild_damage, wild_move = self.wild_attack(battle)
            battle.player_pokemon.current_hp -= wild_damage
            battle.player_pokemon.current_hp = max(0, battle.player_pokemon.current_hp)
            battle.player_pokemon.save()

            message = f'Cambiaste a {new_pokemon.pokemon.name}. '
            message += f'{battle.wild_pokemon.name} usó {wild_move.name}. Causó {wild_damage} de daño.'

            if battle.player_pokemon.current_hp <= 0:
                next_pokemon = self.get_next_available_pokemon(battle.player)
                if next_pokemon:
                    battle.player_pokemon = next_pokemon
                    battle.save()
                    message += f' {battle.player_pokemon.pokemon.name} fue derrotado. ¡{next_pokemon.pokemon.name} entra al combate!'
                else:
                    battle.state = 'lost'
                    battle.save()
                    return self.handle_battle_loss(battle, message)
            else:
                battle.save()

        return Response({
            'message': message,
            'battle_state': self.get_battle_state(battle)
        })

    @action(detail=True, methods=['post'])
    def flee(self, request, pk=None):
        """Intentar huir del combate"""
        battle = self.get_battle(pk, request.user)
        if not battle or not battle.is_active:
            return Response({'error': 'Combate no encontrado o ya terminado'}, status=404)

        # Siempre se puede huir de Pokémon salvajes
        battle.state = 'fled'
        battle.save()

        return Response({
            'message': 'Has huido del combate',
            'battle_ended': True,
            'fled': True
        })

    def handle_battle_win(self, battle, message):
        """Manejar victoria en combate"""
        # Otorgar experiencia (simplificado)
        experience_gained = battle.wild_level * 10
        battle.player_pokemon.experience += experience_gained
        battle.player_pokemon.save()

        # Otorgar dinero
        money_gained = battle.wild_level * 5
        battle.player.money += money_gained
        battle.player.save()

        return Response({
            'message': f'{message} ¡Has derrotado al {battle.wild_pokemon.name} salvaje! Ganaste {experience_gained} de experiencia y ${money_gained}.',
            'battle_ended': True,
            'won': True,
            'experience_gained': experience_gained,
            'money_gained': money_gained
        })

    def handle_battle_loss(self, battle, message):
        """Manejar derrota en combate"""
        # Transportar al último pueblo
        last_town = battle.player.current_location
        # Buscar el primer pueblo disponible si no está en uno
        if not last_town or last_town.location_type != 'town':
            from pokemon.models.Location import Location
            last_town = Location.objects.filter(location_type='town').first()

        battle.player.current_location = last_town
        battle.player.save()

        # Curar todos los Pokémon
        for pokemon in battle.player.pokemons.all():
            pokemon.current_hp = pokemon.hp
            pokemon.save()

        return Response({
            'message': f'{message} Todos tus Pokémon fueron derrotados. Has sido transportado a {last_town.name} y tus Pokémon han sido curados.',
            'battle_ended': True,
            'lost': True,
            'new_location': last_town.name
        })

    def handle_capture(self, battle, ball_type):
        """Manejar captura exitosa"""
        # Crear nuevo Pokémon para el jugador
        new_pokemon = PlayerPokemon.objects.create(
            player=battle.player,
            pokemon=battle.wild_pokemon,
            level=battle.wild_level,
            experience=0,
            in_team=False  # Va a la reserva
        )
        new_pokemon.calculate_stats()
        new_pokemon.current_hp = new_pokemon.hp
        new_pokemon.save()

        # Aprender movimientos iniciales
        wild_moves = PokemonMove.objects.filter(
            pokemon=battle.wild_pokemon,
            level__lte=battle.wild_level
        )[:2]
        for move in wild_moves:
            new_pokemon.moves.add(move.move)

        # Registrar en la Pokédex
        from usuario.models.Pokedex import Pokedex
        Pokedex.objects.get_or_create(
            player=battle.player,
            pokemon=battle.wild_pokemon,
            defaults={'state': 'caught'}
        )

        return Response({
            'message': f'¡Has capturado a {battle.wild_pokemon.name} con una {ball_type}!',
            'battle_ended': True,
            'captured': True,
            'new_pokemon_id': new_pokemon.id
        })

    def get_battle_state(self, battle):
        """Obtener estado actual del combate"""
        return {
            'battle_id': battle.id,
            'player_pokemon': {
                'id': battle.player_pokemon.id,
                'name': battle.player_pokemon.pokemon.name,
                'current_hp': battle.player_pokemon.current_hp,
                'max_hp': battle.player_pokemon.hp,
                'moves': [{'id': move.id, 'name': move.name, 'type': move.type} for move in
                          battle.player_pokemon.moves.all()]
            },
            'wild_pokemon': {
                'id': battle.wild_pokemon.id,
                'name': battle.wild_pokemon.name,
                'current_hp': battle.wild_current_hp,
                'max_hp': battle.wild_max_hp
            },
            'state': battle.state
        }
