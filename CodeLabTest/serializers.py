from rest_framework import serializers
from django.contrib.auth import authenticate
from CodeLabTest.models import User, Post, Like, Comment, Notification

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password': 'As senhas não coincidem'})
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            
            if not user:
                raise serializers.ValidationError('Credenciais inválidas')
            
            if not user.is_active:
                raise serializers.ValidationError('Usuário inativo')
            
            data['user'] = user
        else:
            raise serializers.ValidationError('Username e password são obrigatórios')
        
        return data

class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    post_count = serializers.IntegerField(source='posts.count', read_only=True)
    comment_count = serializers.IntegerField(source='comments.count', read_only=True)
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name', 'bio',
                  'avatar', 'avatar_url', 'created_datetime', 'post_count', 'comment_count']
        read_only_fields = ['id', 'created_datetime']
    
    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
        return None

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'bio']
        extra_kwargs = {
            'email': {'required': False},
        }

class AvatarUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['avatar']
    
    def validate_avatar(self, value):
        # Validar tamanho do arquivo (máximo 2MB)
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError('O avatar não pode ser maior que 2MB')
        
        # Validar tipo de arquivo
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError('Apenas arquivos JPEG, PNG e WebP são permitidos')
        
        return value

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    new_password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})
    
    def validate(self, data):
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({'new_password': 'As senhas não coincidem'})
        return data
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Senha atual incorreta')
        return value

class PostSerializer(serializers.ModelSerializer):
    like_count = serializers.IntegerField(source='likes.count', read_only=True)
    comment_count = serializers.IntegerField(source='comments.count', read_only=True)
    is_liked = serializers.SerializerMethodField()
    author_name = serializers.CharField(source='author.username', read_only=True)
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'author', 'author_name', 'title', 'content', 'image', 'image_url',
            'created_at', 'updated_at', 'like_count', 'comment_count', 'is_liked'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return Like.objects.filter(user=request.user, post=obj).exists()
        return False
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None
    
    def validate_image(self, value):
        if value:
            # Validar tamanho do arquivo (máximo 5MB)
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError('A imagem não pode ser maior que 5MB')
            
            # Validar tipo de arquivo
            allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp']
            if value.content_type not in allowed_types:
                raise serializers.ValidationError('Apenas arquivos JPEG, PNG e WebP são permitidos')
        
        return value

class CommentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    reply_count = serializers.IntegerField(read_only=True)
    is_reply = serializers.BooleanField(read_only=True)
    replies = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'user_name', 'post', 'parent', 
            'content', 'created_at', 'updated_at', 'is_edited',
            'reply_count', 'is_reply', 'replies'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'is_edited']
    
    def get_replies(self, obj):
        if obj.parent is None:
            replies = obj.replies.all()[:5]
            return CommentReplySerializer(replies, many=True).data
        return []

class CommentReplySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'user_name', 'content', 
            'created_at', 'updated_at', 'is_edited'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at', 'is_edited']

class LikeSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    post_title = serializers.CharField(source='post.title', read_only=True)
    
    class Meta:
        model = Like
        fields = ['id', 'user', 'user_name', 'post', 'post_title', 'created_at']
        read_only_fields = ['user', 'created_at']

class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer para notificações
    """
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_avatar = serializers.SerializerMethodField()
    post_title = serializers.CharField(source='post.title', read_only=True)
    post_id = serializers.UUIDField(source='post.id', read_only=True)
    comment_content = serializers.SerializerMethodField()
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'sender', 'sender_username', 
            'sender_avatar', 'post_id', 'post_title', 'comment_content',
            'message', 'is_read', 'created_at', 'read_at', 'time_ago'
        ]
        read_only_fields = ['id', 'created_at', 'read_at']
    
    def get_sender_avatar(self, obj):
        if obj.sender and obj.sender.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.sender.avatar.url)
        return None
    
    def get_comment_content(self, obj):
        if obj.comment:
            content = obj.comment.content
            return content[:100] + '...' if len(content) > 100 else content
        return None
    
    def get_time_ago(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.created_at)