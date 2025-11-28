from rest_framework import viewsets, permissions, serializers
from pokemon.models.PokemonMove import PokemonMove

class PokemonMoveSerializer(serializers.ModelSerializer):
    pokemon_name = serializers.CharField(source='pokemon.name', read_only=True)
    move_name = serializers.CharField(source='move.name', read_only=True)
    move_type = serializers.CharField(source='move.type', read_only=True)
    move_power = serializers.IntegerField(source='move.power', read_only=True)
    move_accuracy = serializers.IntegerField(source='move.accuracy', read_only=True)
    move_pp = serializers.IntegerField(source='move.pp', read_only=True)

    class Meta:
        model = PokemonMove
        fields = ('id', 'pokemon', 'pokemon_name', 'move', 'move_name', 'move_type',
                 'move_power', 'move_accuracy', 'move_pp', 'level')

class PokemonMoveViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PokemonMove.objects.all()
    serializer_class = PokemonMoveSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = PokemonMove.objects.all()
        pokemon_id = self.request.query_params.get('pokemon_id')
        if pokemon_id:
            queryset = queryset.filter(pokemon_id=pokemon_id)
        return queryset