# CodeLabTest/tests_complete.py

from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from CodeLabTest.models import User, Post, Like, Comment, Notification
import uuid

class AuthenticationTests(APITestCase):
    """Testes de autenticação"""
    
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.login_url = reverse('login')
    
    def test_user_registration(self):
        """Teste de registro de usuário"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'senha@123',
            'password_confirm': 'senha@123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
    
    def test_user_login(self):
        """Teste de login"""
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='senha@123'
        )
        
        data = {'username': 'testuser', 'password': 'senha@123'}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
    
    def test_invalid_login(self):
        """Teste de login inválido"""
        data = {'username': 'wrong', 'password': 'wrong'}
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PostTests(APITestCase):
    """Testes de posts"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='senha@123'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_create_post(self):
        """Teste de criação de post"""
        data = {
            'title': 'Test Post',
            'content': 'Test content'
        }
        response = self.client.post('/api/posts/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)
    
    def test_list_posts(self):
        """Teste de listagem de posts"""
        Post.objects.create(
            author=self.user,
            title='Test Post',
            content='Content'
        )
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_update_own_post(self):
        """Teste de atualização de próprio post"""
        post = Post.objects.create(
            author=self.user,
            title='Original',
            content='Content'
        )
        data = {'title': 'Updated', 'content': 'New content'}
        response = self.client.patch(f'/api/posts/{post.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.title, 'Updated')
    
    def test_cannot_update_others_post(self):
        """Teste que não pode editar post de outros"""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='senha@123'
        )
        post = Post.objects.create(
            author=other_user,
            title='Other Post',
            content='Content'
        )
        data = {'title': 'Hacked'}
        response = self.client.patch(f'/api/posts/{post.id}/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class LikeTests(APITestCase):
    """Testes de likes"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='senha@123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='senha@123'
        )
        self.post = Post.objects.create(
            author=self.user1,
            title='Test Post',
            content='Content'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user2)
    
    def test_like_post(self):
        """Teste de curtir post"""
        response = self.client.post(f'/api/posts/{self.post.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.post.likes.count(), 1)
    
    def test_cannot_like_twice(self):
        """Teste que não pode curtir duas vezes"""
        self.client.post(f'/api/posts/{self.post.id}/like/')
        response = self.client.post(f'/api/posts/{self.post.id}/like/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.post.likes.count(), 1)
    
    def test_unlike_post(self):
        """Teste de descurtir post"""
        Like.objects.create(user=self.user2, post=self.post)
        response = self.client.delete(f'/api/posts/{self.post.id}/unlike/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.post.likes.count(), 0)


class CommentTests(APITestCase):
    """Testes de comentários"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='senha@123'
        )
        self.post = Post.objects.create(
            author=self.user,
            title='Test Post',
            content='Content'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_create_comment(self):
        """Teste de criação de comentário"""
        data = {'content': 'Test comment'}
        response = self.client.post(f'/api/posts/{self.post.id}/comment/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)
    
    def test_reply_to_comment(self):
        """Teste de resposta a comentário"""
        comment = Comment.objects.create(
            user=self.user,
            post=self.post,
            content='Parent comment'
        )
        data = {'content': 'Reply'}
        response = self.client.post(f'/api/comments/{comment.id}/reply/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(comment.replies.count(), 1)


class NotificationTests(APITestCase):
    """Testes de notificações"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='senha@123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='senha@123'
        )
        self.post = Post.objects.create(
            author=self.user1,
            title='Test Post',
            content='Content'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user1)
    
    def test_like_creates_notification(self):
        """Teste que like cria notificação"""
        Like.objects.create(user=self.user2, post=self.post)
        Notification.create_like_notification(
            Like.objects.get(user=self.user2, post=self.post)
        )
        self.assertEqual(Notification.objects.count(), 1)
        notif = Notification.objects.first()
        self.assertEqual(notif.recipient, self.user1)
        self.assertEqual(notif.notification_type, 'like')
    
    def test_unread_count(self):
        """Teste de contagem de não lidas"""
        Notification.objects.create(
            recipient=self.user1,
            sender=self.user2,
            notification_type='like',
            post=self.post,
            message='Test'
        )
        response = self.client.get('/api/notifications/unread-count/')
        self.assertEqual(response.data['count'], 1)
    
    def test_mark_as_read(self):
        """Teste de marcar como lida"""
        notif = Notification.objects.create(
            recipient=self.user1,
            sender=self.user2,
            notification_type='like',
            post=self.post,
            message='Test'
        )
        response = self.client.post(f'/api/notifications/{notif.id}/mark-read/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)


class PaginationTests(APITestCase):
    """Testes de paginação"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='senha@123'
        )
        # Criar 30 posts
        for i in range(30):
            Post.objects.create(
                author=self.user,
                title=f'Post {i}',
                content='Content'
            )
        self.client = APIClient()
    
    def test_pagination_works(self):
        """Teste que paginação funciona"""
        response = self.client.get('/api/posts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 20)  # page_size padrão
    
    def test_custom_page_size(self):
        """Teste de tamanho de página customizado"""
        response = self.client.get('/api/posts/?page_size=5')
        self.assertEqual(len(response.data['results']), 5)


class SearchTests(APITestCase):
    """Testes de busca"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='senha@123'
        )
        Post.objects.create(
            author=self.user,
            title='Django Tutorial',
            content='Learn Django'
        )
        Post.objects.create(
            author=self.user,
            title='Python Basics',
            content='Learn Python'
        )
        self.client = APIClient()
    
    def test_global_search(self):
        """Teste de busca global"""
        response = self.client.get('/api/search/?q=django')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreater(response.data['total_results'], 0)
    
    def test_post_search(self):
        """Teste de busca em posts"""
        response = self.client.get('/api/search/posts/?q=python')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
    
    def test_search_suggestions(self):
        """Teste de sugestões"""
        response = self.client.get('/api/search/suggestions/?q=dja')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('suggestions', response.data)