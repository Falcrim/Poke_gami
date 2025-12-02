# usuario/api/PvPBattleViewSet.py
from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
import random
import string
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from usuario.models.Battle import Battle
from usuario.models.Player import Player
from usuario.models.PlayerPokemon import PlayerPokemon
from pokemon.models.Pokemon import Pokemon
from pokemon.models.Move import Move
import json


class PvPBattleSerializer(serializers.ModelSerializer):
    player1_username = serializers.CharField(source='player1.user.username', read_only=True)
    player2_username = serializers.CharField(source='player2.user.username', read_only=True)

    class Meta:
        model = Battle
        fields = ('id', 'room_code', 'battle_format', 'player1', 'player1_username',
                  'player2', 'player2_username', 'state', 'current_turn', 'created_at')


class PvPBattleViewSet(viewsets.ViewSet):
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

    def generate_room_code(self):
        """Genera un código único de sala"""
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Battle.objects.filter(room_code=code).exists():
                return code

    def scale_pokemon_to_level_50(self, player_pokemon):
        level = 50

        # Calcular stats (igual que antes)
        hp = int((2 * player_pokemon.pokemon.base_hp * level) / 100) + level + 10
        attack = int((2 * player_pokemon.pokemon.base_attack * level) / 100) + 5
        defense = int((2 * player_pokemon.pokemon.base_defense * level) / 100) + 5
        special_attack = int((2 * player_pokemon.pokemon.base_special_attack * level) / 100) + 5
        special_defense = int((2 * player_pokemon.pokemon.base_special_defense * level) / 100) + 5
        speed = int((2 * player_pokemon.pokemon.base_speed * level) / 100) + 5

        from pokemon.models.PokemonMove import PokemonMove

        moves_data = []
        current_move_ids = set()

        # 1. PRIMERO: Movimientos actuales del Pokémon (respetando elección del jugador)
        current_moves = list(player_pokemon.moves.all())
        for move in current_moves[:4]:  # Solo hasta 4
            current_pp = player_pokemon.moves_pp.get(str(move.id), move.pp) if player_pokemon.moves_pp else move.pp

            moves_data.append({
                'id': move.id,
                'name': move.name,
                'type': move.type,
                'power': move.power or 0,
                'accuracy': move.accuracy or 100,
                'pp': move.pp,
                'current_pp': current_pp,
                'damage_class': move.damage_class
            })
            current_move_ids.add(move.id)

        # 2. SEGUNDO: Si tenemos menos de 4, agregar movimientos por nivel (más fuertes primero)
        if len(moves_data) < 4:
            # Obtener todos los movimientos por nivel ordenados por:
            # 1. Movimientos de daño primero (no status)
            # 2. Mayor poder
            # 3. Mayor nivel aprendido
            level_moves = PokemonMove.objects.filter(
                pokemon=player_pokemon.pokemon,
                level__lte=level
            ).select_related('move').order_by('-level')

            # Convertir a lista para ordenar personalizado
            move_list = []
            for pm in level_moves:
                move = pm.move
                if move.id in current_move_ids:
                    continue

                # Puntuación para ordenar
                score = 0
                if move.damage_class != 'status':
                    score += 1000  # Priorizar movimientos de daño
                score += move.power or 0  # Mayor poder = mejor
                score += pm.level * 10  # Mayor nivel aprendido = mejor

                move_list.append((score, move))

            # Ordenar por score descendente
            move_list.sort(key=lambda x: x[0], reverse=True)

            for score, move in move_list:
                if len(moves_data) >= 4:
                    break

                moves_data.append({
                    'id': move.id,
                    'name': move.name,
                    'type': move.type,
                    'power': move.power or 0,
                    'accuracy': move.accuracy or 100,
                    'pp': move.pp,
                    'current_pp': move.pp,
                    'damage_class': move.damage_class
                })
                current_move_ids.add(move.id)

        # 3. TERCERO: Si aún falta, agregar movimientos del mismo tipo (preferiblemente de daño)
        if len(moves_data) < 4:
            # Buscar movimientos del tipo del Pokémon
            type_moves = Move.objects.filter(
                type__in=[player_pokemon.pokemon.type1, player_pokemon.pokemon.type2]
            ).exclude(id__in=current_move_ids).order_by('-power')

            for move in type_moves:
                if len(moves_data) >= 4:
                    break

                moves_data.append({
                    'id': move.id,
                    'name': move.name,
                    'type': move.type,
                    'power': move.power or 0,
                    'accuracy': move.accuracy or 100,
                    'pp': move.pp,
                    'current_pp': move.pp,
                    'damage_class': move.damage_class
                })
                current_move_ids.add(move.id)

        # 4. CUARTO: Como último recurso, movimientos básicos útiles
        if len(moves_data) < 4:
            basic_moves_list = [
                ('Quick Attack', 40, 100),  # Ataque prioritario
                ('Tackle', 40, 100),
                ('Scratch', 40, 100),
                ('Pound', 40, 100),
                ('Ember', 40, 100),  # Para Pokémon de fuego
                ('Water Gun', 40, 100),  # Para Pokémon de agua
                ('Vine Whip', 45, 100),  # Para Pokémon de planta
                ('Thunder Shock', 40, 100),  # Para Pokémon eléctrico
            ]

            for move_name, power, accuracy in basic_moves_list:
                if len(moves_data) >= 4:
                    break

                move = Move.objects.filter(name=move_name).first()
                if move and move.id not in current_move_ids:
                    moves_data.append({
                        'id': move.id,
                        'name': move.name,
                        'type': move.type,
                        'power': move.power or power,
                        'accuracy': move.accuracy or accuracy,
                        'pp': move.pp,
                        'current_pp': move.pp,
                        'damage_class': move.damage_class
                    })
                    current_move_ids.add(move.id)

        # Asegurar que tenemos al menos 1 movimiento (nunca debería pasar)
        if not moves_data:
            default_move = Move.objects.filter(damage_class='physical', power__gt=0).first()
            if default_move:
                moves_data.append({
                    'id': default_move.id,
                    'name': default_move.name,
                    'type': default_move.type,
                    'power': default_move.power,
                    'accuracy': default_move.accuracy,
                    'pp': default_move.pp,
                    'current_pp': default_move.pp,
                    'damage_class': default_move.damage_class
                })

        return {
            'pokemon_id': player_pokemon.pokemon.id,
            'pokemon_name': player_pokemon.pokemon.name,
            'player_pokemon_id': player_pokemon.id,
            'level': level,
            'current_hp': hp,
            'max_hp': hp,
            'attack': attack,
            'defense': defense,
            'special_attack': special_attack,
            'special_defense': special_defense,
            'speed': speed,
            'type1': player_pokemon.pokemon.type1,
            'type2': player_pokemon.pokemon.type2,
            'sprite_front': player_pokemon.pokemon.sprite_front,
            'sprite_back': player_pokemon.pokemon.sprite_back,
            'moves': moves_data,
            'total_moves': len(moves_data),
            'auto_filled_moves': len(moves_data) - len(current_moves)  # Para debug
        }

    @action(detail=False, methods=['post'])
    def create_room(self, request):
        """Crear una sala de PvP"""
        player = request.user.player_profile
        battle_format = request.data.get('battle_format', '1vs1')

        if battle_format not in ['1vs1', '2vs2']:
            return Response({'error': 'Formato de batalla no válido'}, status=400)

        # Verificar que el jugador tiene Pokémon suficientes
        required_pokemon = 1 if battle_format == '1vs1' else 2
        available_pokemon = player.pokemons.filter(in_team=True, current_hp__gt=0).count()

        if available_pokemon < required_pokemon:
            return Response({
                'error': f'Necesitas al menos {required_pokemon} Pokémon en tu equipo para este formato'
            }, status=400)

        # Obtener los Pokémon del equipo
        team_pokemons = player.pokemons.filter(in_team=True, current_hp__gt=0).order_by('order')[:required_pokemon]

        # Escalar Pokémon al nivel 50
        scaled_team = []
        for pokemon in team_pokemons:
            scaled_team.append(self.scale_pokemon_to_level_50(pokemon))

        with transaction.atomic():
            # Crear la batalla
            battle = Battle.objects.create(
                battle_type='pvp',
                battle_format=battle_format,
                player1=player,
                current_turn=player,
                player1_team=scaled_team,
                state='waiting',
                room_code=self.generate_room_code(),
                is_private=request.data.get('is_private', False),
                password=request.data.get('password', None)
            )

        return Response({
            'message': f'Sala creada con código: {battle.room_code}',
            'room_code': battle.room_code,
            'battle_id': battle.id,
            'battle_format': battle_format,
            'your_team': scaled_team
        })

    @action(detail=False, methods=['get'])
    def available_rooms(self, request):
        """Obtener salas disponibles para unirse"""
        rooms = Battle.objects.filter(
            battle_type='pvp',
            state='waiting',
            player2__isnull=True,
            is_private=False
        ).exclude(player1__user=request.user)

        serializer = PvPBattleSerializer(rooms, many=True)
        return Response({
            'rooms': serializer.data,
            'count': rooms.count()
        })

    @action(detail=False, methods=['post'])
    def join_room(self, request):
        """Unirse a una sala de PvP"""
        player = request.user.player_profile
        room_code = request.data.get('room_code')
        password = request.data.get('password')

        if not room_code:
            return Response({'error': 'Se requiere room_code'}, status=400)

        try:
            battle = Battle.objects.get(
                room_code=room_code,
                battle_type='pvp',
                state='waiting',
                player2__isnull=True
            )
        except Battle.DoesNotExist:
            return Response({'error': 'Sala no encontrada o no disponible'}, status=404)

        # Verificar contraseña si la sala es privada
        if battle.is_private and battle.password != password:
            return Response({'error': 'Contraseña incorrecta'}, status=403)

        # No permitir unirse a tu propia sala
        if battle.player1 == player:
            return Response({'error': 'No puedes unirte a tu propia sala'}, status=400)

        # Verificar que el jugador tiene Pokémon suficientes
        required_pokemon = 1 if battle.battle_format == '1vs1' else 2
        available_pokemon = player.pokemons.filter(in_team=True, current_hp__gt=0).count()

        if available_pokemon < required_pokemon:
            return Response({
                'error': f'Necesitas al menos {required_pokemon} Pokémon en tu equipo para esta batalla'
            }, status=400)

        # Obtener los Pokémon del equipo
        team_pokemons = player.pokemons.filter(in_team=True, current_hp__gt=0).order_by('order')[:required_pokemon]

        # Escalar Pokémon al nivel 50
        scaled_team = []
        for pokemon in team_pokemons:
            scaled_team.append(self.scale_pokemon_to_level_50(pokemon))

        with transaction.atomic():
            # Unir al jugador a la batalla
            battle.player2 = player
            battle.player2_team = scaled_team
            battle.state = 'active'

            # Decidir quién comienza basado en la velocidad del primer Pokémon
            player1_speed = battle.player1_team[0]['speed'] if battle.player1_team else 0
            player2_speed = scaled_team[0]['speed'] if scaled_team else 0

            if player1_speed > player2_speed:
                battle.current_turn = battle.player1
            elif player2_speed > player1_speed:
                battle.current_turn = battle.player2
            else:
                # Empate, decide aleatoriamente
                battle.current_turn = random.choice([battle.player1, battle.player2])

            battle.save()

        return Response({
            'message': f'Te has unido a la batalla contra {battle.player1.user.username}',
            'battle_id': battle.id,
            'battle_format': battle.battle_format,
            'your_team': scaled_team,
            'opponent_username': battle.player1.user.username,
            'your_turn': battle.current_turn == player,
            'battle_state': self.get_pvp_battle_state(battle, player)
        })

    @action(detail=True, methods=['get'])
    def state(self, request, pk=None):
        """Obtener el estado actual de la batalla PvP"""
        battle = self.get_pvp_battle(pk, request.user)
        if not battle:
            return Response({'error': 'Batalla PvP no encontrada o no tienes acceso'}, status=404)

        return Response(self.get_pvp_battle_state(battle, request.user.player_profile))

    @action(detail=True, methods=['post'])
    def attack(self, request, pk=None):
        """Atacar en batalla PvP"""
        battle = self.get_pvp_battle(pk, request.user)
        if not battle:
            return Response({'error': 'Batalla PvP no encontrada'}, status=404)

        player = request.user.player_profile

        # Verificar que es el turno del jugador
        if not battle.is_player_turn(player):
            return Response({'error': 'No es tu turno'}, status=400)

        move_id = request.data.get('move_id')
        target = request.data.get('target', 0)  # Para 2vs2, especificar qué Pokémon atacar

        if not move_id:
            return Response({'error': 'Se requiere move_id'}, status=400)

        # Obtener Pokémon actual del jugador
        player_pokemon = battle.get_current_pokemon(player)
        if not player_pokemon or player_pokemon['current_hp'] <= 0:
            return Response({'error': 'Tu Pokémon actual está debilitado'}, status=400)

        # Buscar el movimiento en los movimientos del Pokémon
        move = None
        for m in player_pokemon['moves']:
            if str(m['id']) == str(move_id):
                move = m
                break

        if not move:
            return Response({'error': 'Movimiento no disponible'}, status=400)

        # Verificar PP
        if move['current_pp'] <= 0:
            return Response({'error': f'No hay PP restantes para {move["name"]}'}, status=400)

        with transaction.atomic():
            # Reducir PP
            move['current_pp'] -= 1

            # Actualizar el equipo del jugador
            if player == battle.player1:
                battle.player1_team[battle.player1_current_pokemon] = player_pokemon
            else:
                battle.player2_team[battle.player2_current_pokemon] = player_pokemon

            # Obtener Pokémon objetivo
            opponent = battle.player2 if player == battle.player1 else battle.player1
            opponent_team = battle.get_current_opponent_team(player)

            # Para 2vs2, seleccionar el objetivo
            if battle.battle_format == '2vs2':
                if target < 0 or target >= len(opponent_team):
                    return Response({'error': 'Objetivo no válido'}, status=400)
                opponent_pokemon = opponent_team[target]
            else:
                # 1vs1, atacar al Pokémon actual
                opponent_pokemon = battle.get_opponent_current_pokemon(player)

            if not opponent_pokemon or opponent_pokemon['current_hp'] <= 0:
                return Response({'error': 'El Pokémon objetivo está debilitado'}, status=400)

            # Calcular daño
            damage = self.calculate_pvp_damage(player_pokemon, opponent_pokemon, move)

            # Aplicar daño
            opponent_pokemon['current_hp'] -= damage
            opponent_pokemon['current_hp'] = max(0, opponent_pokemon['current_hp'])

            # Actualizar equipo del oponente
            if player == battle.player1:
                battle.player2_team[battle.player2_current_pokemon] = opponent_pokemon
            else:
                battle.player1_team[battle.player1_current_pokemon] = opponent_pokemon

            message = f'{player_pokemon["pokemon_name"]} usó {move["name"]}. '
            if damage > 0:
                message += f'Causó {damage} de daño.'

            # Verificar si el Pokémon oponente fue derrotado
            if opponent_pokemon['current_hp'] <= 0:
                message += f' ¡{opponent_pokemon["pokemon_name"]} fue derrotado!'

                # Verificar si todo el equipo oponente está derrotado
                if battle.check_team_defeated(battle.get_current_opponent_team(player)):
                    battle.end_battle(player)
                    message += f' ¡Has ganado la batalla!'

                    return Response({
                        'message': message,
                        'battle_ended': True,
                        'winner': player.user.username,
                        'battle_state': self.get_pvp_battle_state(battle, player)
                    })

            # Cambiar turno al oponente
            battle.current_turn = opponent
            battle.save()

            return Response({
                'message': message,
                'damage': damage,
                'your_turn': False,
                'battle_state': self.get_pvp_battle_state(battle, player)
            })

    @action(detail=True, methods=['post'])
    def switch_pokemon(self, request, pk=None):
        """Cambiar de Pokémon en batalla PvP (solo en 2vs2)"""
        battle = self.get_pvp_battle(pk, request.user)
        if not battle:
            return Response({'error': 'Batalla PvP no encontrada'}, status=404)

        player = request.user.player_profile

        # Verificar que es el turno del jugador
        if not battle.is_player_turn(player):
            return Response({'error': 'No es tu turno'}, status=400)

        # Solo permitir en formato 2vs2
        if battle.battle_format != '2vs2':
            return Response({'error': 'Solo se puede cambiar Pokémon en formato 2vs2'}, status=400)

        pokemon_index = request.data.get('pokemon_index')
        if pokemon_index is None:
            return Response({'error': 'Se requiere pokemon_index'}, status=400)

        team = battle.get_current_player_team(player)
        current_index = battle.get_current_pokemon_index(player)

        if pokemon_index < 0 or pokemon_index >= len(team):
            return Response({'error': 'Índice de Pokémon no válido'}, status=400)

        if pokemon_index == current_index:
            return Response({'error': 'Ya estás usando ese Pokémon'}, status=400)

        if team[pokemon_index]['current_hp'] <= 0:
            return Response({'error': 'Ese Pokémon está debilitado'}, status=400)

        with transaction.atomic():
            # Cambiar Pokémon
            if player == battle.player1:
                battle.player1_current_pokemon = pokemon_index
            else:
                battle.player2_current_pokemon = pokemon_index

            # Cambiar turno al oponente
            opponent = battle.player2 if player == battle.player1 else battle.player1
            battle.current_turn = opponent
            battle.save()

            return Response({
                'message': f'Cambiaste a {team[pokemon_index]["pokemon_name"]}',
                'your_turn': False,
                'battle_state': self.get_pvp_battle_state(battle, player)
            })

    @action(detail=True, methods=['post'])
    def surrender(self, request, pk=None):
        """Rendirse en batalla PvP"""
        battle = self.get_pvp_battle(pk, request.user)
        if not battle:
            return Response({'error': 'Batalla PvP no encontrada'}, status=404)

        player = request.user.player_profile
        opponent = battle.player2 if player == battle.player1 else battle.player1

        with transaction.atomic():
            battle.end_battle(opponent)

            return Response({
                'message': 'Te has rendido',
                'battle_ended': True,
                'winner': opponent.user.username,
                'loser': player.user.username
            })

    @action(detail=True, methods=['post'])
    def use_item(self, request, pk=None):
        battle = self.get_pvp_battle(pk, request.user)
        if not battle:
            return Response({'error': 'Batalla no encontrada'}, status=404)

        player = request.user.player_profile
        item_type = request.data.get('item_type')

        # Verificar turno
        if not battle.is_player_turn(player):
            return Response({'error': 'No es tu turno'}, status=400)

        # Lógica de usar poción (similar a battle salvaje)
        if item_type in ['potion', 'super_potion', 'hyper_potion']:
            # Usar poción
            bag = Bag.objects.get(player=player)

            if getattr(bag, f'{item_type}s', 0) <= 0:
                return Response({'error': f'No tienes {item_type}s'}, status=400)

            heal_amounts = {
                'potion': 20,
                'super_potion': 50,
                'hyper_potion': 200
            }

            heal_amount = heal_amounts[item_type]
            current_pokemon = battle.get_current_pokemon(player)

            new_hp = min(current_pokemon['current_hp'] + heal_amount, current_pokemon['max_hp'])
            actual_heal = new_hp - current_pokemon['current_hp']

            # Actualizar HP
            current_pokemon['current_hp'] = new_hp

            # Guardar cambios
            if player == battle.player1:
                battle.player1_team[battle.player1_current_pokemon] = current_pokemon
            else:
                battle.player2_team[battle.player2_current_pokemon] = current_pokemon

            # Usar item del inventario
            setattr(bag, f'{item_type}s', getattr(bag, f'{item_type}s') - 1)
            bag.save()

            message = f'{player.user.username} usó una {item_type}. Curó {actual_heal} HP.'

            # Cambiar turno
            opponent = battle.player2 if player == battle.player1 else battle.player1
            battle.current_turn = opponent
            battle.save()

            # Notificar a ambos jugadores
            self.send_battle_notification(battle.id, {
                'action': 'use_item',
                'player': player.user.username,
                'item': item_type,
                'pokemon': current_pokemon['pokemon_name'],
                'heal': actual_heal,
                'message': message,
                'turn_changed_to': opponent.user.username
            })

            return Response({
                'message': message,
                'healed': actual_heal,
                'your_turn': False,
                'battle_state': self.get_pvp_battle_state(battle, player)
            })

        return Response({'error': 'Item no válido para PvP'}, status=400)

    def get_pvp_battle(self, battle_id, user):
        """Obtener una batalla PvP donde el usuario sea jugador"""
        try:
            battle = Battle.objects.get(
                id=battle_id,
                battle_type='pvp'
            )
            if battle.player1.user == user or (battle.player2 and battle.player2.user == user):
                return battle
            return None
        except Battle.DoesNotExist:
            return None

    def get_pvp_battle_state(self, battle, player):
        """Obtener el estado de la batalla PvP para un jugador"""
        is_player1 = (player == battle.player1)

        # Verificaciones de seguridad para evitar None
        player1_username = battle.player1.user.username if battle.player1 else None
        player2_username = battle.player2.user.username if battle.player2 else None
        current_turn_username = battle.current_turn.user.username if battle.current_turn else None
        winner_username = battle.winner.user.username if battle.winner else None

        return {
            'battle_id': battle.id,
            'room_code': battle.room_code,
            'battle_format': battle.battle_format,
            'state': battle.state,
            'your_turn': battle.is_player_turn(player) if hasattr(battle, 'is_player_turn') else (
                        battle.current_turn == player),
            'current_turn_username': current_turn_username,
            'your_team': battle.player1_team if is_player1 else battle.player2_team,
            'opponent_team': battle.player2_team if is_player1 else battle.player1_team,
            'your_current_pokemon_index': battle.player1_current_pokemon if is_player1 else battle.player2_current_pokemon,
            'opponent_current_pokemon_index': battle.player2_current_pokemon if is_player1 else battle.player1_current_pokemon,
            'player1_username': player1_username,
            'player2_username': player2_username,
            'winner_username': winner_username
        }

    def calculate_pvp_damage(self, attacker, defender, move):
        """Calcular daño en batalla PvP"""
        if move.get('damage_class') == 'status':
            return 0

        # Determinar stat de ataque y defensa
        if move['damage_class'] == 'physical':
            attack_stat = attacker['attack']
            defense_stat = defender['defense']
        else:  # special
            attack_stat = attacker['special_attack']
            defense_stat = defender['special_defense']

        # Fórmula de daño
        level = 50  # Todos a nivel 50 en PvP
        level_factor = (2 * level) / 5 + 2
        power_factor = move['power'] if move['power'] else 0
        stat_factor = attack_stat / defense_stat

        base_damage = (level_factor * power_factor * stat_factor) / 50 + 2

        # Modificador de tipo
        defender_types = [defender['type1']]
        if defender['type2']:
            defender_types.append(defender['type2'])

        type_effectiveness = self.get_type_effectiveness(move['type'], defender_types)
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