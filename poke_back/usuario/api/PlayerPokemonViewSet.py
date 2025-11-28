# usuario/api/PlayerPokemonViewSet.py - VERSIÓN MEJORADA
from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from usuario.models.PlayerPokemon import PlayerPokemon
from pokemon.models.Move import Move


class PlayerPokemonSerializer(serializers.ModelSerializer):
    pokemon_name = serializers.CharField(source='pokemon.name', read_only=True)
    pokemon_types = serializers.SerializerMethodField()
    sprite_front = serializers.URLField(source='pokemon.sprite_front', read_only=True)
    sprite_back = serializers.URLField(source='pokemon.sprite_back', read_only=True)
    moves_details = serializers.SerializerMethodField()
    available_moves = serializers.SerializerMethodField()

    class Meta:
        model = PlayerPokemon
        fields = ('id', 'pokemon', 'pokemon_name', 'pokemon_types', 'nickname', 'level',
                  'current_hp', 'hp', 'attack', 'defense', 'special_attack', 'special_defense',
                  'speed', 'experience', 'sprite_front', 'sprite_back', 'moves', 'moves_details',
                  'available_moves')
        read_only_fields = ('moves',)

    def get_pokemon_types(self, obj):
        types = [obj.pokemon.type1]
        if obj.pokemon.type2:
            types.append(obj.pokemon.type2)
        return types

    def get_moves_details(self, obj):
        return [{
            'id': move.id,
            'name': move.name,
            'type': move.type,
            'power': move.power,
            'accuracy': move.accuracy,
            'pp': move.pp,
            'damage_class': move.damage_class,
            'current_pp': move.pp
        } for move in obj.moves.all()]

    def get_available_moves(self, obj):
        available_moves = obj.get_available_moves()
        return [{
            'id': pm.move.id,
            'name': pm.move.name,
            'level_learned': pm.level,
            'type': pm.move.type,
            'power': pm.move.power,
            'accuracy': pm.move.accuracy,
            'pp': pm.move.pp,
            'damage_class': pm.move.damage_class,
            'already_known': obj.moves.filter(id=pm.move.id).exists()
        } for pm in available_moves]


class PlayerPokemonViewSet(viewsets.ModelViewSet):
    serializer_class = PlayerPokemonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PlayerPokemon.objects.filter(player__user=self.request.user)

    @action(detail=True, methods=['post'])
    def teach_move(self, request, pk=None):
        player_pokemon = self.get_object()
        move_id = request.data.get('move_id')

        try:
            move = Move.objects.get(id=move_id)

            player_pokemon.teach_move(move)

            return Response({
                'message': f'{player_pokemon.pokemon.name} aprendió {move.name}',
                'moves': [m.name for m in player_pokemon.moves.all()]
            })

        except Move.DoesNotExist:
            return Response({'error': 'Movimiento no encontrado'}, status=404)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

    @action(detail=True, methods=['post'])
    def replace_move(self, request, pk=None):
        player_pokemon = self.get_object()
        old_move_id = request.data.get('old_move_id')
        new_move_id = request.data.get('new_move_id')

        try:
            old_move = Move.objects.get(id=old_move_id)
            new_move = Move.objects.get(id=new_move_id)

            if not player_pokemon.moves.filter(id=old_move.id).exists():
                return Response({'error': 'El Pokémon no conoce ese movimiento'}, status=400)

            if not player_pokemon.can_learn_move(new_move):
                return Response({'error': f'No puede aprender {new_move.name}'}, status=400)

            player_pokemon.moves.remove(old_move)
            player_pokemon.moves.add(new_move)

            return Response({
                'message': f'Reemplazado {old_move.name} por {new_move.name}',
                'moves': [m.name for m in player_pokemon.moves.all()]
            })

        except Move.DoesNotExist:
            return Response({'error': 'Movimiento no encontrado'}, status=404)

    @action(detail=True, methods=['post'])
    def forget_move(self, request, pk=None):
        player_pokemon = self.get_object()
        move_id = request.data.get('move_id')

        try:
            move = Move.objects.get(id=move_id)

            if player_pokemon.moves.count() <= 1:
                return Response({'error': 'El Pokémon debe tener al menos 1 movimiento'}, status=400)

            if not player_pokemon.moves.filter(id=move.id).exists():
                return Response({'error': 'El Pokémon no conoce ese movimiento'}, status=400)

            player_pokemon.moves.remove(move)
            return Response({
                'message': f'Olvidado: {move.name}',
                'moves': [m.name for m in player_pokemon.moves.all()]
            })

        except Move.DoesNotExist:
            return Response({'error': 'Movimiento no encontrado'}, status=404)

    @action(detail=True, methods=['post'])
    def heal(self, request, pk=None):
        player_pokemon = self.get_object()
        player_pokemon.current_hp = player_pokemon.hp
        player_pokemon.save()
        return Response({
            'message': f'{player_pokemon.pokemon.name} curado completamente',
            'current_hp': player_pokemon.current_hp,
            'max_hp': player_pokemon.hp
        })