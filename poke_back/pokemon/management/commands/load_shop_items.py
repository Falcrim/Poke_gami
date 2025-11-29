from django.core.management.base import BaseCommand
from pokemon.models.ShopItem import ShopItem

class Command(BaseCommand):
    help = 'Carga los items iniciales de la tienda'

    def handle(self, *args, **options):
        self.stdout.write('Cargando items de tienda...')

        shop_items = [
            {
                'name': 'Pokéball',
                'item_type': 'pokeball',
                'price': 200,
                'description': 'Dispositivo para capturar Pokémon salvajes',
                'effect_value': 1
            },
            {
                'name': 'Ultraball',
                'item_type': 'ultra_ball',
                'price': 800,
                'description': 'Pokéball con mayor tasa de captura',
                'effect_value': 2
            },
            {
                'name': 'Poción',
                'item_type': 'potion',
                'price': 300,
                'description': 'Restaura 20 HP de un Pokémon',
                'effect_value': 20
            },
            {
                'name': 'Superpoción',
                'item_type': 'super_potion',
                'price': 700,
                'description': 'Restaura 50 HP de un Pokémon',
                'effect_value': 50
            },
            {
                'name': 'Hiperpoción',
                'item_type': 'hyper_potion',
                'price': 1200,
                'description': 'Restaura 200 HP de un Pokémon',
                'effect_value': 200
            },
        ]

        # Limpiar items existentes
        ShopItem.objects.all().delete()

        for item_data in shop_items:
            item = ShopItem.objects.create(**item_data)
            self.stdout.write(f'Creado: {item.name} - ${item.price}')

        self.stdout.write(self.style.SUCCESS('Items de tienda cargados exitosamente!'))