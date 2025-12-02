from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response

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
        pokemon_type = self.request.query_params.get('type')
        if pokemon_type:
            queryset = queryset.filter(type1=pokemon_type) | queryset.filter(type2=pokemon_type)
        return queryset

    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def starters(self, request):
        starters = Pokemon.objects.filter(pokedex_id__in=[1, 4, 7])

        starter_data = []
        for starter in starters:
            initial_moves = PokemonMove.objects.filter(
                pokemon=starter,
                level__lte=5
            )[:4]

            moves_data = []
            for move in initial_moves:
                moves_data.append({
                    'name': move.move.name,
                    'type': move.move.type,
                    'power': move.move.power,
                    'accuracy': move.move.accuracy,
                    'pp': move.move.pp,
                    'damage_class': move.move.damage_class,
                    'level_learned': move.level
                })

            evolved_pokemon = Pokemon.objects.filter(evolves_from=starter).first()

            starter_data.append({
                'id': starter.id,
                'pokedex_id': starter.pokedex_id,
                'name': starter.name,
                'types': [starter.type1, starter.type2] if starter.type2 else [starter.type1],
                'sprite_front': starter.sprite_front,
                'sprite_back': starter.sprite_back,
                'base_stats': {
                    'hp': starter.base_hp,
                    'attack': starter.base_attack,
                    'defense': starter.base_defense,
                    'special_attack': starter.base_special_attack,
                    'special_defense': starter.base_special_defense,
                    'speed': starter.base_speed
                },
                'initial_moves': moves_data,
                'evolution': {
                    'evolves_to': evolved_pokemon.name if evolved_pokemon else None,
                    'evolution_level': evolved_pokemon.evolution_level if evolved_pokemon else None
                } if evolved_pokemon else None
            })

        return Response(starter_data)