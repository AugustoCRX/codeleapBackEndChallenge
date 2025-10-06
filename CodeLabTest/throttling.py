# CodeLabTest/throttling.py

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class BurstRateThrottle(UserRateThrottle):
    """
    Rate limit para picos de requisições (muito rápido)
    5 requisições por minuto
    """
    scope = 'burst'
    rate = '5/min'

class SustainedRateThrottle(UserRateThrottle):
    """
    Rate limit sustentado (médio prazo)
    100 requisições por hora
    """
    scope = 'sustained'
    rate = '100/hour'

class DailyRateThrottle(UserRateThrottle):
    """
    Rate limit diário
    1000 requisições por dia
    """
    scope = 'daily'
    rate = '1000/day'

class PostCreateThrottle(UserRateThrottle):
    """
    Limite para criação de posts
    10 posts por hora
    """
    scope = 'post_create'
    rate = '10/hour'

class CommentCreateThrottle(UserRateThrottle):
    """
    Limite para criação de comentários
    30 comentários por hora
    """
    scope = 'comment_create'
    rate = '30/hour'

class LoginThrottle(AnonRateThrottle):
    """
    Limite para tentativas de login
    5 tentativas por hora
    """
    scope = 'login'
    rate = '5/hour'

class RegistrationThrottle(AnonRateThrottle):
    """
    Limite para registro de usuários
    3 registros por hora por IP
    """
    scope = 'registration'
    rate = '3/hour'