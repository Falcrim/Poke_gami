from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from usuario.models.Player import Player
from pokemon.models.Location import Location
from pokemon.models.Pokemon import Pokemon


class PlayerSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    current_location_name = serializers.CharField(source='current_location.name', read_only=True)

    class Meta:
        model = Player
        fields = ('id', 'username', 'current_location', 'current_location_name', 'money', 'starter_chosen')


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
        if starter_id not in [1, 4, 7]:  # Bulbasaur, Charmander, Squirtle
            return Response({'error': 'Pokémon inicial inválido'}, status=400)

        try:
            from pokemon.models.Pokemon import Pokemon
            from usuario.models.PlayerPokemon import PlayerPokemon
            from pokemon.models.PokemonMove import PokemonMove
            from usuario.models.Pokedex import Pokedex

            starter_pokemon = Pokemon.objects.get(pokedex_id=starter_id)

            # Crear el Pokémon del jugador
            player_pokemon = PlayerPokemon.objects.create(
                player=player,
                pokemon=starter_pokemon,
                level=5,  # Nivel inicial
                experience=0
            )

            # Los stats se calculan automáticamente en el save()
            # Solo aseguramos que current_hp esté lleno
            player_pokemon.current_hp = player_pokemon.hp
            player_pokemon.save()

            # Aprender movimientos iniciales (nivel <= 5)
            initial_moves = PokemonMove.objects.filter(
                pokemon=starter_pokemon,
                level__lte=5
            )[:2]  # Solo 2 movimientos iniciales para evitar problemas

            for pokemon_move in initial_moves:
                player_pokemon.moves.add(pokemon_move.move)

            # Marcar como elegido
            player.starter_chosen = True

            # Establecer ubicación inicial (Pueblo Paleta)
            from pokemon.models.Location import Location
            try:
                starting_location = Location.objects.get(name='Pueblo Paleta')
                player.current_location = starting_location
            except Location.DoesNotExist:
                # Si no existe, usar la primera ubicación
                starting_location = Location.objects.first()
                if starting_location:
                    player.current_location = starting_location

            player.save()

            # Registrar en la pokédex
            Pokedex.objects.get_or_create(
                player=player,
                pokemon=starter_pokemon,
                defaults={'state': 'caught'}
            )

            return Response({
                'message': f'Pokémon inicial {starter_pokemon.name} elegido y agregado a tu equipo!',
                'pokemon': {
                    'id': player_pokemon.id,
                    'name': starter_pokemon.name,
                    'level': player_pokemon.level,
                    'hp': player_pokemon.hp,
                    'current_hp': player_pokemon.current_hp
                }
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

            return Response({
                'message': f'Viajaste a {new_location.name}',
                'new_location': new_location.name,
                'location_type': new_location.location_type
            })

        except Location.DoesNotExist:
            return Response({'error': 'Ubicación no encontrada'}, status=404)
