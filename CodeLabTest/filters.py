# CodeLabTest/filters.py
from django_filters import rest_framework as filters
from CodeLabTest.models import Post, Comment, User
from django.db.models import Q

class PostFilter(filters.FilterSet):
    """
    Filtros avançados para posts
    """
    # Filtros básicos
    author = filters.NumberFilter(field_name='author__id')
    author_username = filters.CharFilter(field_name='author__username', lookup_expr='iexact')
    
    # Filtros de data
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Busca em múltiplos campos
    search = filters.CharFilter(method='filter_search')
    
    # Filtros de engajamento
    min_likes = filters.NumberFilter(method='filter_min_likes')
    min_comments = filters.NumberFilter(method='filter_min_comments')
    has_image = filters.BooleanFilter(field_name='image', lookup_expr='isnull', exclude=True)
    
    # Ordenação
    ordering = filters.OrderingFilter(
        fields=(
            ('created_at', 'created_at'),
            ('updated_at', 'updated_at'),
            ('title', 'title'),
        )
    )
    
    class Meta:
        model = Post
        fields = ['author', 'author_username', 'has_image']
    
    def filter_search(self, queryset, name, value):
        """
        Busca em título e conteúdo
        """
        return queryset.filter(
            Q(title__icontains=value) | Q(content__icontains=value)
        )
    
    def filter_min_likes(self, queryset, name, value):
        """
        Filtrar por número mínimo de likes
        """
        from django.db.models import Count
        return queryset.annotate(
            num_likes=Count('likes')
        ).filter(num_likes__gte=value)
    
    def filter_min_comments(self, queryset, name, value):
        """
        Filtrar por número mínimo de comentários
        """
        from django.db.models import Count
        return queryset.annotate(
            num_comments=Count('comments')
        ).filter(num_comments__gte=value)

class CommentFilter(filters.FilterSet):
    """
    Filtros para comentários
    """
    post = filters.UUIDFilter(field_name='post__id')
    user = filters.NumberFilter(field_name='user__id')
    is_reply = filters.BooleanFilter(field_name='parent', lookup_expr='isnull', exclude=True)
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    search = filters.CharFilter(field_name='content', lookup_expr='icontains')
    
    ordering = filters.OrderingFilter(
        fields=(
            ('created_at', 'created_at'),
            ('updated_at', 'updated_at'),
        )
    )
    
    class Meta:
        model = Comment
        fields = ['post', 'user', 'is_reply']

class UserFilter(filters.FilterSet):
    """
    Filtros para usuários
    """
    search = filters.CharFilter(method='filter_search')
    is_active = filters.BooleanFilter(field_name='is_active')
    joined_after = filters.DateTimeFilter(field_name='created_datetime', lookup_expr='gte')
    joined_before = filters.DateTimeFilter(field_name='created_datetime', lookup_expr='lte')
    has_avatar = filters.BooleanFilter(field_name='avatar', lookup_expr='isnull', exclude=True)
    
    ordering = filters.OrderingFilter(
        fields=(
            ('created_datetime', 'joined'),
            ('username', 'username'),
            ('last_login', 'last_login'),
        )
    )
    
    class Meta:
        model = User
        fields = ['is_active', 'has_avatar']
    
    def filter_search(self, queryset, name, value):
        """
        Busca em username, first_name, last_name e email
        """
        return queryset.filter(
            Q(username__icontains=value) |
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value) |
            Q(email__icontains=value)
        )