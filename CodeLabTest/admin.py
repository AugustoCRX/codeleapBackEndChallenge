from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from CodeLabTest.models import User, Post, Like, Comment

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin customizado para o modelo User
    """
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'created_datetime']
    list_filter = ['is_staff', 'is_active', 'is_superuser', 'created_datetime']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-created_datetime']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissões', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Datas Importantes', {'fields': ('last_login', 'created_datetime', 'updated_datetime')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'first_name', 'last_name'),
        }),
    )
    
    readonly_fields = ['created_datetime', 'updated_datetime', 'last_login']
    
    def get_queryset(self, request):
        """
        Otimiza a query para exibir contadores
        """
        qs = super().get_queryset(request)
        return qs.prefetch_related('posts', 'comments', 'likes')

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'author', 'created_at', 'get_like_count', 'get_comment_count']
    list_filter = ['created_at', 'author']
    search_fields = ['title', 'content', 'author__username']
    ordering = ['-created_at']
    raw_id_fields = ['author']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informações do Post', {
            'fields': ('author', 'title', 'content')
        }),
        ('Datas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_like_count(self, obj):
        return obj.likes.count()
    get_like_count.short_description = 'Likes'
    
    def get_comment_count(self, obj):
        return obj.comments.filter(parent__isnull=True).count()
    get_comment_count.short_description = 'Comentários'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('author').prefetch_related('likes', 'comments')

@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'post', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'post__title']
    ordering = ['-created_at']
    raw_id_fields = ['user', 'post']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'post')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'post', 'parent', 'content_preview', 'is_edited', 'created_at', 'get_reply_count']
    list_filter = ['created_at', 'is_edited', 'user']
    search_fields = ['content', 'user__username', 'post__title']
    ordering = ['-created_at']
    raw_id_fields = ['user', 'post', 'parent']
    readonly_fields = ['created_at', 'updated_at', 'is_edited']
    
    fieldsets = (
        ('Informações do Comentário', {
            'fields': ('user', 'post', 'parent', 'content')
        }),
        ('Metadados', {
            'fields': ('is_edited', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """Exibe preview do conteúdo"""
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Conteúdo'
    
    def get_reply_count(self, obj):
        """Exibe número de respostas"""
        if obj.parent is None:
            return obj.replies.count()
        return '-'
    get_reply_count.short_description = 'Respostas'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'post', 'parent').prefetch_related('replies')