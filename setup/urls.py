from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView
from CodeLabTest.views import (
    UserViewSet, PostViewSet, LikeViewSet, CommentViewSet,
    RegisterView, LoginView, LogoutView, ProfileView,
    UpdateProfileView, ChangePasswordView, UploadAvatarView,
    NotificationViewSet
)

from CodeLabTest.search import (
    GlobalSearchView, AdvancedPostSearchView,
    HashtagSearchView, SuggestionsView
)

from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'posts', PostViewSet, basename='post')
router.register(r'likes', LikeViewSet, basename='like')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    
    # Autenticação JWT
    path('api/auth/register/', RegisterView.as_view(), name='register'),
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Perfil do usuário
    path('api/auth/profile/', ProfileView.as_view(), name='profile'),
    path('api/auth/profile/update/', UpdateProfileView.as_view(), name='update_profile'),
    path('api/auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    # Upload de mídia
    path('api/auth/avatar/upload/', UploadAvatarView.as_view(), name='upload_avatar'),

    # Busca
    path('api/search/', GlobalSearchView.as_view(), name='global_search'),
    path('api/search/posts/', AdvancedPostSearchView.as_view(), name='search_posts'),
    path('api/search/hashtags/', HashtagSearchView.as_view(), name='search_hashtags'),
    path('api/search/suggestions/', SuggestionsView.as_view(), name='search_suggestions'),  

    #Documentação
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Servir arquivos de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)