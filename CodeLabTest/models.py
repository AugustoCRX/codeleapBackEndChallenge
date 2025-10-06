from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import uuid
import os

def user_avatar_path(instance, filename):
    """
    Caminho para salvar avatar do usuário
    uploads/avatars/user_123/filename.jpg
    """
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join('avatars', f'user_{instance.id}', filename)

def post_image_path(instance, filename):
    """
    Caminho para salvar imagem do post
    uploads/posts/post_uuid/filename.jpg
    """
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join('posts', str(instance.id), filename)

class UserManager(BaseUserManager):
    """
    Manager customizado para o modelo User
    """
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório')
        if not username:
            raise ValueError('O username é obrigatório')
        
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser precisa ter is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser precisa ter is_superuser=True')
        
        return self.create_user(username, email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuário customizado com suporte a JWT e avatar
    """
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to=user_avatar_path, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['-created_datetime']
    
    def __str__(self):
        return self.username
    
    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.username
    
    def get_short_name(self):
        return self.first_name or self.username
    
    def delete(self, *args, **kwargs):
        """
        Delete avatar quando usuário é deletado
        """
        if self.avatar:
            if os.path.isfile(self.avatar.path):
                os.remove(self.avatar.path)
        super().delete(*args, **kwargs)

class Post(models.Model):
    """
    Modelo de Post com suporte a imagem
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=255)
    content = models.TextField()
    image = models.ImageField(upload_to=post_image_path, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author']),
        ]

    def __str__(self):
        return self.title
    
    def delete(self, *args, **kwargs):
        """
        Delete imagem quando post é deletado
        """
        if self.image:
            if os.path.isfile(self.image.path):
                os.remove(self.image.path)
        super().delete(*args, **kwargs)

class Like(models.Model):
    """
    Modelo de Like
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.user.username} likes {self.post.title}'

class Comment(models.Model):
    """
    Modelo de Comentário com suporte a respostas
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='replies'
    )
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        if self.parent:
            return f'{self.user.username} replied to {self.parent.user.username}'
        return f'{self.user.username} commented on {self.post.title}'
    
    def save(self, *args, **kwargs):
        if self.pk:
            try:
                old_comment = Comment.objects.get(pk=self.pk)
                if old_comment.content != self.content:
                    self.is_edited = True
            except Comment.DoesNotExist:
                pass
        super().save(*args, **kwargs)
    
    @property
    def reply_count(self):
        return self.replies.count()
    
    @property
    def is_reply(self):
        return self.parent is not None
    
class Notification(models.Model):
    """
    Sistema de notificações
    """
    NOTIFICATION_TYPES = (
        ('like', 'Like em Post'),
        ('comment', 'Comentário em Post'),
        ('reply', 'Resposta em Comentário'),
        ('mention', 'Menção'),
        ('follow', 'Novo Seguidor'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        'User', 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    sender = models.ForeignKey(
        'User', 
        on_delete=models.CASCADE, 
        related_name='sent_notifications',
        null=True,
        blank=True
    )
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    
    # Referências genéricas
    post = models.ForeignKey(
        'Post', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='notifications'
    )
    comment = models.ForeignKey(
        'Comment', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='notifications'
    )
    
    message = models.TextField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f'{self.notification_type} para {self.recipient.username}'
    
    def mark_as_read(self):
        """Marca notificação como lida"""
        if not self.is_read:
            self.is_read = True
            from django.utils import timezone
            self.read_at = timezone.now()
            self.save()
    
    @staticmethod
    def create_like_notification(like):
        """Cria notificação quando alguém curte um post"""
        if like.user != like.post.author:
            message = f'{like.user.username} curtiu seu post "{like.post.title}"'
            Notification.objects.create(
                recipient=like.post.author,
                sender=like.user,
                notification_type='like',
                post=like.post,
                message=message
            )
    
    @staticmethod
    def create_comment_notification(comment):
        """Cria notificação quando alguém comenta em um post"""
        if comment.user != comment.post.author and not comment.parent:
            message = f'{comment.user.username} comentou no seu post "{comment.post.title}"'
            Notification.objects.create(
                recipient=comment.post.author,
                sender=comment.user,
                notification_type='comment',
                post=comment.post,
                comment=comment,
                message=message
            )
    
    @staticmethod
    def create_reply_notification(reply):
        """Cria notificação quando alguém responde um comentário"""
        if reply.parent and reply.user != reply.parent.user:
            message = f'{reply.user.username} respondeu seu comentário'
            Notification.objects.create(
                recipient=reply.parent.user,
                sender=reply.user,
                notification_type='reply',
                post=reply.post,
                comment=reply,
                message=message
            )