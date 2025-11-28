from django.core.management.base import BaseCommand
from pokemon.models.Location import Location


class Command(BaseCommand):
    help = 'Carga las ubicaciones iniciales del mapa'

    def handle(self, *args, **options):
        self.stdout.write('Cargando ubicaciones...')

        # Crear pueblos
        towns = [
            {'name': 'Pueblo Paleta', 'location_type': 'town'},  # 1
            {'name': 'Ciudad Celeste', 'location_type': 'town'},  # 2
            {'name': 'Pueblo Lavanda', 'location_type': 'town'},  # 3
            {'name': 'Ciudad Azulona', 'location_type': 'town'},  # 4
            {'name': 'Ciudad Carmín', 'location_type': 'town'},  # 5
            {'name': 'Ciudad Azafrán', 'location_type': 'town'},  # 6
            {'name': 'Ciudad Fucsia', 'location_type': 'town'},  # 7
            {'name': 'Pueblo Verde', 'location_type': 'town'},  # 8
            {'name': 'Ciudad Canela', 'location_type': 'town'},  # 9
            {'name': 'Isla Espuma', 'location_type': 'town'},  # 10
            {'name': 'Ciudad Plateada', 'location_type': 'town'},  # 11
        ]

        # Crear rutas
        routes = [
            {'name': 'Ruta 1', 'location_type': 'route'},
            {'name': 'Ruta 2', 'location_type': 'route'},
            {'name': 'Ruta 3', 'location_type': 'route'},
            {'name': 'Ruta 4', 'location_type': 'route'},
            {'name': 'Ruta 5', 'location_type': 'route'},
            {'name': 'Ruta 6', 'location_type': 'route'},
            {'name': 'Ruta 7', 'location_type': 'route'},
            {'name': 'Ruta 8', 'location_type': 'route'},
            {'name': 'Ruta 9', 'location_type': 'route'},
            {'name': 'Ruta 10', 'location_type': 'route'},
            {'name': 'Ruta 11', 'location_type': 'route'},
            {'name': 'Ruta 12', 'location_type': 'route'},
            {'name': 'Ruta 13', 'location_type': 'route'},
            {'name': 'Ruta 14', 'location_type': 'route'},
            {'name': 'Ruta 15', 'location_type': 'route'},
            {'name': 'Ruta 16', 'location_type': 'route'},
            {'name': 'Ruta 17', 'location_type': 'route'},
            {'name': 'Ruta 18', 'location_type': 'route'},
            {'name': 'Ruta 19', 'location_type': 'route'},
            {'name': 'Ruta 20', 'location_type': 'route'},
            {'name': 'Ruta 21', 'location_type': 'route'},
            {'name': 'Ruta 22', 'location_type': 'route'},
            {'name': 'Ruta 23', 'location_type': 'route'},
        ]

        # Crear todas las ubicaciones
        locations = {}
        for town_data in towns:
            location, created = Location.objects.get_or_create(
                name=town_data['name'],
                defaults={'location_type': town_data['location_type']}
            )
            locations[town_data['name']] = location
            if created:
                self.stdout.write(f'Creada: {town_data["name"]}')

        for route_data in routes:
            location, created = Location.objects.get_or_create(
                name=route_data['name'],
                defaults={'location_type': route_data['location_type']}
            )
            locations[route_data['name']] = location
            if created:
                self.stdout.write(f'Creada: {route_data["name"]}')

        # Establecer conexiones BIDIRECCIONALES (según tu mapa)
        # Para cada conexión A->B, también conectamos B->A

        # Pueblo Paleta <-> Ruta 1
        locations['Pueblo Paleta'].connected_locations.add(locations['Ruta 1'])
        locations['Ruta 1'].connected_locations.add(locations['Pueblo Paleta'])

        # Ruta 1 <-> Ciudad Celeste
        locations['Ruta 1'].connected_locations.add(locations['Ciudad Celeste'])
        locations['Ciudad Celeste'].connected_locations.add(locations['Ruta 1'])

        # Ciudad Celeste <-> Ruta 2
        locations['Ciudad Celeste'].connected_locations.add(locations['Ruta 2'])
        locations['Ruta 2'].connected_locations.add(locations['Ciudad Celeste'])

        # Ruta 2 <-> Pueblo Lavanda
        locations['Ruta 2'].connected_locations.add(locations['Pueblo Lavanda'])
        locations['Pueblo Lavanda'].connected_locations.add(locations['Ruta 2'])

        # Pueblo Lavanda <-> Ruta 3
        locations['Pueblo Lavanda'].connected_locations.add(locations['Ruta 3'])
        locations['Ruta 3'].connected_locations.add(locations['Pueblo Lavanda'])

        # Ruta 3 <-> Ruta 4
        locations['Ruta 3'].connected_locations.add(locations['Ruta 4'])
        locations['Ruta 4'].connected_locations.add(locations['Ruta 3'])

        # Ruta 4 <-> Ruta 5
        locations['Ruta 4'].connected_locations.add(locations['Ruta 5'])
        locations['Ruta 5'].connected_locations.add(locations['Ruta 4'])

        # Ruta 5 <-> Ciudad Azulona
        locations['Ruta 5'].connected_locations.add(locations['Ciudad Azulona'])
        locations['Ciudad Azulona'].connected_locations.add(locations['Ruta 5'])

        # Pueblo Lavanda <-> Ruta 6
        locations['Pueblo Lavanda'].connected_locations.add(locations['Ruta 6'])
        locations['Ruta 6'].connected_locations.add(locations['Pueblo Lavanda'])

        # Ruta 6 <-> Ciudad Carmín
        locations['Ruta 6'].connected_locations.add(locations['Ciudad Carmín'])
        locations['Ciudad Carmín'].connected_locations.add(locations['Ruta 6'])

        # Ciudad Carmín <-> Ruta 7
        locations['Ciudad Carmín'].connected_locations.add(locations['Ruta 7'])
        locations['Ruta 7'].connected_locations.add(locations['Ciudad Carmín'])

        # Ruta 7 <-> Ruta 8
        locations['Ruta 7'].connected_locations.add(locations['Ruta 8'])
        locations['Ruta 8'].connected_locations.add(locations['Ruta 7'])

        # Ruta 8 <-> Ruta 9
        locations['Ruta 8'].connected_locations.add(locations['Ruta 9'])
        locations['Ruta 9'].connected_locations.add(locations['Ruta 8'])

        # Ruta 9 <-> Ciudad Azafrán
        locations['Ruta 9'].connected_locations.add(locations['Ciudad Azafrán'])
        locations['Ciudad Azafrán'].connected_locations.add(locations['Ruta 9'])

        # Ciudad Azafrán <-> Ruta 13
        locations['Ciudad Azafrán'].connected_locations.add(locations['Ruta 13'])
        locations['Ruta 13'].connected_locations.add(locations['Ciudad Azafrán'])

        # Ciudad Azafrán <-> Ruta 10
        locations['Ciudad Azafrán'].connected_locations.add(locations['Ruta 10'])
        locations['Ruta 10'].connected_locations.add(locations['Ciudad Azafrán'])

        # Ruta 10 <-> Ruta 11
        locations['Ruta 10'].connected_locations.add(locations['Ruta 11'])
        locations['Ruta 11'].connected_locations.add(locations['Ruta 10'])

        # Ruta 11 <-> Ciudad Fucsia
        locations['Ruta 11'].connected_locations.add(locations['Ciudad Fucsia'])
        locations['Ciudad Fucsia'].connected_locations.add(locations['Ruta 11'])

        # Ciudad Fucsia <-> Ruta 18
        locations['Ciudad Fucsia'].connected_locations.add(locations['Ruta 18'])
        locations['Ruta 18'].connected_locations.add(locations['Ciudad Fucsia'])

        # Ciudad Fucsia <-> Ruta 12
        locations['Ciudad Fucsia'].connected_locations.add(locations['Ruta 12'])
        locations['Ruta 12'].connected_locations.add(locations['Ciudad Fucsia'])

        # Ruta 12 <-> Pueblo Verde
        locations['Ruta 12'].connected_locations.add(locations['Pueblo Verde'])
        locations['Pueblo Verde'].connected_locations.add(locations['Ruta 12'])

        # Pueblo Verde <-> Ruta 13
        locations['Pueblo Verde'].connected_locations.add(locations['Ruta 13'])
        locations['Ruta 13'].connected_locations.add(locations['Pueblo Verde'])

        # Pueblo Verde <-> Ruta 20
        locations['Pueblo Verde'].connected_locations.add(locations['Ruta 20'])
        locations['Ruta 20'].connected_locations.add(locations['Pueblo Verde'])

        # Pueblo Verde <-> Ruta 14
        locations['Pueblo Verde'].connected_locations.add(locations['Ruta 14'])
        locations['Ruta 14'].connected_locations.add(locations['Pueblo Verde'])

        # Ruta 14 <-> Ciudad Canela
        locations['Ruta 14'].connected_locations.add(locations['Ciudad Canela'])
        locations['Ciudad Canela'].connected_locations.add(locations['Ruta 14'])

        # Ciudad Canela <-> Ruta 15
        locations['Ciudad Canela'].connected_locations.add(locations['Ruta 15'])
        locations['Ruta 15'].connected_locations.add(locations['Ciudad Canela'])

        # Ruta 15 <-> Ruta 16
        locations['Ruta 15'].connected_locations.add(locations['Ruta 16'])
        locations['Ruta 16'].connected_locations.add(locations['Ruta 15'])

        # Ruta 16 <-> Ruta 17
        locations['Ruta 16'].connected_locations.add(locations['Ruta 17'])
        locations['Ruta 17'].connected_locations.add(locations['Ruta 16'])

        # Ruta 17 <-> Isla Espuma
        locations['Ruta 17'].connected_locations.add(locations['Isla Espuma'])
        locations['Isla Espuma'].connected_locations.add(locations['Ruta 17'])

        # Ruta 18 <-> Ruta 19
        locations['Ruta 18'].connected_locations.add(locations['Ruta 19'])
        locations['Ruta 19'].connected_locations.add(locations['Ruta 18'])

        # Ruta 19 <-> Ciudad Plateada
        locations['Ruta 19'].connected_locations.add(locations['Ciudad Plateada'])
        locations['Ciudad Plateada'].connected_locations.add(locations['Ruta 19'])

        # Ciudad Plateada <-> Ruta 20
        locations['Ciudad Plateada'].connected_locations.add(locations['Ruta 20'])
        locations['Ruta 20'].connected_locations.add(locations['Ciudad Plateada'])

        # Ruta 18 <-> Ruta 21
        locations['Ruta 18'].connected_locations.add(locations['Ruta 21'])
        locations['Ruta 21'].connected_locations.add(locations['Ruta 18'])

        # Ruta 21 <-> Ruta 22
        locations['Ruta 21'].connected_locations.add(locations['Ruta 22'])
        locations['Ruta 22'].connected_locations.add(locations['Ruta 21'])

        # Ruta 22 <-> Ruta 23
        locations['Ruta 22'].connected_locations.add(locations['Ruta 23'])
        locations['Ruta 23'].connected_locations.add(locations['Ruta 22'])

        # Ruta 23 <-> Ciudad Plateada
        locations['Ruta 23'].connected_locations.add(locations['Ciudad Plateada'])
        locations['Ciudad Plateada'].connected_locations.add(locations['Ruta 23'])

        self.stdout.write(self.style.SUCCESS('Ubicaciones cargadas exitosamente!'))