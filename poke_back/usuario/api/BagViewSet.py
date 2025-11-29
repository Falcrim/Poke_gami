from rest_framework import viewsets, permissions, serializers
from usuario.models.Bag import Bag


class BagSerializer(serializers.ModelSerializer):
    item_summary = serializers.SerializerMethodField()

    class Meta:
        model = Bag
        fields = ('id', 'pokeballs', 'ultra_balls', 'potions', 'super_potions', 'hyper_potions', 'item_summary')

    def get_item_summary(self, obj):
        return obj.get_summary()


class BagViewSet(viewsets.ModelViewSet):
    serializer_class = BagSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Bag.objects.filter(player__user=self.request.user)


class BagViewSet(viewsets.ModelViewSet):
    serializer_class = BagSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Bag.objects.filter(player__user=self.request.user)
