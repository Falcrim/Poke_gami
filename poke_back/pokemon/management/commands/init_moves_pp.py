from django.core.management.base import BaseCommand
from usuario.models.PlayerPokemon import PlayerPokemon


class Command(BaseCommand):
    help = 'Inicializa moves_pp para todos los Pokémon existentes'

    def handle(self, *args, **options):
        count = 0
        for pokemon in PlayerPokemon.objects.all():
            needs_update = False
            if not pokemon.moves_pp:
                pokemon.moves_pp = {}
                needs_update = True

            # Inicializar PP para cada movimiento si no existe
            for move in pokemon.moves.all():
                move_id_str = str(move.id)
                if move_id_str not in pokemon.moves_pp:
                    pokemon.moves_pp[move_id_str] = move.pp
                    needs_update = True

            if needs_update:
                pokemon.save()
                count += 1

        self.stdout.write(self.style.SUCCESS(f'Actualizados {count} Pokémon con moves_pp'))