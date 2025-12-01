from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from usuario.models.PlayerPokemon import PlayerPokemon


class TeamOrderViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def _get_ordered_team(self, player):
        return player.pokemons.filter(in_team=True).order_by('order', 'id')

    @action(detail=False, methods=['get'])
    def get_team_order(self, request):
        player = request.user.player_profile
        team_pokemons = self._get_ordered_team(player)

        from usuario.api.PlayerPokemonViewSet import PlayerPokemonSerializer
        serializer = PlayerPokemonSerializer(team_pokemons, many=True)

        return Response({
            'team': serializer.data,
            'team_count': team_pokemons.count(),
            'max_team_size': 6
        })

    @action(detail=False, methods=['post'])
    def update_order(self, request):
        """Actualizar el orden completo del equipo"""
        player = request.user.player_profile
        new_order_ids = request.data.get('new_order')  # Lista de IDs en el nuevo orden

        if not new_order_ids or not isinstance(new_order_ids, list):
            return Response({'error': 'Se requiere new_order como lista de IDs'}, status=400)

        # Verificar que todos los Pokémon pertenecen al jugador y están en el equipo
        team_pokemons = self._get_ordered_team(player)
        if len(new_order_ids) != team_pokemons.count():
            return Response({'error': 'La cantidad de Pokémon no coincide con el equipo actual'}, status=400)

        # Verificar que todos los IDs son válidos
        valid_ids = set(team_pokemons.values_list('id', flat=True))
        if set(new_order_ids) != valid_ids:
            return Response({'error': 'IDs de Pokémon inválidos'}, status=400)

        # Actualizar los órdenes
        for position, pokemon_id in enumerate(new_order_ids):
            PlayerPokemon.objects.filter(
                id=pokemon_id,
                player=player
            ).update(order=position)

        # Reordenar para asegurar consistencia
        self._reorder_team(player)

        return Response({
            'message': 'Orden del equipo actualizado correctamente',
            'new_order': new_order_ids
        })

    @action(detail=True, methods=['post'])
    def move_to_position(self, request, pk=None):
        """Mover un Pokémon a una posición específica"""
        player = request.user.player_profile
        new_position = request.data.get('position')

        if new_position is None or new_position < 0 or new_position > 5:
            return Response({'error': 'Posición inválida (debe ser 0-5)'}, status=400)

        try:
            pokemon = PlayerPokemon.objects.get(pk=pk, player=player, in_team=True)
        except PlayerPokemon.DoesNotExist:
            return Response({'error': 'Pokémon no encontrado en tu equipo'}, status=404)

        # Obtener equipo actual
        team_pokemons = list(self._get_ordered_team(player).exclude(pk=pk))

        # Insertar en la nueva posición
        if new_position >= len(team_pokemons):
            team_pokemons.append(pokemon)
        else:
            team_pokemons.insert(new_position, pokemon)

        # Actualizar todos los órdenes
        for order, p in enumerate(team_pokemons):
            PlayerPokemon.objects.filter(pk=p.pk).update(order=order)

        # Reordenar para asegurar consistencia
        self._reorder_team(player)

        new_order_ids = [p.id for p in self._get_ordered_team(player)]

        return Response({
            'message': f'{pokemon.pokemon.name} movido a la posición {new_position}',
            'new_order': new_order_ids
        })

    @action(detail=True, methods=['post'])
    def swap_positions(self, request, pk=None):
        """Intercambiar posiciones entre dos Pokémon"""
        player = request.user.player_profile
        other_pokemon_id = request.data.get('other_pokemon_id')

        if not other_pokemon_id:
            return Response({'error': 'Se requiere other_pokemon_id'}, status=400)

        try:
            pokemon1 = PlayerPokemon.objects.get(pk=pk, player=player, in_team=True)
            pokemon2 = PlayerPokemon.objects.get(pk=other_pokemon_id, player=player, in_team=True)
        except PlayerPokemon.DoesNotExist:
            return Response({'error': 'Uno o ambos Pokémon no encontrados en tu equipo'}, status=404)

        # Intercambiar órdenes temporalmente
        temp_order = 999  # Valor temporal alto
        PlayerPokemon.objects.filter(pk=pokemon1.pk).update(order=temp_order)
        PlayerPokemon.objects.filter(pk=pokemon2.pk).update(order=pokemon1.order)
        PlayerPokemon.objects.filter(pk=pokemon1.pk).update(order=pokemon2.order)

        # Reordenar para asegurar consistencia
        self._reorder_team(player)

        return Response({
            'message': f'{pokemon1.pokemon.name} y {pokemon2.pokemon.name} intercambiados de posición',
            'new_order': [p.id for p in self._get_ordered_team(player)]
        })

    @action(detail=False, methods=['post'])
    def fix_team_order(self, request):
        """Forzar la corrección del orden del equipo (útil para debugging)"""
        player = request.user.player_profile
        self._reorder_team(player)

        team_pokemons = self._get_ordered_team(player)
        return Response({
            'message': 'Orden del equipo corregido',
            'current_order': [p.id for p in team_pokemons]
        })

    def _reorder_team(self, player):
        """Reordenar el equipo para órdenes consecutivos"""
        team_pokemons = PlayerPokemon.objects.filter(
            player=player,
            in_team=True
        ).order_by('order', 'id')

        for new_order, pokemon in enumerate(team_pokemons):
            if pokemon.order != new_order:
                PlayerPokemon.objects.filter(pk=pokemon.pk).update(order=new_order)