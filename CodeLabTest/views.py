from rest_framework import viewsets, status, generics, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Count, Q
from django_filters import rest_framework as filters_backend
from CodeLabTest.pagination import StandardResultsSetPagination # Certifique-se de que esta importação existe
from CodeLabTest.models import User, Post, Like, Comment, Notification
from CodeLabTest.serializers import (
    UserSerializer, PostSerializer, LikeSerializer, 
    CommentSerializer, CommentReplySerializer,
    UserRegistrationSerializer, UserLoginSerializer,
    UserUpdateSerializer, ChangePasswordSerializer,
    AvatarUploadSerializer, NotificationSerializer
)
from CodeLabTest.pagination import StandardResultsSetPagination, PostCursorPagination
from CodeLabTest.filters import PostFilter, CommentFilter, UserFilter
from CodeLabTest.throttling import (
    LoginThrottle, RegistrationThrottle,
    PostCreateThrottle, CommentCreateThrottle
)

from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

@extend_schema_view(
    list=extend_schema(
        summary='Listar Posts',
        description='Lista todos os posts com paginação e filtros',
        tags=['Posts'],
        parameters=[
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Número da página'
            ),
            OpenApiParameter(   
                name='page_size',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Tamanho da página (máx: 100)'
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Buscar por título ou conteúdo'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Ordenação: -created_at, -like_count, -comment_count'
            ),
        ]
    ),
    create=extend_schema(
        summary='Criar Post',
        description='Cria um novo post (requer autenticação)',
        tags=['Posts'],
        examples=[
            OpenApiExample(
                'Exemplo de Post',
                value={
                    'title': 'Meu Primeiro Post',
                    'content': 'Conteúdo do post aqui'
                }
            )
        ]
    ),
    retrieve=extend_schema(
        summary='Detalhes do Post',
        description='Retorna detalhes de um post específico',
        tags=['Posts']
    ),
    update=extend_schema(
        summary='Atualizar Post',
        description='Atualiza um post (apenas o autor)',
        tags=['Posts']
    ),
    partial_update=extend_schema(
        summary='Atualizar Post Parcialmente',
        description='Atualiza campos específicos de um post',
        tags=['Posts']
    ),
    destroy=extend_schema(
        summary='Deletar Post',
        description='Deleta um post (apenas o autor)',
        tags=['Posts']
    )
)

# ==================== AUTENTICAÇÃO ====================

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    throttle_classes = [RegistrationThrottle]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Usuário criado com sucesso',
            'user': UserSerializer(user, context={'request': request}).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)

# Decorar view de Login
@extend_schema(
    summary='Login',
    description='Autenticação de usuário com JWT',
    tags=['Authentication'],
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string'},
                'password': {'type': 'string'}
            }
        }
    },
    examples=[
        OpenApiExample(
            'Exemplo de Login',
            value={
                'username': 'testuser',
                'password': 'senha@123'
            }
        )
    ],
    responses={
        200: {
            'description': 'Login bem sucedido',
            'content': {
                'application/json': {
                    'example': {
                        'message': 'Login realizado com sucesso',
                        'user': {
                            'id': 1,
                            'username': 'testuser',
                            'email': 'test@example.com'
                        },
                        'tokens': {
                            'refresh': 'token_aqui',
                            'access': 'token_aqui'
                        }
                    }
                }
            }
        },
        400: {'description': 'Credenciais inválidas'}
    }
)

class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Login realizado com sucesso',
            'user': UserSerializer(user, context={'request': request}).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({
                    'error': 'Refresh token é obrigatório'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({
                'message': 'Logout realizado com sucesso'
            }, status=status.HTTP_200_OK)
        except Exception:
            return Response({
                'error': 'Token inválido'
            }, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)

class UpdateProfileView(generics.UpdateAPIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'message': 'Perfil atualizado com sucesso',
            'user': UserSerializer(instance, context={'request': request}).data
        })

class UploadAvatarView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser]
    
    def post(self, request):
        serializer = AvatarUploadSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            # Deletar avatar antigo se existir
            if request.user.avatar:
                request.user.avatar.delete(save=False)
            
            serializer.save()
            
            return Response({
                'message': 'Avatar atualizado com sucesso',
                'user': UserSerializer(request.user, context={'request': request}).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        if request.user.avatar:
            request.user.avatar.delete(save=True)
            return Response({
                'message': 'Avatar removido com sucesso'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error': 'Usuário não possui avatar'
        }, status=status.HTTP_404_NOT_FOUND)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'message': 'Senha alterada com sucesso'
        }, status=status.HTTP_200_OK)

# ==================== USUÁRIOS ====================

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para usuários com filtros e paginação
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters_backend.DjangoFilterBackend]
    filterset_class = UserFilter
    
    def get_queryset(self):
        """
        Adiciona contadores de posts e comentários
        """
        return User.objects.annotate(
            post_count=Count('posts'),
            comment_count=Count('comments')
        )
    
    def get_serializer_context(self):
        return {'request': self.request}
    
    @action(detail=True, methods=['get'], url_path='posts')
    def get_user_posts(self, request, pk=None):
        """
        Lista posts do usuário com paginação
        """
        user = self.get_object()
        posts = user.posts.all()
        
        # Aplicar filtros se fornecidos
        filterset = PostFilter(request.GET, queryset=posts)
        posts = filterset.qs
        
        # Paginar resultados
        paginator = StandardResultsSetPagination()
        paginated_posts = paginator.paginate_queryset(posts, request)
        
        serializer = PostSerializer(paginated_posts, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

# ==================== POSTS ====================

class PostViewSet(viewsets.ModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        return Post.objects.annotate(
            like_count=Count('likes'),
            comment_count=Count('comments', filter=Q(comments__parent__isnull=True))
        ).select_related('author').prefetch_related('likes', 'comments').order_by('-created_at')
    
    def get_serializer_context(self):
        return {'request': self.request}
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=False, methods=['get'], url_path='trending')
    def trending(self, request):
        """
        Posts em alta (mais likes nas últimas 24h)
        GET /api/posts/trending/
        """
        from datetime import timedelta
        from django.utils import timezone
        
        twenty_four_hours_ago = timezone.now() - timedelta(hours=24)
        
        posts = self.get_queryset().filter(
            created_at__gte=twenty_four_hours_ago
        ).order_by('-like_count', '-created_at')
        
        paginator = self.pagination_class()
        paginated_posts = paginator.paginate_queryset(posts, request)
        serializer = self.get_serializer(paginated_posts, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='feed')
    def feed(self, request):
        """
        Feed personalizado (cursor pagination para scroll infinito)
        GET /api/posts/feed/?cursor=xxx
        """
        posts = self.get_queryset().order_by('-created_at')
        
        paginator = PostCursorPagination()
        paginated_posts = paginator.paginate_queryset(posts, request)
        serializer = self.get_serializer(paginated_posts, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='popular')
    def popular(self, request):
        """
        Posts mais populares de todos os tempos
        GET /api/posts/popular/
        """
        posts = self.get_queryset().order_by('-like_count', '-comment_count', '-created_at')
        
        paginator = self.pagination_class()
        paginated_posts = paginator.paginate_queryset(posts, request)
        serializer = self.get_serializer(paginated_posts, many=True)
        return paginator.get_paginated_response(serializer.data)

    def update(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return Response({
                'error': 'Você não pode editar posts de outros usuários'
            }, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return Response({
                'error': 'Você não pode deletar posts de outros usuários'
            }, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'], url_path='upload-image')
    def upload_image(self, request, pk=None):
        post = self.get_object()
        
        if post.author != request.user:
            return Response({
                'error': 'Você não pode editar posts de outros usuários'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if 'image' not in request.data:
            return Response({
                'error': 'Nenhuma imagem foi enviada'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Deletar imagem antiga se existir
        if post.image:
            post.image.delete(save=False)
        
        serializer = self.get_serializer(post, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'message': 'Imagem atualizada com sucesso',
            'post': serializer.data
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['delete'], url_path='delete-image')
    def delete_image(self, request, pk=None):
        post = self.get_object()
        
        if post.author != request.user:
            return Response({
                'error': 'Você não pode editar posts de outros usuários'
            }, status=status.HTTP_403_FORBIDDEN)
        
        if post.image:
            post.image.delete(save=True)
            return Response({
                'message': 'Imagem removida com sucesso'
            }, status=status.HTTP_200_OK)
        
        return Response({
            'error': 'Post não possui imagem'
        }, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
        summary='Curtir Post',
        description='Adiciona um like ao post',
        tags=['Likes'],
        responses={
            201: {'description': 'Post curtido com sucesso'},
            200: {'description': 'Você já curtiu este post'}
        }
    )
    
    @extend_schema(
        summary='Curtir Post',
        description='Adiciona um like ao post e cria notificação',
        tags=['Likes']
    )
    @action(detail=True, methods=['post'], url_path='like')
    def like_post(self, request, pk=None):
        post = self.get_object()
        user = request.user
        
        like, created = Like.objects.get_or_create(user=user, post=post)
        
        if created:
            # Criar notificação
            Notification.create_like_notification(like)
            return Response({
                'message': 'Post curtido com sucesso',
                'like_count': post.likes.count()
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'message': 'Você já curtiu este post',
                'like_count': post.likes.count()
            }, status=status.HTTP_200_OK)
        
    @extend_schema(
        summary='Descurtir Post',
        description='Remove o like do post',
        tags=['Likes'],
        responses={
            200: {'description': 'Like removido'},
            404: {'description': 'Você não curtiu este post'}
        }
    )
    
    @action(detail=True, methods=['delete'], url_path='unlike')
    def unlike_post(self, request, pk=None):
        post = self.get_object()
        user = request.user
        
        try:
            like = Like.objects.get(user=user, post=post)
            like.delete()
            return Response({
                'message': 'Like removido com sucesso',
                'like_count': post.likes.count()
            }, status=status.HTTP_200_OK)
        except Like.DoesNotExist:
            return Response({
                'message': 'Você não curtiu este post',
                'like_count': post.likes.count()
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'], url_path='likes')
    def get_likes(self, request, pk=None):
        post = self.get_object()
        likes = post.likes.select_related('user').all()
        serializer = LikeSerializer(likes, many=True)
        return Response({
            'count': likes.count(),
            'likes': serializer.data
        })
    
    @action(detail=True, methods=['get'], url_path='comments')
    def get_comments(self, request, pk=None):
        post = self.get_object()
        comments = post.comments.filter(parent__isnull=True).select_related('user').prefetch_related('replies')
        serializer = CommentSerializer(comments, many=True)
        return Response({
            'count': comments.count(),
            'comments': serializer.data
        })
    
    @action(detail=True, methods=['post'], url_path='comment')
    def add_comment(self, request, pk=None):
        post = self.get_object()
        content = request.data.get('content', '').strip()
        
        if not content:
            return Response({
                'error': 'O conteúdo do comentário não pode estar vazio'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(content) > 1000:
            return Response({
                'error': 'O comentário não pode ter mais de 1000 caracteres'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        comment = Comment.objects.create(
            user=request.user,
            post=post,
            content=content
        )

        Notification.create_comment_notification(comment)
        
        serializer = CommentSerializer(comment)
        return Response({
            'message': 'Comentário adicionado com sucesso',
            'comment': serializer.data,
            'comment_count': post.comments.filter(parent__isnull=True).count()
        }, status=status.HTTP_201_CREATED)
    def get_throttles(self):
        """
        Aplicar rate limiting diferente por ação
        """
        if self.action == 'create':
            return [PostCreateThrottle()]
        return super().get_throttles()

# ==================== COMENTÁRIOS ====================

class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet para comentários com filtros e paginação
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters_backend.DjangoFilterBackend]
    filterset_class = CommentFilter
    
    def get_queryset(self):
        return Comment.objects.select_related(
            'user', 'post', 'parent'
        ).prefetch_related('replies')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.user != request.user:
            return Response({
                'error': 'Você não pode editar comentários de outros usuários'
            }, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.user != request.user:
            return Response({
                'error': 'Você não pode deletar comentários de outros usuários'
            }, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'], url_path='reply')
    def reply_to_comment(self, request, pk=None):
        parent_comment = self.get_object()
        content = request.data.get('content', '').strip()
        
        if not content:
            return Response({
                'error': 'O conteúdo da resposta não pode estar vazio'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if len(content) > 1000:
            return Response({
                'error': 'A resposta não pode ter mais de 1000 caracteres'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if parent_comment.parent is not None:
            return Response({
                'error': 'Não é possível responder a uma resposta. Responda ao comentário principal.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        reply = Comment.objects.create(
            user=request.user,
            post=parent_comment.post,
            parent=parent_comment,
            content=content
        )
        
        Notification.create_reply_notification(reply)

        serializer = CommentReplySerializer(reply)
        return Response({
            'message': 'Resposta adicionada com sucesso',
            'reply': serializer.data,
            'reply_count': parent_comment.replies.count()
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'], url_path='replies')
    def get_replies(self, request, pk=None):
        comment = self.get_object()
        replies = comment.replies.select_related('user').all()
        serializer = CommentReplySerializer(replies, many=True)
        return Response({
            'count': replies.count(),
            'replies': serializer.data
        })
    def get_throttles(self):
        """
        Aplicar rate limiting para criação de comentários
        """
        if self.action in ['create', 'reply_to_comment']:
            return [CommentCreateThrottle()]
        return super().get_throttles()

# ==================== LIKES ====================

class LikeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Like.objects.select_related('user', 'post').all()
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

# ==================== NOTIFICAÇÕES ====================

@extend_schema_view(
    list=extend_schema(
        summary='Listar Notificações',
        description='Lista todas as notificações do usuário autenticado',
        tags=['Notifications']
    )
)
class NotificationViewSet(viewsets.ModelViewSet):
    """
    ViewSet para notificações do usuário
    """
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        return Notification.objects.filter(
            recipient=self.request.user
        ).select_related('sender', 'post', 'comment')
    
    def get_serializer_context(self):
        return {'request': self.request}
    
    @extend_schema(
        summary='Notificações Não Lidas',
        tags=['Notifications']
    )
    @action(detail=False, methods=['get'], url_path='unread')
    def unread(self, request):
        notifications = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response({
            'count': notifications.count(),
            'results': serializer.data
        })
    
    @extend_schema(
        summary='Contar Não Lidas',
        tags=['Notifications']
    )
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({'count': count})
    
    @extend_schema(
        summary='Marcar como Lida',
        tags=['Notifications']
    )
    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.mark_as_read()
        return Response({
            'message': 'Notificação marcada como lida',
            'notification': self.get_serializer(notification).data
        })
    
    @extend_schema(
        summary='Marcar Todas como Lidas',
        tags=['Notifications']
    )
    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        from django.utils import timezone
        count = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({
            'message': f'{count} notificações marcadas como lidas',
            'count': count
        })
    
    @extend_schema(
        summary='Limpar Todas as Lidas',
        tags=['Notifications']
    )
    @action(detail=False, methods=['delete'], url_path='clear-all')
    def clear_all(self, request):
        count = self.get_queryset().filter(is_read=True).delete()[0]
        return Response({
            'message': f'{count} notificações deletadas',
            'count': count
        })