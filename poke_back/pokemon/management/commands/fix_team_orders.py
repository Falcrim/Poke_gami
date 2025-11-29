from django.core.management.base import BaseCommand
from usuario.models.Player import Player


class Command(BaseCommand):
    help = 'Corrige los órdenes de todos los equipos de jugadores'

    def handle(self, *args, **options):
        self.stdout.write('Corrigiendo órdenes de equipos...')

        players = Player.objects.all()

        for player in players:
            team_pokemons = player.pokemons.filter(in_team=True).order_by('order', 'id')

            fixed_count = 0
            for new_order, pokemon in enumerate(team_pokemons):
                if pokemon.order != new_order:
                    pokemon.order = new_order
                    pokemon.save(update_fields=['order'])
                    fixed_count += 1

            if fixed_count > 0:
                self.stdout.write(f'Jugador {player.user.username}: {fixed_count} Pokémon reordenados')

        self.stdout.write(self.style.SUCCESS('Órdenes de equipos corregidos exitosamente!'))
