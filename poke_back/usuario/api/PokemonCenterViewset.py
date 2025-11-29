from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from usuario.models.Player import Player
from usuario.models.PlayerPokemon import PlayerPokemon
from pokemon.models.Move import Move


class PokemonCenterViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def _check_location(self, player):
        if not player.current_location:
            raise ValidationError('No estás en ninguna ubicación')
        if player.current_location.location_type != 'town':
            raise ValidationError('Solo puedes usar el Centro Pokémon en pueblos')

    @action(detail=False, methods=['post'])
    def heal_team(self, request):
        player = request.user.player_profile

        try:
            self._check_location(player)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        team_pokemons = player.pokemons.filter(in_team=True)

        healed_count = 0
        for pokemon in team_pokemons:
            PlayerPokemon.objects.filter(pk=pokemon.pk).update(current_hp=pokemon.hp)
            healed_count += 1

        return Response({
            'message': f'Todos tus Pokémon del equipo han sido curados ({healed_count} Pokémon)',
            'healed_count': healed_count
        })

    @action(detail=False, methods=['get'])
    def get_team_and_reserve(self, request):
        player = request.user.player_profile

        try:
            self._check_location(player)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        team_pokemons = player.pokemons.filter(in_team=True).order_by('order')
        reserve_pokemons = player.pokemons.filter(in_team=False)

        from usuario.api.PlayerPokemonViewSet import PlayerPokemonSerializer
        team_serializer = PlayerPokemonSerializer(team_pokemons, many=True)
        reserve_serializer = PlayerPokemonSerializer(reserve_pokemons, many=True)

        return Response({
            'team': team_serializer.data,
            'reserve': reserve_serializer.data,
            'team_count': team_pokemons.count(),
            'reserve_count': reserve_pokemons.count(),
            'max_team_size': 6
        })

    @action(detail=True, methods=['post'], url_path='move-to-reserve')
    def move_to_reserve(self, request, pk=None):
        player = request.user.player_profile

        try:
            self._check_location(player)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        try:
            pokemon = PlayerPokemon.objects.get(pk=pk, player__user=request.user, in_team=True)
        except PlayerPokemon.DoesNotExist:
            return Response({'error': 'Pokémon no encontrado en tu equipo'}, status=404)

        team_count = PlayerPokemon.objects.filter(player__user=request.user, in_team=True).count()
        if team_count <= 1:
            return Response({'error': 'No puedes dejar el equipo vacío'}, status=400)

        old_order = pokemon.order

        pokemon.in_team = False
        pokemon.order = 0
        pokemon.save()

        self._reorder_team(request.user.player_profile)

        return Response({
            'message': f'{pokemon.pokemon.name} movido a la reserva',
            'new_team_count': team_count - 1
        })

    @action(detail=True, methods=['post'], url_path='move-to-team')
    def move_to_team(self, request, pk=None):
        player = request.user.player_profile

        try:
            self._check_location(player)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        try:
            pokemon = PlayerPokemon.objects.get(pk=pk, player__user=request.user, in_team=False)
        except PlayerPokemon.DoesNotExist:
            return Response({'error': 'Pokémon no encontrado en tu reserva'}, status=404)

        team_count = PlayerPokemon.objects.filter(player__user=request.user, in_team=True).count()
        if team_count >= 6:
            return Response({'error': 'El equipo está lleno (máximo 6 Pokémon)'}, status=400)

        pokemon.in_team = True
        pokemon.save()

        return Response({
            'message': f'{pokemon.pokemon.name} movido al equipo',
            'new_team_count': team_count + 1,
            'new_order': pokemon.order
        })

    @action(detail=True, methods=['post'], url_path='swap-with-team')
    def swap_with_team(self, request, pk=None):
        player = request.user.player_profile

        try:
            self._check_location(player)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        reserve_pokemon_id = pk
        team_pokemon_id = request.data.get('team_pokemon_id')

        if not team_pokemon_id:
            return Response({'error': 'Se requiere team_pokemon_id'}, status=400)

        try:
            reserve_pokemon = PlayerPokemon.objects.get(
                pk=reserve_pokemon_id,
                player__user=request.user,
                in_team=False
            )
            team_pokemon = PlayerPokemon.objects.get(
                pk=team_pokemon_id,
                player__user=request.user,
                in_team=True
            )
        except PlayerPokemon.DoesNotExist:
            return Response({'error': 'Pokémon no encontrado'}, status=404)

        team_order = team_pokemon.order

        team_pokemon.in_team = False
        team_pokemon.order = 0
        team_pokemon.save()

        reserve_pokemon.in_team = True
        reserve_pokemon.order = team_order
        reserve_pokemon.save()

        return Response({
            'message': f'{reserve_pokemon.pokemon.name} intercambiado con {team_pokemon.pokemon.name}',
            'new_team_member': reserve_pokemon.pokemon.name,
            'to_reserve': team_pokemon.pokemon.name,
            'position': team_order
        })

    @action(detail=True, methods=['get'])
    def available_moves(self, request, pk=None):
        player = request.user.player_profile

        try:
            self._check_location(player)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        try:
            pokemon = PlayerPokemon.objects.get(pk=pk, player__user=request.user)
        except PlayerPokemon.DoesNotExist:
            return Response({'error': 'Pokémon no encontrado'}, status=404)

        available_moves = pokemon.get_available_moves()

        moves_data = []
        for pm in available_moves:
            moves_data.append({
                'id': pm.move.id,
                'name': pm.move.name,
                'level_learned': pm.level,
                'type': pm.move.type,
                'power': pm.move.power,
                'accuracy': pm.move.accuracy,
                'pp': pm.move.pp,
                'damage_class': pm.move.damage_class,
                'already_known': pokemon.moves.filter(id=pm.move.id).exists()
            })

        return Response({
            'pokemon': pokemon.pokemon.name,
            'current_moves': [{'id': m.id, 'name': m.name} for m in pokemon.moves.all()],
            'available_moves': moves_data
        })

    @action(detail=True, methods=['post'], url_path='teach-move')
    def teach_move(self, request, pk=None):
        """Enseñar un nuevo movimiento al Pokémon"""
        player = request.user.player_profile

        # Verificar ubicación
        try:
            self._check_location(player)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        try:
            pokemon = PlayerPokemon.objects.get(pk=pk, player__user=request.user)
        except PlayerPokemon.DoesNotExist:
            return Response({'error': 'Pokémon no encontrado'}, status=404)

        move_id = request.data.get('move_id')
        if not move_id:
            return Response({'error': 'Se requiere move_id'}, status=400)

        try:
            move = Move.objects.get(id=move_id)
            pokemon.teach_move(move)

            return Response({
                'message': f'{pokemon.pokemon.name} aprendió {move.name}',
                'current_moves': [m.name for m in pokemon.moves.all()]
            })

        except Move.DoesNotExist:
            return Response({'error': 'Movimiento no encontrado'}, status=404)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'], url_path='forget-move')
    def forget_move(self, request, pk=None):
        """Olvidar un movimiento del Pokémon"""
        player = request.user.player_profile

        # Verificar ubicación
        try:
            self._check_location(player)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        try:
            pokemon = PlayerPokemon.objects.get(pk=pk, player__user=request.user)
        except PlayerPokemon.DoesNotExist:
            return Response({'error': 'Pokémon no encontrado'}, status=404)

        move_id = request.data.get('move_id')
        if not move_id:
            return Response({'error': 'Se requiere move_id'}, status=400)

        try:
            move = Move.objects.get(id=move_id)

            if not pokemon.moves.filter(id=move.id).exists():
                return Response({'error': 'El Pokémon no conoce ese movimiento'}, status=400)

            if pokemon.moves.count() <= 1:
                return Response({'error': 'El Pokémon debe tener al menos 1 movimiento'}, status=400)

            pokemon.moves.remove(move)

            return Response({
                'message': f'{pokemon.pokemon.name} olvidó {move.name}',
                'current_moves': [m.name for m in pokemon.moves.all()]
            })

        except Move.DoesNotExist:
            return Response({'error': 'Movimiento no encontrado'}, status=404)

    def _reorder_team(self, player):
        team_pokemons = PlayerPokemon.objects.filter(
            player=player,
            in_team=True
        ).order_by('order', 'id')

        for new_order, pokemon in enumerate(team_pokemons):
            if pokemon.order != new_order:
                PlayerPokemon.objects.filter(pk=pokemon.pk).update(order=new_order)

    # En cada método que modifique el equipo, llama a _reorder_team al final

    # Enponts de prueba para agregar Pokémon
    @action(detail=False, methods=['post'])
    def add_test_pokemon(self, request):
        """Endpoint temporal para agregar Pokémon de prueba"""
        player = request.user.player_profile

        # Pokémon disponibles para agregar
        test_pokemon_ids = [16, 19, 10, 13]  # Pidgey, Rattata, Caterpie, Weedle

        pokemon_id = request.data.get('pokemon_id')
        if not pokemon_id:
            return Response({'error': 'Se requiere pokemon_id'}, status=400)

        if pokemon_id not in test_pokemon_ids:
            return Response({'error': 'Pokémon no disponible para prueba'}, status=400)

        try:
            from pokemon.models.Pokemon import Pokemon
            from pokemon.models.PokemonMove import PokemonMove

            # Obtener el Pokémon
            test_pokemon = Pokemon.objects.get(pokedex_id=pokemon_id)

            # Verificar si el jugador ya tiene este Pokémon
            existing_pokemon = player.pokemons.filter(pokemon=test_pokemon).first()
            if existing_pokemon:
                return Response({
                    'message': f'Ya tienes un {test_pokemon.name}',
                    'pokemon_id': existing_pokemon.id
                })

            # Crear el nuevo Pokémon (siempre en reserva inicialmente)
            new_pokemon = PlayerPokemon.objects.create(
                player=player,
                pokemon=test_pokemon,
                level=5,
                experience=0,
                in_team=False,  # Siempre a reserva inicialmente
                order=0  # Orden 0 en reserva
            )

            # Calcular stats
            new_pokemon.calculate_stats()
            new_pokemon.current_hp = new_pokemon.hp
            new_pokemon.save()

            # Aprender movimientos iniciales
            initial_moves = PokemonMove.objects.filter(
                pokemon=test_pokemon,
                level__lte=5
            )[:2]

            for move in initial_moves:
                new_pokemon.moves.add(move.move)

            # Registrar en la Pokédex
            from usuario.models.Pokedex import Pokedex
            Pokedex.objects.get_or_create(
                player=player,
                pokemon=test_pokemon,
                defaults={'state': 'caught'}
            )

            return Response({
                'message': f'{test_pokemon.name} agregado a tu reserva!',
                'pokemon': {
                    'id': new_pokemon.id,
                    'name': test_pokemon.name,
                    'level': new_pokemon.level,
                    'hp': new_pokemon.hp,
                    'current_hp': new_pokemon.current_hp,
                    'in_team': new_pokemon.in_team,
                    'order': new_pokemon.order
                },
                'available_pokemon': test_pokemon_ids
            })

        except Pokemon.DoesNotExist:
            return Response({'error': 'Pokémon no encontrado'}, status=404)
        except Exception as e:
            return Response({'error': f'Error: {str(e)}'}, status=500)

    @action(detail=False, methods=['get'])
    def available_test_pokemon(self, request):
        """Ver Pokémon disponibles para agregar en pruebas"""
        available_pokemon = [
            {'id': 16, 'name': 'Pidgey', 'types': ['normal', 'flying']},
            {'id': 19, 'name': 'Rattata', 'types': ['normal']},
            {'id': 10, 'name': 'Caterpie', 'types': ['bug']},
            {'id': 13, 'name': 'Weedle', 'types': ['bug', 'poison']},
        ]
        return Response({
            'available_pokemon': available_pokemon,
            'instructions': 'Usa POST /api/auth/pokemon-center/add_test_pokemon/ con {"pokemon_id": X}'
        })
