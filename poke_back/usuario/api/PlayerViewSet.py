from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from usuario.models.Player import Player
from pokemon.models.Location import Location
from pokemon.models.Pokemon import Pokemon


class PlayerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    current_location_name = serializers.CharField(source='current_location.name', read_only=True)
    current_location_type = serializers.CharField(source='current_location.location_type', read_only=True)
    connected_locations = serializers.SerializerMethodField()

    class Meta:
        model = Player
        fields = ('id', 'username', 'current_location', 'current_location_name',
                  'current_location_type', 'money', 'starter_chosen', 'connected_locations')

    def get_connected_locations(self, obj):
        if obj.current_location:
            connected_locations = obj.current_location.connected_locations.all()
            return [{
                'id': loc.id,
                'name': loc.name,
                'type': loc.location_type
            } for loc in connected_locations]
        return []


class PlayerViewSet(viewsets.ModelViewSet):
    serializer_class = PlayerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Player.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def choose_starter(self, request):
        player = self.get_queryset().first()
        if player.starter_chosen:
            return Response({'error': 'Ya elegiste tu Pokémon inicial'}, status=400)

        starter_id = request.data.get('starter_id')
        if starter_id not in [1, 4, 7]:
            return Response({'error': 'Pokémon inicial inválido'}, status=400)

        try:
            from pokemon.models.Pokemon import Pokemon
            from usuario.models.PlayerPokemon import PlayerPokemon
            from pokemon.models.PokemonMove import PokemonMove
            from usuario.models.Pokedex import Pokedex

            starter_pokemon = Pokemon.objects.get(pokedex_id=starter_id)

            player_pokemon = PlayerPokemon.objects.create(
                player=player,
                pokemon=starter_pokemon,
                level=5,
                experience=0
            )

            player_pokemon.calculate_stats()
            player_pokemon.current_hp = player_pokemon.hp
            player_pokemon.save()

            initial_moves = PokemonMove.objects.filter(
                pokemon=starter_pokemon,
                level__lte=5
            )[:2]

            for pokemon_move in initial_moves:
                player_pokemon.moves.add(pokemon_move.move)

            player.starter_chosen = True

            from pokemon.models.Location import Location
            starting_location = Location.objects.get(name='Pueblo Paleta')
            player.current_location = starting_location
            player.save()

            Pokedex.objects.create(
                player=player,
                pokemon=starter_pokemon,
                state='caught'
            )

            connected_locations = starting_location.connected_locations.all()
            connected_locations_data = [{
                'id': loc.id,
                'name': loc.name,
                'type': loc.location_type
            } for loc in connected_locations]

            return Response({
                'message': f'Pokémon inicial {starter_pokemon.name} elegido y agregado a tu equipo!',
                'pokemon': {
                    'id': player_pokemon.id,
                    'name': starter_pokemon.name,
                    'level': player_pokemon.level,
                    'hp': player_pokemon.hp,
                    'current_hp': player_pokemon.current_hp
                },
                'current_location': {
                    'id': starting_location.id,
                    'name': starting_location.name,
                    'type': starting_location.location_type
                },
                'connected_locations': connected_locations_data
            })

        except Pokemon.DoesNotExist:
            return Response({'error': 'Pokémon inicial no encontrado'}, status=404)
        except Exception as e:
            return Response({'error': f'Error al crear Pokémon inicial: {str(e)}'}, status=500)

    @action(detail=False, methods=['post'])
    def travel(self, request):
        player = self.get_queryset().first()
        location_id = request.data.get('location_id')

        try:
            new_location = Location.objects.get(id=location_id)
            current_location = player.current_location

            if current_location and new_location not in current_location.connected_locations.all():
                return Response({'error': 'Ubicación no accesible'}, status=400)

            player.current_location = new_location
            player.save()

            connected_locations = new_location.connected_locations.all()
            connected_locations_data = [{
                'id': loc.id,
                'name': loc.name,
                'type': loc.location_type
            } for loc in connected_locations]

            return Response({
                'message': f'Viajaste a {new_location.name}',
                'current_location': {
                    'id': new_location.id,
                    'name': new_location.name,
                    'type': new_location.location_type
                },
                'connected_locations': connected_locations_data
            })

        except Location.DoesNotExist:
            return Response({'error': 'Ubicación no encontrada'}, status=404)

    @action(detail=False, methods=['get'])
    def current_location(self, request):
        player = self.get_queryset().first()

        if not player.current_location:
            return Response({'error': 'No estás en ninguna ubicación'}, status=404)

        current_loc = player.current_location
        connected_locations = current_loc.connected_locations.all()

        connected_locations_data = [{
            'id': loc.id,
            'name': loc.name,
            'type': loc.location_type
        } for loc in connected_locations]

        return Response({
            'current_location': {
                'id': current_loc.id,
                'name': current_loc.name,
                'type': current_loc.location_type
            },
            'connected_locations': connected_locations_data
        })

