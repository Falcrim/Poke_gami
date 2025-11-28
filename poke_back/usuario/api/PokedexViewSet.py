from rest_framework import viewsets, permissions, serializers
from usuario.models.Pokedex import Pokedex
from pokemon.models.Pokemon import Pokemon


class PokedexSerializer(serializers.ModelSerializer):
    pokemon_name = serializers.CharField(source='pokemon.name', read_only=True)
    pokemon_types = serializers.SerializerMethodField()
    sprite_front = serializers.URLField(source='pokemon.sprite_front', read_only=True)
    evolves_to_name = serializers.CharField(source='pokemon.evolves_to.name', read_only=True, allow_null=True)

    class Meta:
        model = Pokedex
        fields = ('id', 'pokemon', 'pokemon_name', 'pokemon_types', 'sprite_front',
                  'state', 'date_registered', 'evolves_to_name')

    def get_pokemon_types(self, obj):
        types = [obj.pokemon.type1]
        if obj.pokemon.type2:
            types.append(obj.pokemon.type2)
        return types


class PokedexViewSet(viewsets.ModelViewSet):
    serializer_class = PokedexSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Pokedex.objects.filter(player__user=self.request.user)

    def create(self, request, *args, **kwargs):
        # Para registrar un Pokémon en la pokédex (visto o capturado)
        player = request.user.player_profile
        pokemon_id = request.data.get('pokemon_id')
        state = request.data.get('state', 'seen')  # 'seen' or 'caught'

        try:
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