from django.apps import AppConfig


class UsuarioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuario'

    def ready(self):
        # Eliminar esta línea por ahora, agregaremos signals después
        # import usuario.signals
        pass