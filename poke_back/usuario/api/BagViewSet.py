from rest_framework import viewsets, permissions, serializers
from usuario.models.Bag import Bag


class BagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bag
        fields = ('id', 'pokeballs', 'potions')


class BagViewSet(viewsets.ModelViewSet):
    serializer_class = BagSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Bag.objects.filter(player__user=self.request.user)