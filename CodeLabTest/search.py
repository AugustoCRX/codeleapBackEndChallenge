# CodeLabTest/search.py

from django.db.models import Q, Count
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.views import APIView
from CodeLabTest.models import Post, User, Comment
from CodeLabTest.serializers import PostSerializer, UserSerializer, CommentSerializer
from CodeLabTest.pagination import StandardResultsSetPagination

class GlobalSearchView(APIView):
    """
    Busca global em posts, usuários e comentários
    GET /api/search/?q=termo&type=all
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        search_type = request.query_params.get('type', 'all')  # all, posts, users, comments
        
        if not query or len(query) < 2:
            return Response({
                'error': 'Query deve ter pelo menos 2 caracteres'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        results = {}
        
        if search_type in ['all', 'posts']:
            posts = self.search_posts(query)
            results['posts'] = {
                'count': posts.count(),
                'results': PostSerializer(posts[:10], many=True, context={'request': request}).data
            }
        
        if search_type in ['all', 'users']:
            users = self.search_users(query)
            results['users'] = {
                'count': users.count(),
                'results': UserSerializer(users[:10], many=True, context={'request': request}).data
            }
        
        if search_type in ['all', 'comments']:
            comments = self.search_comments(query)
            results['comments'] = {
                'count': comments.count(),
                'results': CommentSerializer(comments[:10], many=True).data
            }
        
        # Total de resultados
        total = sum(r['count'] for r in results.values())
        
        return Response({
            'query': query,
            'total_results': total,
            'results': results
        })
    
    def search_posts(self, query):
        """Busca em posts (título e conteúdo)"""
        return Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).annotate(
            like_count=Count('likes'),
            comment_count=Count('comments')
        ).select_related('author').order_by('-created_at')
    
    def search_users(self, query):
        """Busca em usuários (username, nome, email)"""
        return User.objects.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        ).filter(is_active=True).order_by('-created_datetime')
    
    def search_comments(self, query):
        """Busca em comentários"""
        return Comment.objects.filter(
            content__icontains=query
        ).select_related('user', 'post').order_by('-created_at')


class AdvancedPostSearchView(generics.ListAPIView):
    """
    Busca avançada apenas em posts com filtros
    GET /api/search/posts/?q=termo&author=1&min_likes=5
    """
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        query = self.request.query_params.get('q', '').strip()
        
        if not query or len(query) < 2:
            return Post.objects.none()
        
        # Busca base
        queryset = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        ).annotate(
            like_count=Count('likes'),
            comment_count=Count('comments')
        ).select_related('author')
        
        # Filtros adicionais
        author_id = self.request.query_params.get('author')
        if author_id:
            queryset = queryset.filter(author_id=author_id)
        
        min_likes = self.request.query_params.get('min_likes')
        if min_likes:
            queryset = queryset.filter(like_count__gte=int(min_likes))
        
        has_image = self.request.query_params.get('has_image')
        if has_image == 'true':
            queryset = queryset.exclude(image='')
        
        # Ordenação
        order_by = self.request.query_params.get('order_by', '-created_at')
        valid_orders = ['-created_at', 'created_at', '-like_count', '-comment_count']
        if order_by in valid_orders:
            queryset = queryset.order_by(order_by)
        
        return queryset
    
    def get_serializer_context(self):
        return {'request': self.request}


class HashtagSearchView(APIView):
    """
    Busca por hashtags em posts
    GET /api/search/hashtags/?tag=python
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request):
        tag = request.query_params.get('tag', '').strip().lower()
        
        if not tag:
            return Response({
                'error': 'Tag é obrigatória'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Buscar posts que contenham #tag
        hashtag = f'#{tag}'
        posts = Post.objects.filter(
            Q(title__icontains=hashtag) | Q(content__icontains=hashtag)
        ).annotate(
            like_count=Count('likes'),
            comment_count=Count('comments')
        ).select_related('author').order_by('-created_at')
        
        paginator = StandardResultsSetPagination()
        paginated_posts = paginator.paginate_queryset(posts, request)
        
        serializer = PostSerializer(paginated_posts, many=True, context={'request': request})
        
        return paginator.get_paginated_response(serializer.data)


class SuggestionsView(APIView):
    """
    Sugestões de busca (autocomplete)
    GET /api/search/suggestions/?q=term
    """
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        
        if not query or len(query) < 2:
            return Response({'suggestions': []})
        
        # Buscar títulos de posts que começam com o termo
        post_titles = Post.objects.filter(
            title__istartswith=query
        ).values_list('title', flat=True)[:5]
        
        # Buscar usernames que começam com o termo
        usernames = User.objects.filter(
            username__istartswith=query,
            is_active=True
        ).values_list('username', flat=True)[:5]
        
        # Combinar sugestões
        suggestions = list(set(list(post_titles) + [f'@{u}' for u in usernames]))
        
        return Response({
            'query': query,
            'suggestions': suggestions[:10]
        })