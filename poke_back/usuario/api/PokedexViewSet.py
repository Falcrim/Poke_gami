from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response

from usuario.models.Pokedex import Pokedex
from pokemon.models.WildPokemonEncounter import WildPokemonEncounter
from pokemon.models.Pokemon import Pokemon


class PokedexSerializer(serializers.ModelSerializer):
    pokemon_name = serializers.CharField(source='pokemon.name', read_only=True)
    pokemon_types = serializers.SerializerMethodField()
    sprite_front = serializers.URLField(source='pokemon.sprite_front', read_only=True)
    evolution_info = serializers.SerializerMethodField()
    locations = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    class Meta:
        model = Pokedex
        fields = ('id', 'pokemon', 'pokemon_name', 'pokemon_types', 'sprite_front',
                  'state', 'date_registered', 'evolution_info', 'locations', 'description')

    def get_pokemon_types(self, obj):
        types = [obj.pokemon.type1]
        if obj.pokemon.type2:
            types.append(obj.pokemon.type2)
        return types

    def get_evolution_info(self, obj):
        """Obtener información completa de la evolución"""
        pokemon = obj.pokemon

        # Si este Pokémon evoluciona de otro
        evolves_from = None
        if pokemon.evolves_from:
            evolves_from = {
                'id': pokemon.evolves_from.id,
                'name': pokemon.evolves_from.name,
                'pokedex_id': pokemon.evolves_from.pokedex_id
            }

        # CORRECCIÓN: Buscar qué Pokémon evoluciona desde este
        evolves_to = None
        evolved_pokemon = Pokemon.objects.filter(evolves_from=pokemon).first()
        if evolved_pokemon:
            evolves_to = {
                'id': evolved_pokemon.id,
                'name': evolved_pokemon.name,
                'pokedex_id': evolved_pokemon.pokedex_id,
                'evolution_level': evolved_pokemon.evolution_level
            }

        return {
            'evolves_from': evolves_from,
            'evolves_to': evolves_to
        }

    def get_locations(self, obj):
        """Obtener todas las rutas donde aparece este Pokémon"""
        try:
            encounters = WildPokemonEncounter.objects.filter(pokemon=obj.pokemon)
            locations = []

            for encounter in encounters:
                locations.append({
                    'location_id': encounter.location.id,
                    'location_name': encounter.location.name,
                    'location_type': encounter.location.location_type,
                    'min_level': encounter.min_level,
                    'max_level': encounter.max_level,
                    'rarity': encounter.rarity,
                    'rarity_display': encounter.get_rarity_display()
                })

            return locations
        except Exception as e:
            return []

    def get_description(self, obj):
        """Generar descripción del Pokémon con información de rutas"""
        pokemon = obj.pokemon

        # Obtener rutas donde aparece
        encounters = WildPokemonEncounter.objects.filter(pokemon=pokemon)
        route_names = [encounter.location.name for encounter in encounters]

        if route_names:
            routes_text = ", ".join(sorted(set(route_names)))
            description = f"Puede ser encontrado en: {routes_text}"
        else:
            description = "Este Pokémon no aparece en rutas salvajes"

        # Agregar información de evolución si existe
        evolved_pokemon = Pokemon.objects.filter(evolves_from=pokemon).first()
        if evolved_pokemon and evolved_pokemon.evolution_level:
            description += f". Evoluciona a {evolved_pokemon.name} al nivel {evolved_pokemon.evolution_level}"

        return description


class PokedexViewSet(viewsets.ModelViewSet):
    serializer_class = PokedexSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Pokedex.objects.filter(player__user=self.request.user)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Obtener estadísticas de la Pokédex"""
        player = request.user.player_profile
        total_pokemon = 151  # Pokémon de Kanto

        pokedex_entries = Pokedex.objects.filter(player=player)
        seen_count = pokedex_entries.count()
        caught_count = pokedex_entries.filter(state='caught').count()

        return Response({
            'total_pokemon': total_pokemon,
            'seen': seen_count,
            'caught': caught_count,
            'completion_percentage': round((caught_count / total_pokemon) * 100, 2)
        })

    def create(self, request, *args, **kwargs):
        player = request.user.player_profile
        pokemon_id = request.data.get('pokemon_id')
        state = request.data.get('state', 'seen')

        try:
            from pokemon.models.Pokemon import Pokemon
            pokemon = Pokemon.objects.get(id=pokemon_id)

            pokedex_entry, created = Pokedex.objects.get_or_create(
                player=player,
                pokemon=pokemon,
                defaults={'state': state}
            )

            if not created and state == 'caught':
                pokedex_entry.state = 'caught'
                pokedex_entry.save()

            serializer = self.get_serializer(pokedex_entry)
            return Response(serializer.data)

        except Pokemon.DoesNotExist:
            return Response({'error': 'Pokémon no encontrado'}, status=404)