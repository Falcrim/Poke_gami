from rest_framework import viewsets, status, permissions, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import authenticate
from usuario.models.User import User
from usuario.models.Player import Player
from usuario.models.Bag import Bag

from rest_framework.authtoken.models import Token


class UserSerializer(serializers.ModelSerializer):
    player_info = serializers.SerializerMethodField()
    pokedex_stats = serializers.SerializerMethodField()
    ranking_position = serializers.SerializerMethodField()
    achievements = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'battles_won', 'battles_lost',
                  'pvp_rating', 'date_joined', 'player_info', 'pokedex_stats', 'ranking_position', 'achievements')
        read_only_fields = ('battles_won', 'battles_lost', 'pvp_rating')

    def get_player_info(self, obj):
        try:
            player = obj.player_profile
            current_location = None
            if player.current_location:
                current_location = {
                    'id': player.current_location.id,
                    'name': player.current_location.name,
                    'type': player.current_location.location_type
                }

            return {
                'money': player.money,
                'starter_chosen': player.starter_chosen,
                'current_location': current_location,
                'pokemon_count': player.pokemons.count(),
                'team_count': player.pokemons.count()
            }
        except:
            return None

    def get_pokedex_stats(self, obj):
        try:
            from usuario.models.Pokedex import Pokedex
            player = obj.player_profile
            total_pokemon = 151

            pokedex_entries = Pokedex.objects.filter(player=player)
            seen_count = pokedex_entries.count()
            caught_count = pokedex_entries.filter(state='caught').count()

            return {
                'total_pokemon': total_pokemon,
                'seen': seen_count,
                'caught': caught_count,
                'completion_percentage': round((caught_count / total_pokemon) * 100, 2)
            }
        except:
            return None

    def get_ranking_position(self, obj):
        try:
            higher_rated = User.objects.filter(pvp_rating__gt=obj.pvp_rating).count()
            return higher_rated + 1  # Posición (1-based)
        except:
            return None

    def get_achievements(self, obj):
        achievements = []
        player = obj.player_profile

        if player.starter_chosen:
            achievements.append({'name': 'Entrenador Novato', 'description': 'Elegir Pokémon inicial'})

        pokedex_stats = self.get_pokedex_stats(obj)
        if pokedex_stats and pokedex_stats['caught'] >= 10:
            achievements.append({'name': 'Coleccionista', 'description': 'Capturar 10 Pokémon'})

        if obj.battles_won >= 10:
            achievements.append({'name': 'Veterano', 'description': 'Ganar 10 batallas'})

        return achievements


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )

        player = Player.objects.create(user=user)
        Bag.objects.create(player=player)

        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action == 'login':
            return UserLoginSerializer
        return UserSerializer

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                username=serializer.validated_data['username'],
                password=serializer.validated_data['password']
            )
            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'user': UserSerializer(user).data
                })
            return Response({'error': 'Credenciales inválidas'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        try:
            Token.objects.filter(user=request.user).delete()
            return Response({'message': 'Sesión cerrada correctamente'})
        except Exception as e:
            return Response({'error': f'Error al cerrar sesión: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def profile(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def ranking(self, request):
        top_players = User.objects.all().order_by('-pvp_rating', 'username')[:50]

        ranking_data = []
        for position, user in enumerate(top_players, 1):
            try:
                player_info = user.player_profile
                pokemon_count = player_info.pokemons.count()

                total_battles = user.battles_won + user.battles_lost
                win_rate = round((user.battles_won / total_battles * 100), 2) if total_battles > 0 else 0

                ranking_data.append({
                    'position': position,
                    'username': user.username,
                    'pvp_rating': user.pvp_rating,
                    'battles_won': user.battles_won,
                    'battles_lost': user.battles_lost,
                    'win_rate': win_rate,
                    'total_battles': total_battles,
                    'pokemon_count': pokemon_count,
                    'starter_chosen': player_info.starter_chosen
                })
            except:
                continue

        return Response(ranking_data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_ranking(self, request):
        user = request.user

        higher_rated = User.objects.filter(pvp_rating__gt=user.pvp_rating).count()
        user_position = higher_rated + 1

        start_idx = max(0, user_position - 3)
        end_idx = user_position + 2

        all_players = User.objects.all().order_by('-pvp_rating', 'username')
        nearby_players = all_players[start_idx:end_idx]

        nearby_data = []
        for position, player in enumerate(nearby_players, start_idx + 1):
            try:
                player_info = player.player_profile
                total_battles = player.battles_won + player.battles_lost
                win_rate = round((player.battles_won / total_battles * 100), 2) if total_battles > 0 else 0

                nearby_data.append({
                    'position': position,
                    'username': player.username,
                    'pvp_rating': player.pvp_rating,
                    'battles_won': player.battles_won,
                    'battles_lost': player.battles_lost,
                    'win_rate': win_rate,
                    'is_current_user': player.id == user.id
                })
            except:
                continue

        total_battles = user.battles_won + user.battles_lost
        win_rate = round((user.battles_won / total_battles * 100), 2) if total_battles > 0 else 0

        user_stats = {
            'position': user_position,
            'username': user.username,
            'pvp_rating': user.pvp_rating,
            'battles_won': user.battles_won,
            'battles_lost': user.battles_lost,
            'win_rate': win_rate,
            'total_battles': total_battles,
            'total_players': User.objects.count()
        }

        return Response({
            'user_stats': user_stats,
            'nearby_players': nearby_data
        })
