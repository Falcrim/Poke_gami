from rest_framework import viewsets, permissions, serializers
from pokemon.models.Move import Move

class MoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Move
        fields = ('id', 'name', 'type', 'power', 'accuracy', 'pp', 'damage_class')

class MoveViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Move.objects.all()
    serializer_class = MoveSerializer
    permission_classes = [permissions.IsAuthenticated]