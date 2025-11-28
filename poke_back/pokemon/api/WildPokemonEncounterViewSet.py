from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
import random
from pokemon.models.WildPokemonEncounter import WildPokemonEncounter
from usuario.models.PlayerPokemon import PlayerPokemon
from usuario.models.Pokedex import Pokedex


class WildPokemonEncounterSerializer(serializers.ModelSerializer):
    pokemon_name = serializers.CharField(source='pokemon.name', read_only=True)
    pokemon_types = serializers.SerializerMethodField()
    sprite_front = serializers.URLField(source='pokemon.sprite_front', read_only=True)

    class Meta:
        model = WildPokemonEncounter
        fields = ('id', 'location', 'pokemon', 'pokemon_name', 'pokemon_types',
                  'sprite_front', 'min_level', 'max_level', 'rarity')

    def get_pokemon_types(self, obj):
        types = [obj.pokemon.type1]
        if obj.pokemon.type2:
            types.append(obj.pokemon.type2)
        return types


class WildPokemonEncounterViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WildPokemonEncounter.objects.all()
    serializer_class = WildPokemonEncounterSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = WildPokemonEncounter.objects.all()
        location_id = self.request.query_params.get('location_id')
        if location_id:
            queryset = queryset.filter(location_id=location_id)
        return queryset

    @action(detail=False, methods=['post'])
    def encounter(self, request):
        player = request.user.player_profile
        location_id = request.data.get('location_id')

        if not location_id:
            return Response({'error': 'Se requiere location_id'}, status=400)

        # Obtener encuentros posibles en esta ubicación
        encounters = WildPokemonEncounter.objects.filter(location_id=location_id)
        if not encounters.exists():
            return Response({'error': 'No hay Pokémon en esta ubicación'}, status=400)

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

        if not weighted_encounters:
            return Response({'error': 'No se pudo generar encuentro'}, status=400)

        # Seleccionar Pokémon aleatorio
        selected_encounter = random.choice(weighted_encounters)
        level = random.randint(selected_encounter.min_level, selected_encounter.max_level)

        # Registrar en pokédex como visto
        Pokedex.objects.get_or_create(
            player=player,
            pokemon=selected_encounter.pokemon,
            defaults={'state': 'seen'}
        )

        return Response({
            'pokemon': {
                'id': selected_encounter.pokemon.id,
                'name': selected_encounter.pokemon.name,
                'level': level,
                'types': [selected_encounter.pokemon.type1,
                          selected_encounter.pokemon.type2] if selected_encounter.pokemon.type2 else [
                    selected_encounter.pokemon.type1],
                'sprite_front': selected_encounter.pokemon.sprite_front,
                'current_hp': 0,  # Se calculará en el frontend
                'max_hp': 0,  # Se calculará en el frontend
                'moves': []  # Se poblará con movimientos por nivel
            },
            'encounter_id': selected_encounter.id
        })