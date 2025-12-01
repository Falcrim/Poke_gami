from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from usuario.models.Trainer import Trainer
from pokemon.models.Location import Location
from pokemon.models.WildPokemonEncounter import WildPokemonEncounter


class TrainerSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source='location.name', read_only=True)

    class Meta:
        model = Trainer
        fields = ('id', 'name', 'trainer_type', 'location', 'location_name',
                  'sprite', 'dialogue_before', 'dialogue_after', 'money_reward',
                  'min_level', 'max_level', 'team_size')


class TrainerViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TrainerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Solo mostrar entrenadores en la ubicación actual del jugador
        player = self.request.user.player_profile
        if player.current_location:
            return Trainer.objects.filter(location=player.current_location)
        return Trainer.objects.none()

    @action(detail=True, methods=['post'])
    def challenge(self, request, pk=None):
        """Desafiar a un entrenador a un combate"""
        player = request.user.player_profile
        trainer = self.get_object()

        # Verificar que el jugador esté en la misma ubicación
        if player.current_location != trainer.location:
            return Response({'error': 'El entrenador no está en tu ubicación actual'}, status=400)

        # Verificar que es una ruta (no pueblo)
        if trainer.location.location_type != 'route':
            return Response({'error': 'Solo puedes combatir con entrenadores en rutas'}, status=400)

        # Verificar que el jugador tiene Pokémon vivos
        active_pokemon = player.pokemons.filter(in_team=True, current_hp__gt=0).order_by('order').first()
        if not active_pokemon:
            return Response({'error': 'No tienes Pokémon disponibles para combatir'}, status=400)

        # Generar equipo del entrenador
        trainer_team = trainer.generate_team()
        if not trainer_team:
            return Response({'error': 'No se pudo generar el equipo del entrenador'}, status=400)

        # Convertir equipo a formato JSON serializable
        serializable_team = []
        for pokemon_data in trainer_team:
            pokemon_dict = {
                'pokemon_id': pokemon_data['pokemon'].id,
                'pokemon_name': pokemon_data['pokemon'].name,
                'level': pokemon_data['level'],
                'current_hp': pokemon_data['current_hp'],
                'max_hp': pokemon_data['max_hp'],
                'attack': pokemon_data['attack'],
                'defense': pokemon_data['defense'],
                'special_attack': pokemon_data['special_attack'],
                'special_defense': pokemon_data['special_defense'],
                'speed': pokemon_data['speed'],
                'type1': pokemon_data['type1'],
                'type2': pokemon_data.get('type2'),
                'sprite_front': pokemon_data['pokemon'].sprite_front,
                'sprite_back': pokemon_data['pokemon'].sprite_back,
                'moves': [
                    {
                        'id': move.id,
                        'name': move.name,
                        'type': move.type,
                        'power': move.power,
                        'accuracy': move.accuracy,
                        'pp': move.pp,
                        'damage_class': move.damage_class
                    } for move in pokemon_data['moves']
                ]
            }
            serializable_team.append(pokemon_dict)

        # Crear la batalla
        from usuario.models.Battle import Battle
        battle = Battle.objects.create(
            battle_type='trainer',
            player=player,
            trainer=trainer,
            trainer_team=serializable_team,
            current_trainer_pokemon_index=0,
            player_pokemon=active_pokemon,
            state='active',
            turn=0  # Empieza el jugador
        )

        return Response({
            'battle_id': battle.id,
            'message': f'{trainer.dialogue_before or f"{trainer.name} te desafía a un combate!"}',
            'trainer': {
                'id': trainer.id,
                'name': trainer.name,
                'type': trainer.trainer_type,
                'sprite': trainer.sprite,
                'team_size': len(serializable_team)
            },
            'opponent_pokemon': serializable_team[0] if serializable_team else None,
            'player_pokemon': {
                'id': active_pokemon.id,
                'name': active_pokemon.pokemon.name,
                'level': active_pokemon.level,
                'current_hp': active_pokemon.current_hp,
                'max_hp': active_pokemon.hp,
                'moves': [{'id': move.id, 'name': move.name} for move in active_pokemon.moves.all()]
            }
        })

    @action(detail=False, methods=['get'])
    def available_in_location(self, request):
        """Obtener entrenadores disponibles en la ubicación actual"""
        player = request.user.player_profile

        if not player.current_location:
            return Response({'trainers': []})

        trainers = Trainer.objects.filter(location=player.current_location)
        serializer = self.get_serializer(trainers, many=True)

        return Response({
            'location': player.current_location.name,
            'location_type': player.current_location.location_type,
            'trainers': serializer.data
        })
