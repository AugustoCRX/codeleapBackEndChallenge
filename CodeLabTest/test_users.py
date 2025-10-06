from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from CodeLabTest.models import User, Post, Like
import uuid

class LikeSystemTestCase(APITestCase):
    """
    Testes para o sistema de likes
    """
    
    def setUp(self):
        """
        Configura dados iniciais para os testes
        """
        # Criar usuários
        self.user1 = User.objects.create(
            username='user1',
            email='user1@test.com',
            password='pass123',
            first_name='User',
            last_name='One'
        )
        
        self.user2 = User.objects.create(
            username='user2',
            email='user2@test.com',
            password='pass123',
            first_name='User',
            last_name='Two'
        )
        
        # Criar post
        self.post = Post.objects.create(
            id=uuid.uuid4(),
            author=self.user1,
            title='Test Post',
            content=b'Test content'
        )
    
    def test_create_like(self):
        """
        Testa a criação de um like
        """
        like = Like.objects.create(user=self.user2, post=self.post)
        self.assertEqual(self.post.likes.count(), 1)
        self.assertEqual(like.user, self.user2)
        self.assertEqual(like.post, self.post)
    
    def test_unique_like_constraint(self):
        """
        Testa se um usuário não pode dar like duas vezes no mesmo post
        """
        Like.objects.create(user=self.user2, post=self.post)
        
        # Tentar criar outro like do mesmo usuário no mesmo post
        with self.assertRaises(Exception):
            Like.objects.create(user=self.user2, post=self.post)
    
    def test_multiple_users_like_same_post(self):
        """
        Testa se múltiplos usuários podem dar like no mesmo post
        """
        Like.objects.create(user=self.user1, post=self.post)
        Like.objects.create(user=self.user2, post=self.post)
        
        self.assertEqual(self.post.likes.count(), 2)
    
    def test_delete_like(self):
        """
        Testa a remoção de um like
        """
        like = Like.objects.create(user=self.user2, post=self.post)
        self.assertEqual(self.post.likes.count(), 1)
        
        like.delete()
        self.assertEqual(self.post.likes.count(), 0)
    
    def test_like_count_in_post(self):
        """
        Testa a contagem de likes em um post
        """
        # Criar 3 likes
        Like.objects.create(user=self.user1, post=self.post)
        Like.objects.create(user=self.user2, post=self.post)
        
        # Criar outro usuário para o terceiro like
        user3 = User.objects.create(
            username='user3',
            email='user3@test.com',
            password='pass123',
            first_name='User',
            last_name='Three'
        )
        Like.objects.create(user=user3, post=self.post)
        
        self.assertEqual(self.post.likes.count(), 3)
    
    def test_cascade_delete_post(self):
        """
        Testa se os likes são deletados quando o post é deletado
        """
        Like.objects.create(user=self.user2, post=self.post)
        self.assertEqual(Like.objects.count(), 1)
        
        self.post.delete()
        self.assertEqual(Like.objects.count(), 0)
    
    def test_cascade_delete_user(self):
        """
        Testa se os likes são deletados quando o usuário é deletado
        """
        Like.objects.create(user=self.user2, post=self.post)
        self.assertEqual(Like.objects.count(), 1)
        
        self.user2.delete()
        self.assertEqual(Like.objects.count(), 0)