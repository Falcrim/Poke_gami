from rest_framework import viewsets, permissions, serializers
from pokemon.models.Location import Location
from pokemon.models.WildPokemonEncounter import WildPokemonEncounter


class WildPokemonEncounterSerializer(serializers.ModelSerializer):
    pokemon_name = serializers.CharField(source='pokemon.name', read_only=True)
    pokemon_types = serializers.SerializerMethodField()

    class Meta:
        model = WildPokemonEncounter
        fields = ('id', 'pokemon', 'pokemon_name', 'pokemon_types', 'min_level', 'max_level', 'rarity')

    def get_pokemon_types(self, obj):
        types = [obj.pokemon.type1]
        if obj.pokemon.type2:
            types.append(obj.pokemon.type2)
        return types


class LocationSerializer(serializers.ModelSerializer):
    connected_locations = serializers.SerializerMethodField()
    wild_pokemons = WildPokemonEncounterSerializer(many=True, read_only=True)

    class Meta:
        model = Location
        fields = ('id', 'name', 'location_type', 'connected_locations', 'wild_pokemons')

    def get_connected_locations(self, obj):
        return [{'id': loc.id, 'name': loc.name, 'type': loc.location_type}
                for loc in obj.connected_locations.all()]


class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated]