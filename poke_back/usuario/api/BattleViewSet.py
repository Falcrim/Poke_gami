from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
import random
from django.db import models
from django.db import transaction
from usuario.models.Battle import Battle
from usuario.models.Player import Player
from usuario.models.PlayerPokemon import PlayerPokemon
from usuario.models.Bag import Bag
from pokemon.models.Pokemon import Pokemon
from pokemon.models.Move import Move
from pokemon.models.PokemonMove import PokemonMove
from pokemon.models.WildPokemonEncounter import WildPokemonEncounter
import json
import random


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
        player = request.user.player_profile

        if not player.current_location:
            return Response({'error': 'No estás en ninguna ubicación'}, status=400)
        if player.current_location.location_type != 'route':
            return Response({'error': 'Solo puedes encontrar Pokémon salvajes en rutas'}, status=400)

        active_pokemon = player.pokemons.filter(in_team=True, current_hp__gt=0).order_by('order').first()
        if not active_pokemon:
            return Response({'error': 'No tienes Pokémon disponibles para combatir'}, status=400)

        location_id = player.current_location.id

        try:
            encounter = self.get_wild_encounter(location_id)
            if not encounter:
                return Response({'error': 'No hay Pokémon salvajes en esta ruta'}, status=400)
        except Exception as e:
            return Response({'error': f'Error al buscar Pokémon: {str(e)}'}, status=400)

        wild_level = random.randint(encounter.min_level, encounter.max_level)
        wild_hp = self.calculate_hp(encounter.pokemon.base_hp, wild_level)
        wild_attack = self.calculate_stat(encounter.pokemon.base_attack, wild_level)
        wild_defense = self.calculate_stat(encounter.pokemon.base_defense, wild_level)
        wild_special_attack = self.calculate_stat(encounter.pokemon.base_special_attack, wild_level)
        wild_special_defense = self.calculate_stat(encounter.pokemon.base_special_defense, wild_level)
        wild_speed = self.calculate_stat(encounter.pokemon.base_speed, wild_level)

        wild_moves = PokemonMove.objects.filter(
            pokemon=encounter.pokemon,
            level__lte=wild_level
        ).select_related('move')[:4]

        if not wild_moves:
            return Response({'error': 'El Pokémon salvaje no tiene movimientos'}, status=400)

        with transaction.atomic():
            battle = Battle.objects.create(
                player=player,
                wild_pokemon=encounter.pokemon,
                wild_level=wild_level,
                wild_current_hp=wild_hp,
                wild_max_hp=wild_hp,
                player_pokemon=active_pokemon,
                state='active',
                turn=0
            )

            for pokemon_move in wild_moves:
                battle.wild_moves.add(pokemon_move.move)

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

    @action(detail=False, methods=['post'])
    def start_trainer_battle(self, request):
        player = request.user.player_profile

        if not player.current_location:
            return Response({'error': 'No estás en ninguna ubicación'}, status=400)

        if player.current_location.location_type != 'route':
            return Response({'error': 'Solo puedes combatir con entrenadores en rutas'}, status=400)

        active_pokemon = player.pokemons.filter(in_team=True, current_hp__gt=0).order_by('order').first()
        if not active_pokemon:
            return Response({'error': 'No tienes Pokémon disponibles para combatir'}, status=400)

        trainer_data = self.generate_random_trainer(player.current_location)

        if not trainer_data:
            return Response({'error': 'No se pudo generar un entrenador para esta zona'}, status=400)

        with transaction.atomic():
            battle = Battle.objects.create(
                battle_type='trainer',
                player=player,
                trainer_name=trainer_data['name'],
                trainer_sprite=trainer_data['sprite'],
                trainer_dialogue=trainer_data['dialogue'],
                trainer_money_reward=trainer_data['money_reward'],
                trainer_team=trainer_data['team'],
                current_trainer_pokemon=0,
                player_pokemon=active_pokemon,
                state='active',
                turn=0
            )

        first_pokemon = trainer_data['team'][0] if trainer_data['team'] else None

        return Response({
            'battle_id': battle.id,
            'message': trainer_data['dialogue'],
            'trainer': {
                'name': trainer_data['name'],
                'sprite': trainer_data['sprite'],
                'team_size': len(trainer_data['team']),
                'money_reward': trainer_data['money_reward']
            },
            'opponent_pokemon': first_pokemon,
            'player_pokemon': {
                'id': active_pokemon.id,
                'name': active_pokemon.pokemon.name,
                'level': active_pokemon.level,
                'current_hp': active_pokemon.current_hp,
                'max_hp': active_pokemon.hp,
                'sprite_front': active_pokemon.pokemon.sprite_front,
                'sprite_back': active_pokemon.pokemon.sprite_back,
                'moves': [{'id': move.id, 'name': move.name, 'type': move.type, 'power': move.power,
                           'accuracy': move.accuracy, 'pp': move.pp} for move in active_pokemon.moves.all()]
            }
        })

    @action(detail=False, methods=['get'])
    def can_start_battle(self, request):
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

        encounters = WildPokemonEncounter.objects.filter(location=player.current_location)
        if not encounters.exists():
            return Response({
                'can_battle': False,
                'reason': 'No hay Pokémon salvajes en esta ruta'
            })

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
        return int((2 * base_hp * level) / 100) + level + 10

    def calculate_stat(self, base_stat, level):
        return int((2 * base_stat * level) / 100) + 5

    @action(detail=True, methods=['post'])
    def attack(self, request, pk=None):
        battle = self.get_battle(pk, request.user)
        if not battle or not battle.is_active:
            return Response({'error': 'Combate no encontrado o ya terminado'}, status=404)

        move_id = request.data.get('move_id')
        if not move_id:
            return Response({'error': 'Se requiere move_id'}, status=400)

        try:
            player_move = battle.player_pokemon.moves.get(id=move_id)
        except Move.DoesNotExist:
            return Response({'error': 'Movimiento no válido'}, status=400)

        current_pp = self.get_move_current_pp(battle.player_pokemon, move_id)
        if current_pp <= 0:
            return Response({'error': f'No hay PP restantes para {player_move.name}'}, status=400)

        with transaction.atomic():
            message = ""

            if battle.battle_type == 'wild':
                damage = self.calculate_damage(
                    battle.player_pokemon,
                    battle.wild_pokemon,
                    player_move,
                    battle.wild_level
                )
                battle.wild_current_hp -= damage
                battle.wild_current_hp = max(0, battle.wild_current_hp)

                remaining_pp = self.reduce_move_pp(battle.player_pokemon, move_id)

                message = f'{battle.player_pokemon.pokemon.name} usó {player_move.name}. '
                if damage > 0:
                    message += f'Causó {damage} de daño.'
                    message += f'(PP: {remaining_pp}/{player_move.pp})'

                if battle.wild_current_hp <= 0:
                    battle.state = 'won'
                    battle.save()
                    return self.handle_battle_win(battle, message)

            if battle.battle_type == 'trainer' :  # battle_type == 'trainer'
                current_opponent = battle.current_opponent_pokemon
                if not current_opponent:
                    return Response({'error': 'No hay Pokémon oponente activo'}, status=400)

                damage = self.calculate_damage_trainer(
                    battle.player_pokemon,
                    current_opponent,
                    player_move
                )

                battle.trainer_team[battle.current_trainer_pokemon]['current_hp'] -= damage
                battle.trainer_team[battle.current_trainer_pokemon]['current_hp'] = max(
                    0, battle.trainer_team[battle.current_trainer_pokemon]['current_hp']
                )

                remaining_pp = self.reduce_move_pp(battle.player_pokemon, move_id)

                message = f'{battle.player_pokemon.pokemon.name} usó {player_move.name}. '
                message += f'Causó {damage} de daño. (PP restantes: {remaining_pp}/{player_move.pp})'
                if damage > 0:
                    message += f'Causó {damage} de daño.'

                if battle.trainer_team[battle.current_trainer_pokemon]['current_hp'] <= 0:
                    opponent_name = battle.trainer_team[battle.current_trainer_pokemon]['pokemon_name']
                    message += f' ¡{opponent_name} fue derrotado!'

                    if battle.is_trainer_defeated():
                        battle.state = 'won'
                        battle.save()
                        return self.handle_trainer_battle_win(battle, message)
                    else:
                        next_index = self.get_next_trainer_pokemon(battle)
                        if next_index is not None:
                            battle.current_trainer_pokemon = next_index
                            next_pokemon = battle.trainer_team[next_index]
                            message += f' {battle.trainer_name} envía a {next_pokemon["pokemon_name"]}.'
                        else:
                            battle.state = 'won'
                            battle.save()
                            return self.handle_trainer_battle_win(battle, message)

                battle.save()

            if battle.battle_type == 'wild':
                wild_damage, wild_move = self.wild_attack(battle)
                battle.player_pokemon.current_hp -= wild_damage
                battle.player_pokemon.current_hp = max(0, battle.player_pokemon.current_hp)

                PlayerPokemon.objects.filter(pk=battle.player_pokemon.pk).update(
                    current_hp=battle.player_pokemon.current_hp
                )

                message += f' {battle.wild_pokemon.name} usó {wild_move.name}. '
                if wild_damage > 0:
                    message += f'Causó {wild_damage} de daño.'

            if battle.battle_type == 'trainer':  # battle_type == 'trainer'
                current_opponent = battle.current_opponent_pokemon
                if current_opponent and current_opponent['current_hp'] > 0:
                    trainer_damage, trainer_move = self.trainer_attack(battle)
                    battle.player_pokemon.current_hp -= trainer_damage
                    battle.player_pokemon.current_hp = max(0, battle.player_pokemon.current_hp)

                    PlayerPokemon.objects.filter(pk=battle.player_pokemon.pk).update(
                        current_hp=battle.player_pokemon.current_hp
                    )

                    opponent_name = battle.trainer_team[battle.current_trainer_pokemon]['pokemon_name']
                    message += f' {opponent_name} usó {trainer_move["name"]}. '
                    if trainer_damage > 0:
                        message += f'Causó {trainer_damage} de daño.'

            if battle.player_pokemon.current_hp <= 0:
                defeated_pokemon_name = battle.player_pokemon.pokemon.name

                next_pokemon = self.get_next_available_pokemon(battle.player)
                if next_pokemon:
                    battle.player_pokemon = next_pokemon
                    battle.save()
                    message += f' {defeated_pokemon_name} fue derrotado. ¡{next_pokemon.pokemon.name} entra al combate!'
                else:
                    battle.state = 'lost'
                    battle.save()
                    if battle.battle_type == 'wild':
                        return self.handle_battle_loss(battle, message)
                    else:
                        return self.handle_trainer_battle_loss(battle, message)
            else:
                battle.save()

            return Response({
                'message': message,
                'battle_state': self.get_battle_state(battle)
            })

    def reduce_move_pp(self, player_pokemon, move_id):
        from usuario.models.PlayerPokemon import PlayerPokemon

        move_id_str = str(move_id)
        if not player_pokemon.moves_pp:
            player_pokemon.moves_pp = {}

        try:
            move = Move.objects.get(id=move_id)
            max_pp = move.pp
        except Move.DoesNotExist:
            max_pp = 0

        if move_id_str not in player_pokemon.moves_pp:
            player_pokemon.moves_pp[move_id_str] = max_pp

        current_pp = player_pokemon.moves_pp[move_id_str]
        if current_pp > 0:
            player_pokemon.moves_pp[move_id_str] = current_pp - 1

        PlayerPokemon.objects.filter(pk=player_pokemon.pk).update(
            moves_pp=player_pokemon.moves_pp
        )

        return player_pokemon.moves_pp[move_id_str]

    def get_move_current_pp(self, player_pokemon, move_id):
        move_id_str = str(move_id)

        if not player_pokemon.moves_pp:
            try:
                move = Move.objects.get(id=move_id)
                return move.pp
            except Move.DoesNotExist:
                return 0

        if move_id_str in player_pokemon.moves_pp:
            return player_pokemon.moves_pp[move_id_str]
        else:
            try:
                move = Move.objects.get(id=move_id)
                return move.pp
            except Move.DoesNotExist:
                return 0

    def get_battle(self, battle_id, user):
        try:
            return Battle.objects.get(id=battle_id, player__user=user, state='active')
        except Battle.DoesNotExist:
            return None

    def calculate_damage(self, attacker, defender, move, defender_level):
        if move.damage_class == 'status':
            return 0

        if move.damage_class == 'physical':
            attack_stat = attacker.attack
            defense_stat = self.calculate_stat(defender.base_defense, defender_level)
        else:
            attack_stat = attacker.special_attack
            defense_stat = self.calculate_stat(defender.base_special_defense, defender_level)

        level_factor = (2 * attacker.level) / 5 + 2
        power_factor = move.power if move.power else 0
        stat_factor = attack_stat / defense_stat

        base_damage = (level_factor * power_factor * stat_factor) / 50 + 2

        type_effectiveness = self.get_type_effectiveness(move.type, [defender.type1, defender.type2])
        base_damage *= type_effectiveness

        base_damage *= random.uniform(0.85, 1.0)

        return int(max(1, base_damage))

    def get_type_effectiveness(self, move_type, defender_types):
        effectiveness = 1.0
        for defender_type in defender_types:
            if defender_type and move_type in self.TYPE_EFFECTIVENESS:
                if defender_type in self.TYPE_EFFECTIVENESS[move_type]:
                    effectiveness *= self.TYPE_EFFECTIVENESS[move_type][defender_type]
        return effectiveness

    def wild_attack(self, battle):
        available_moves = list(battle.wild_moves.all())
        if not available_moves:
            return 0, Move.objects.first()

        wild_move = random.choice(available_moves)

        wild_attack = self.calculate_stat(battle.wild_pokemon.base_attack, battle.wild_level)
        wild_special_attack = self.calculate_stat(battle.wild_pokemon.base_special_attack, battle.wild_level)

        if wild_move.damage_class == 'status':
            damage = 0
        else:
            if wild_move.damage_class == 'physical':
                attack_stat = wild_attack
                defense_stat = battle.player_pokemon.defense
            else:
                attack_stat = wild_special_attack
                defense_stat = battle.player_pokemon.special_defense

            level_factor = (2 * battle.wild_level) / 5 + 2
            power_factor = wild_move.power if wild_move.power else 0
            stat_factor = attack_stat / defense_stat

            base_damage = (level_factor * power_factor * stat_factor) / 50 + 2

            type_effectiveness = self.get_type_effectiveness(
                wild_move.type,
                [battle.player_pokemon.pokemon.type1, battle.player_pokemon.pokemon.type2]
            )
            base_damage *= type_effectiveness

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
        heal_amounts = {
            'potion': 20,
            'super_potion': 50,
            'hyper_potion': 200
        }

        if getattr(bag, f'{potion_type}s', 0) <= 0:
            return Response({'error': f'No tienes {potion_type}s'}, status=400)

        heal_amount = heal_amounts[potion_type]
        new_hp = min(battle.player_pokemon.current_hp + heal_amount, battle.player_pokemon.hp)
        actual_heal = new_hp - battle.player_pokemon.current_hp

        with transaction.atomic():
            setattr(bag, f'{potion_type}s', getattr(bag, f'{potion_type}s') - 1)
            bag.save()

            PlayerPokemon.objects.filter(pk=battle.player_pokemon.pk).update(
                current_hp=new_hp
            )

            if battle.battle_type == 'wild':
                wild_damage, wild_move = self.wild_attack(battle)
                battle.player_pokemon.current_hp = new_hp - wild_damage
                battle.player_pokemon.current_hp = max(0, battle.player_pokemon.current_hp)

                PlayerPokemon.objects.filter(pk=battle.player_pokemon.pk).update(
                    current_hp=battle.player_pokemon.current_hp
                )

                message = f'Usaste una {potion_type}. Curaste {actual_heal} HP. '
                message += f'{battle.wild_pokemon.name} usó {wild_move.name}. Causó {wild_damage} de daño.'
            if battle.battle_type == 'trainer':
                trainer_damage, trainer_move = self.trainer_attack(battle)
                battle.player_pokemon.current_hp = new_hp - trainer_damage
                battle.player_pokemon.current_hp = max(0, battle.player_pokemon.current_hp)

                PlayerPokemon.objects.filter(pk=battle.player_pokemon.pk).update(
                    current_hp=battle.player_pokemon.current_hp
                )

                current_opponent = battle.current_opponent_pokemon
                opponent_name = current_opponent['pokemon_name'] if current_opponent else 'el oponente'

                message = f'Usaste una {potion_type}. Curaste {actual_heal} HP. '
                message += f'{opponent_name} usó {trainer_move["name"]}. Causó {trainer_damage} de daño.'

            if battle.player_pokemon.current_hp <= 0:
                defeated_pokemon_name = battle.player_pokemon.pokemon.name

                next_pokemon = self.get_next_available_pokemon(battle.player)
                if next_pokemon:
                    battle.player_pokemon = next_pokemon
                    battle.save()
                    message += f' {defeated_pokemon_name} fue derrotado. ¡{next_pokemon.pokemon.name} entra al combate!'
                else:
                    battle.state = 'lost'
                    battle.save()
                    if battle.battle_type == 'wild':
                        return self.handle_battle_loss(battle, message)
                    else:
                        return self.handle_trainer_battle_loss(battle, message)
            else:
                battle.save()

            return Response({
                'message': message,
                'battle_state': self.get_battle_state(battle)
            })

    def use_pokeball(self, battle, bag, ball_type):
        ball_rates = {
            'pokeball': 1.0,
            'ultra_ball': 2.0
        }

        if getattr(bag, f'{ball_type}s', 0) <= 0:
            return Response({'error': f'No tienes {ball_type}s'}, status=400)

        if battle.battle_type != 'wild':
            return Response({'error': 'No puedes capturar Pokémon de entrenadores'}, status=400)

        base_catch_rate = 255

        hp_max = battle.wild_max_hp
        hp_current = battle.wild_current_hp
        hp_factor = (3 * hp_max - 2 * hp_current) * base_catch_rate / (3 * hp_max)

        ball_modifier = ball_rates[ball_type]

        status_modifier = 1.0  # Normal

        catch_rate = (hp_factor * ball_modifier * status_modifier) / 255

        min_catch_chance = 0.1
        max_catch_chance = 0.9
        catch_chance = max(min_catch_chance, min(max_catch_chance, catch_rate))

        print(f"Captura: HP={hp_current}/{hp_max}, Ball={ball_type}, Chance={catch_chance:.2%}")

        with transaction.atomic():
            setattr(bag, f'{ball_type}s', getattr(bag, f'{ball_type}s') - 1)
            bag.save()

            if random.random() < catch_chance:
                battle.state = 'won'
                battle.save()
                return self.handle_capture(battle, ball_type)
            else:
                shake_check = random.random() < (catch_chance * 0.5)  # Simular "sacudidas" de la pokéball
                if shake_check:
                    message = f'Usaste una {ball_type}. ¡Casi lo atrapas! El Pokémon escapó del intento.'
                else:
                    message = f'Usaste una {ball_type}. ¡El Pokémon escapó!'

                wild_damage, wild_move = self.wild_attack(battle)
                battle.player_pokemon.current_hp -= wild_damage
                battle.player_pokemon.current_hp = max(0, battle.player_pokemon.current_hp)

                PlayerPokemon.objects.filter(pk=battle.player_pokemon.pk).update(
                    current_hp=battle.player_pokemon.current_hp
                )

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

            if battle.battle_type == 'wild':
                wild_damage, wild_move = self.wild_attack(battle)
                new_pokemon.current_hp -= wild_damage
                new_pokemon.current_hp = max(0, new_pokemon.current_hp)

                PlayerPokemon.objects.filter(pk=new_pokemon.pk).update(
                    current_hp=new_pokemon.current_hp
                )

                message = f'Cambiaste a {new_pokemon.pokemon.name}. '
                message += f'{battle.wild_pokemon.name} usó {wild_move.name}. Causó {wild_damage} de daño.'
            if battle.battle_type == 'trainer':
                trainer_damage, trainer_move = self.trainer_attack(battle)
                new_pokemon.current_hp -= trainer_damage
                new_pokemon.current_hp = max(0, new_pokemon.current_hp)

                PlayerPokemon.objects.filter(pk=new_pokemon.pk).update(
                    current_hp=new_pokemon.current_hp
                )

                current_opponent = battle.current_opponent_pokemon
                opponent_name = current_opponent['pokemon_name'] if current_opponent else 'el oponente'
                message = f'Cambiaste a {new_pokemon.pokemon.name}. '
                message += f'{opponent_name} usó {trainer_move["name"]}. Causó {trainer_damage} de daño.'

            if new_pokemon.current_hp <= 0:
                next_pokemon = self.get_next_available_pokemon(battle.player)
                if next_pokemon:
                    battle.player_pokemon = next_pokemon
                    battle.save()
                    message += f' {battle.player_pokemon.pokemon.name} fue derrotado. ¡{next_pokemon.pokemon.name} entra al combate!'
                else:
                    battle.state = 'lost'
                    battle.save()
                    if battle.battle_type == 'wild':
                        return self.handle_battle_loss(battle, message)
                    else:
                        return self.handle_trainer_battle_loss(battle, message)
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
        # Para entrenadores, podría haber penalización o no permitirse
        if battle.battle_type == 'trainer':
            # Podrías decidir no permitir huir de entrenadores
            # battle.state = 'fled'
            # battle.save()
            # return Response({
            #     'message': 'Has huido del combate contra el entrenador',
            #     'battle_ended': True,
            #     'fled': True
            # })
            return Response({'error': 'No puedes huir de un combate contra entrenador'}, status=400)

        battle.state = 'fled'
        battle.save()

        return Response({
            'message': 'Has huido del combate',
            'battle_ended': True,
            'fled': True
        })

    def handle_battle_win(self, battle, message):
        experience_gained = battle.wild_level * 10

        original_level = battle.player_pokemon.level
        original_pokemon_name = battle.player_pokemon.pokemon.name

        from usuario.models.PlayerPokemon import PlayerPokemon
        player_pokemon = PlayerPokemon.objects.get(pk=battle.player_pokemon.pk)

        leveled_up = player_pokemon.add_experience(experience_gained)

        money_gained = battle.wild_level * 5
        battle.player.money += money_gained
        battle.player.save()

        victory_message = f'{message} ¡Has derrotado al {battle.wild_pokemon.name} salvaje! '
        victory_message += f'Ganaste {experience_gained} de experiencia y ${money_gained}.'

        if leveled_up:
            victory_message += f' ¡{original_pokemon_name} subió al nivel {player_pokemon.level}!'

            if player_pokemon.just_evolved:
                victory_message += f' ¡Y evolucionó a {player_pokemon.pokemon.name}!'

        return Response({
            'message': victory_message,
            'battle_ended': True,
            'won': True,
            'experience_gained': experience_gained,
            'money_gained': money_gained,
            'leveled_up': leveled_up,
            'new_level': player_pokemon.level if leveled_up else None,
            'evolved': player_pokemon.just_evolved if leveled_up else False,
            'new_pokemon_name': player_pokemon.pokemon.name if player_pokemon.just_evolved else None
        })

    def handle_battle_loss(self, battle, message):
        last_town = battle.player.current_location
        if not last_town or last_town.location_type != 'town':
            from pokemon.models.Location import Location
            last_town = Location.objects.filter(location_type='town').first()

        battle.player.current_location = last_town
        battle.player.save()

        from usuario.models.PlayerPokemon import PlayerPokemon
        PlayerPokemon.objects.filter(player=battle.player).update(current_hp=models.F('hp'))

        return Response({
            'message': f'{message} Todos tus Pokémon fueron derrotados. Has sido transportado a {last_town.name} y tus Pokémon han sido curados.',
            'battle_ended': True,
            'lost': True,
            'new_location': last_town.name
        })

    def handle_capture(self, battle, ball_type):
        new_pokemon = PlayerPokemon.objects.create(
            player=battle.player,
            pokemon=battle.wild_pokemon,
            level=battle.wild_level,
            experience=0,
            in_team=False
        )
        new_pokemon.calculate_stats()

        PlayerPokemon.objects.filter(pk=new_pokemon.pk).update(
            hp=new_pokemon.hp,
            current_hp=new_pokemon.hp,
            attack=new_pokemon.attack,
            defense=new_pokemon.defense,
            special_attack=new_pokemon.special_attack,
            special_defense=new_pokemon.special_defense,
            speed=new_pokemon.speed
        )

        wild_moves = PokemonMove.objects.filter(
            pokemon=battle.wild_pokemon,
            level__lte=battle.wild_level
        )[:2]
        for move in wild_moves:
            new_pokemon.moves.add(move.move)

        from usuario.models.Pokedex import Pokedex
        pokedex_entry, created = Pokedex.objects.get_or_create(
            player=battle.player,
            pokemon=battle.wild_pokemon
        )
        pokedex_entry.state = 'caught'
        pokedex_entry.save()

        return Response({
            'message': f'¡Has capturado a {battle.wild_pokemon.name} con una {ball_type}!',
            'battle_ended': True,
            'captured': True,
            'new_pokemon_id': new_pokemon.id
        })

    def get_battle_state(self, battle):
        moves_with_pp = []
        for move in battle.player_pokemon.moves.all():
            current_pp = self.get_move_current_pp(battle.player_pokemon, move.id)
            max_pp = move.pp

            moves_with_pp.append({
                'id': move.id,
                'name': move.name,
                'type': move.type,
                'current_pp': current_pp,
                'max_pp': max_pp
            })

        if battle.battle_type == 'wild':
            return {
                'battle_type': 'wild',
                'battle_id': battle.id,
                'player_pokemon': {
                    'id': battle.player_pokemon.id,
                    'name': battle.player_pokemon.pokemon.name,
                    'current_hp': battle.player_pokemon.current_hp,
                    'max_hp': battle.player_pokemon.hp,
                    'moves': moves_with_pp
                },
                'wild_pokemon': {
                    'id': battle.wild_pokemon.id,
                    'name': battle.wild_pokemon.name,
                    'current_hp': battle.wild_current_hp,
                    'max_hp': battle.wild_max_hp
                },
                'state': battle.state
            }
        else:
            current_opponent = battle.current_opponent_pokemon

            alive_pokemon = sum(1 for p in battle.trainer_team if p['current_hp'] > 0)

            return {
                'battle_type': 'trainer',
                'battle_id': battle.id,
                'trainer': {
                    'name': battle.trainer_name,
                    'sprite': battle.trainer_sprite,
                    'alive_pokemon': alive_pokemon,
                    'total_pokemon': len(battle.trainer_team)
                },
                'player_pokemon': {
                    'id': battle.player_pokemon.id,
                    'name': battle.player_pokemon.pokemon.name,
                    'current_hp': battle.player_pokemon.current_hp,
                    'max_hp': battle.player_pokemon.hp,
                    'moves': moves_with_pp
                },
                'opponent_pokemon': current_opponent,
                'state': battle.state
            }

    def generate_random_trainer(self, location):
        trainer_names_by_type = {
            'beginner': ['Alex', 'Sofía', 'Leo', 'Emma', 'Luis', 'Ana'],
            'intermediate': ['Entrenador Marcos', 'Entrenadora Carla', 'Rival Diego', 'Rival Elena'],
            'advanced': ['Maestro Koga', 'Maestro Bruno', 'Líder Blanca', 'Líder Rojo'],
            'gym_leader': ['Líder Brock', 'Líder Misty', 'Líder Lt. Surge', 'Líder Erika'],
        }

        trainer_sprites = {
            'beginner': 'https://example.com/trainer_beginner.png',
            'intermediate': 'https://example.com/trainer_intermediate.png',
            'advanced': 'https://example.com/trainer_advanced.png',
            'gym_leader': 'https://example.com/trainer_gym_leader.png',
        }

        trainer_types = ['beginner', 'intermediate', 'advanced', 'gym_leader']
        weights = [0.4, 0.3, 0.2, 0.1]
        trainer_type = random.choices(trainer_types, weights=weights)[0]

        name = random.choice(trainer_names_by_type[trainer_type])

        dialogues = {
            'beginner': f"¡Hola! Soy {name}, un entrenador principiante. ¡Prepárate para luchar!",
            'intermediate': f"Soy {name}. Mi equipo está bien entrenado. ¡No será fácil!",
            'advanced': f"Yo, {name}, te mostraré la fuerza de un entrenador experimentado.",
            'gym_leader': f"¡Soy {name}! Para pasar, tendrás que derrotar a mi poderoso equipo.",
        }

        team = self.generate_trainer_team(location, trainer_type)

        if not team:
            return None

        base_reward = {
            'beginner': 50,
            'intermediate': 100,
            'advanced': 200,
            'gym_leader': 500,
        }

        money_reward = base_reward[trainer_type] * len(team)

        return {
            'name': name,
            'type': trainer_type,
            'sprite': trainer_sprites[trainer_type],
            'dialogue': dialogues[trainer_type],
            'team': team,
            'money_reward': money_reward,
        }

    def generate_trainer_team(self, location, trainer_type):
        from pokemon.models.WildPokemonEncounter import WildPokemonEncounter
        from pokemon.models.PokemonMove import PokemonMove

        encounters = WildPokemonEncounter.objects.filter(location=location)

        if not encounters:
            return []

        team_sizes = {
            'beginner': (1, 2),
            'intermediate': (2, 3),
            'advanced': (3, 4),
            'gym_leader': (5, 6),
        }

        min_size, max_size = team_sizes[trainer_type]
        team_size = random.randint(min_size, max_size)

        base_levels = {
            'beginner': (3, 7),
            'intermediate': (8, 15),
            'advanced': (16, 25),
            'gym_leader': (26, 40),
        }

        min_level, max_level = base_levels[trainer_type]

        team = []
        used_pokemon_ids = set()

        for _ in range(team_size):
            encounter = self.select_weighted_encounter(encounters)

            if encounter.pokemon.id in used_pokemon_ids:
                available_encounters = [e for e in encounters if e.pokemon.id not in used_pokemon_ids]
                if available_encounters:
                    encounter = self.select_weighted_encounter(available_encounters)

            used_pokemon_ids.add(encounter.pokemon.id)

            level = random.randint(min_level, max_level)

            hp = self.calculate_hp(encounter.pokemon.base_hp, level)
            attack = self.calculate_stat(encounter.pokemon.base_attack, level)
            defense = self.calculate_stat(encounter.pokemon.base_defense, level)
            special_attack = self.calculate_stat(encounter.pokemon.base_special_attack, level)
            special_defense = self.calculate_stat(encounter.pokemon.base_special_defense, level)
            speed = self.calculate_stat(encounter.pokemon.base_speed, level)

            wild_moves = PokemonMove.objects.filter(
                pokemon=encounter.pokemon,
                level__lte=level
            ).select_related('move').order_by('-level')[:4]

            pokemon_data = {
                'pokemon_id': encounter.pokemon.id,
                'pokemon_name': encounter.pokemon.name,
                'level': level,
                'current_hp': hp,
                'max_hp': hp,
                'attack': attack,
                'defense': defense,
                'special_attack': special_attack,
                'special_defense': special_defense,
                'speed': speed,
                'type1': encounter.pokemon.type1,
                'type2': encounter.pokemon.type2,
                'sprite_front': encounter.pokemon.sprite_front,
                'sprite_back': encounter.pokemon.sprite_back,
                'moves': [
                    {
                        'id': pokemon_move.move.id,
                        'name': pokemon_move.move.name,
                        'type': pokemon_move.move.type,
                        'power': pokemon_move.move.power,
                        'accuracy': pokemon_move.move.accuracy,
                        'pp': pokemon_move.move.pp,
                        'damage_class': pokemon_move.move.damage_class,
                        'current_pp': pokemon_move.move.pp
                    } for pokemon_move in wild_moves
                ]
            }

            team.append(pokemon_data)

        return team

    def select_weighted_encounter(self, encounters):
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

    @action(detail=False, methods=['get'])
    def can_start_trainer_battle(self, request):
        player = request.user.player_profile

        if not player.current_location:
            return Response({
                'can_battle': False,
                'reason': 'No estás en ninguna ubicación'
            })

        if player.current_location.location_type != 'route':
            return Response({
                'can_battle': False,
                'reason': 'Solo puedes combatir con entrenadores en rutas'
            })

        from pokemon.models.WildPokemonEncounter import WildPokemonEncounter
        encounters = WildPokemonEncounter.objects.filter(location=player.current_location)
        if not encounters.exists():
            return Response({
                'can_battle': False,
                'reason': 'No hay Pokémon disponibles en esta ruta para generar entrenadores'
            })

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

    def calculate_damage_trainer(self, attacker, defender_data, move):
        if move.damage_class == 'status':
            return 0

        if move.damage_class == 'physical':
            attack_stat = attacker.attack
            defense_stat = defender_data['defense']
        else:  # special
            attack_stat = attacker.special_attack
            defense_stat = defender_data['special_defense']

        level_factor = (2 * attacker.level) / 5 + 2
        power_factor = move.power if move.power else 0
        stat_factor = attack_stat / defense_stat

        base_damage = (level_factor * power_factor * stat_factor) / 50 + 2

        defender_types = [defender_data['type1']]
        if defender_data.get('type2'):
            defender_types.append(defender_data['type2'])

        type_effectiveness = self.get_type_effectiveness(move.type, defender_types)
        base_damage *= type_effectiveness

        base_damage *= random.uniform(0.85, 1.0)

        return int(max(1, base_damage))

    def trainer_attack(self, battle):
        if battle.battle_type != 'trainer':
            return 0, {'name': 'Tackle', 'type': 'normal'}

        current_pokemon = battle.trainer_team[battle.current_trainer_pokemon]

        available_moves = current_pokemon['moves']
        if not available_moves:
            return 0, {'name': 'Tackle', 'type': 'normal'}

        move = random.choice(available_moves)

        damage = self.calculate_damage_trainer_reverse(
            current_pokemon,
            battle.player_pokemon,
            move
        )

        return damage, move

    def calculate_damage_trainer_reverse(self, attacker_data, defender, move_dict):
        from pokemon.models.Move import Move

        move = Move(
            name=move_dict['name'],
            type=move_dict['type'],
            power=move_dict.get('power', 0),
            accuracy=move_dict.get('accuracy', 100),
            damage_class=move_dict.get('damage_class', 'physical')
        )

        if move.damage_class == 'status':
            return 0

        if move.damage_class == 'physical':
            attack_stat = attacker_data['attack']
            defense_stat = defender.defense
        else:  # special
            attack_stat = attacker_data['special_attack']
            defense_stat = defender.special_defense

        level_factor = (2 * attacker_data['level']) / 5 + 2
        power_factor = move.power if move.power else 0
        stat_factor = attack_stat / defense_stat

        base_damage = (level_factor * power_factor * stat_factor) / 50 + 2

        defender_types = [defender.pokemon.type1]
        if defender.pokemon.type2:
            defender_types.append(defender.pokemon.type2)

        type_effectiveness = self.get_type_effectiveness(move.type, defender_types)
        base_damage *= type_effectiveness

        base_damage *= random.uniform(0.85, 1.0)

        return int(max(1, base_damage))

    def get_next_trainer_pokemon(self, battle):
        for i, pokemon in enumerate(battle.trainer_team):
            if pokemon['current_hp'] > 0:
                return i
        return None

    def handle_trainer_battle_win(self, battle, message):
        base_experience = 100
        total_experience = 0

        for pokemon in battle.trainer_team:
            if pokemon['current_hp'] <= 0:
                total_experience += base_experience * pokemon['level'] // 10

        original_level = battle.player_pokemon.level

        leveled_up = battle.player_pokemon.add_experience(total_experience)

        money_gained = battle.trainer_money_reward
        battle.player.money += money_gained
        battle.player.save()

        victory_message = f'{message} ¡Has derrotado a {battle.trainer_name}! '
        victory_message += f'Ganaste ${money_gained} y {total_experience} de experiencia.'

        if leveled_up:
            victory_message += f' ¡{battle.player_pokemon.pokemon.name} subió al nivel {battle.player_pokemon.level}!'

        return Response({
            'message': victory_message,
            'battle_ended': True,
            'won': True,
            'trainer_defeated': True,
            'money_gained': money_gained,
            'experience_gained': total_experience,
            'leveled_up': leveled_up,
            'new_level': battle.player_pokemon.level if leveled_up else None
        })

    def handle_trainer_battle_loss(self, battle, message):
        from pokemon.models.Location import Location
        last_town = battle.player.current_location

        if not last_town or last_town.location_type != 'town':
            last_town = Location.objects.filter(location_type='town').first()

        battle.player.current_location = last_town
        battle.player.save()

        from usuario.models.PlayerPokemon import PlayerPokemon
        PlayerPokemon.objects.filter(player=battle.player).update(current_hp=models.F('hp'))

        return Response({
            'message': f'{message} Todos tus Pokémon fueron derrotados por {battle.trainer_name}. Has sido transportado a {last_town.name} y tus Pokémon han sido curados.',
            'battle_ended': True,
            'lost': True,
            'new_location': last_town.name
        })
