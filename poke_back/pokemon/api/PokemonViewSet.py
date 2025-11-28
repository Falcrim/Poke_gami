from rest_framework import viewsets, permissions, serializers
from pokemon.models.Pokemon import Pokemon
from pokemon.models.PokemonMove import PokemonMove


class PokemonMoveSerializer(serializers.ModelSerializer):
    move_name = serializers.CharField(source='move.name', read_only=True)
    move_type = serializers.CharField(source='move.type', read_only=True)
    move_power = serializers.IntegerField(source='move.power', read_only=True)

    class Meta:
        model = PokemonMove
        fields = ('level', 'move_name', 'move_type', 'move_power')


class PokemonSerializer(serializers.ModelSerializer):
    moves = PokemonMoveSerializer(source='moves_by_level', many=True, read_only=True)
    evolves_to_name = serializers.CharField(source='evolves_to.name', read_only=True, allow_null=True)

    class Meta:
        model = Pokemon
        fields = ('id', 'pokedex_id', 'name', 'type1', 'type2',
                  'base_hp', 'base_attack', 'base_defense',
                  'base_special_attack', 'base_special_defense', 'base_speed',
                  'evolution_level', 'evolves_to', 'evolves_to_name',
                  'sprite_front', 'sprite_back', 'moves')


class PokemonViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Pokemon.objects.all()
    serializer_class = PokemonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Pokemon.objects.all()
        # Filtrar por tipo si se especifica
        pokemon_type = self.request.query_params.get('type')
        if pokemon_type:
            queryset = queryset.filter(type1=pokemon_type) | queryset.filter(type2=pokemon_type)
        return queryset