from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from usuario.models.Bag import Bag
from usuario.models.PlayerPokemon import PlayerPokemon


class BagItemsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'])
    def use_potion(self, request):
        player = request.user.player_profile
        bag = Bag.objects.get(player=player)
        pokemon_id = request.data.get('pokemon_id')
        potion_type = request.data.get('potion_type', 'potion')

        if not pokemon_id:
            return Response({'error': 'Se requiere pokemon_id'}, status=400)

        try:
            pokemon = PlayerPokemon.objects.get(pk=pokemon_id, player=player)
        except PlayerPokemon.DoesNotExist:
            return Response({'error': 'Pokémon no encontrado'}, status=404)

        if pokemon.current_hp >= pokemon.hp:
            return Response({'error': 'El Pokémon ya tiene toda su salud'}, status=400)

        heal_amounts = {
            'potion': 20,
            'super_potion': 50,
            'hyper_potion': 200
        }

        if potion_type not in heal_amounts:
            return Response({'error': 'Tipo de poción inválido'}, status=400)

        if not bag.use_item(potion_type):
            return Response({'error': f'No tienes {potion_type}s disponibles'}, status=400)

        new_hp = min(pokemon.current_hp + heal_amounts[potion_type], pokemon.hp)
        pokemon.current_hp = new_hp
        pokemon.save()

        return Response({
            'message': f'Usaste una {potion_type} en {pokemon.pokemon.name}',
            'healed': new_hp - pokemon.current_hp,
            'current_hp': pokemon.current_hp,
            'max_hp': pokemon.hp,
            'bag': bag.get_summary()
        })

    @action(detail=False, methods=['get'])
    def available_items(self, request):
        player = request.user.player_profile
        bag = Bag.objects.get(player=player)

        items = []

        # Pokéballs
        if bag.pokeballs > 0:
            items.append({
                'type': 'pokeball',
                'name': 'Pokéball',
                'count': bag.pokeballs,
                'description': 'Para capturar Pokémon salvajes'
            })

        if bag.ultra_balls > 0:
            items.append({
                'type': 'ultra_ball',
                'name': 'Ultraball',
                'count': bag.ultra_balls,
                'description': 'Mayor probabilidad de captura'
            })

        # Pociones
        if bag.potions > 0:
            items.append({
                'type': 'potion',
                'name': 'Poción',
                'count': bag.potions,
                'description': 'Cura 20 HP',
                'heal_amount': 20
            })

        if bag.super_potions > 0:
            items.append({
                'type': 'super_potion',
                'name': 'Superpoción',
                'count': bag.super_potions,
                'description': 'Cura 50 HP',
                'heal_amount': 50
            })

        if bag.hyper_potions > 0:
            items.append({
                'type': 'hyper_potion',
                'name': 'Hiperpoción',
                'count': bag.hyper_potions,
                'description': 'Cura 200 HP',
                'heal_amount': 200
            })

        return Response({
            'items': items,
            'total_items': len(items)
        })