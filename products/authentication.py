from rest_framework_simplejwt.authentication import JWTAuthentication
import logging

logger = logging.getLogger('django.request')

class CustomJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        logger.debug("Iniciando autenticación personalizada")
        header = self.get_header(request)
        if header is None:
            logger.debug("No se encontró el header de autorización")
            return None

        # Limpiar el header de comillas adicionales
        if isinstance(header, bytes):
            header = header.decode('utf-8')
        header = header.strip('"\'')
        header = header.encode('utf-8')
        
        logger.debug(f"Header limpio: {header}")
        
        raw_token = self.get_raw_token(header)
        if raw_token is None:
            logger.debug("No se pudo extraer el token del header")
            return None

        logger.debug(f"Token raw encontrado: {raw_token}")
        
        try:
            validated_token = self.get_validated_token(raw_token)
            logger.debug("Token validado exitosamente")
            user = self.get_user(validated_token)
            logger.debug(f"Usuario encontrado: {user}")
            return (user, validated_token)
        except Exception as e:
            logger.error(f"Error en la autenticación: {str(e)}")
            return None

    def get_header(self, request):
        header = super().get_header(request)
        logger.debug(f"Header de autorización original: {header}")
        return header

    def get_raw_token(self, header):
        raw_token = super().get_raw_token(header)
        logger.debug(f"Token raw extraído: {raw_token}")
        return raw_token
