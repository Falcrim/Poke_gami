from django.core.exceptions import ValidationError
from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from pokemon.models.ShopItem import ShopItem
from usuario.api.BagViewSet import BagSerializer
from usuario.models.Bag import Bag


class ShopItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopItem
        fields = ('id', 'name', 'item_type', 'price', 'description', 'effect_value')


class ShopViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ShopItem.objects.all()
    serializer_class = ShopItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def _check_location(self, player):
        if not player.current_location:
            raise ValidationError('No estás en ninguna ubicación')
        if player.current_location.location_type != 'town':
            raise ValidationError('Solo puedes usar la Tienda en pueblos')

    @action(detail=True, methods=['post'])
    def buy(self, request, pk=None):
        """Comprar un item de la tienda"""
        player = request.user.player_profile

        # Verificar ubicación
        try:
            self._check_location(player)
        except ValidationError as e:
            return Response({'error': str(e)}, status=400)

        item = self.get_object()
        bag = Bag.objects.get(player=player)

        # Verificar si el jugador tiene suficiente dinero
        if player.money < item.price:
            return Response({'error': 'No tienes suficiente dinero'}, status=400)

        # Comprar el item
        player.money -= item.price
        player.save()

        # Agregar el item a la mochila según el tipo
        if item.item_type == 'potion':
            bag.potions += 1
        elif item.item_type == 'super_potion':
            bag.super_potions += 1
        elif item.item_type == 'hyper_potion':
            bag.hyper_potions += 1
        elif item.item_type == 'pokeball':
            bag.pokeballs += 1
        elif item.item_type == 'ultra_ball':
            bag.ultra_balls += 1

        bag.save()

        return Response({
            'message': f'Has comprado {item.name}',
            'money_left': player.money,
            'bag': bag.get_summary()
        })

    @action(detail=False, methods=['get'])
    def my_bag(self, request):
        player = request.user.player_profile
        bag = Bag.objects.get(player=player)
        serializer = BagSerializer(bag)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def can_shop(self, request):
        player = request.user.player_profile

        if not player.current_location:
            return Response({
                'can_shop': False,
                'reason': 'No estás en ninguna ubicación'
            })

        if player.current_location.location_type != 'town':
            return Response({
                'can_shop': False,
                'reason': 'Solo puedes usar la Tienda en pueblos'
            })

        return Response({
            'can_shop': True,
            'location': player.current_location.name,
            'location_type': player.current_location.location_type,
            'message': f'Bienvenido a la Tienda de {player.current_location.name}'
        })
