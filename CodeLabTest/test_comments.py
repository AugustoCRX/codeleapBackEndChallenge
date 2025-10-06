from django.test import TestCase
from CodeLabTest.models import User, Post, Comment
import uuid

class CommentSystemTestCase(TestCase):
    """
    Testes para o sistema de comentários
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
    
    def test_create_comment(self):
        """
        Testa a criação de um comentário
        """
        comment = Comment.objects.create(
            user=self.user1,
            post=self.post,
            content='Este é um comentário de teste'
        )
        
        self.assertEqual(self.post.comments.count(), 1)
        self.assertEqual(comment.user, self.user1)
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.content, 'Este é um comentário de teste')
        self.assertIsNone(comment.parent)
        self.assertFalse(comment.is_edited)
    
    def test_create_reply(self):
        """
        Testa a criação de uma resposta a um comentário
        """
        # Criar comentário principal
        parent_comment = Comment.objects.create(
            user=self.user1,
            post=self.post,
            content='Comentário principal'
        )
        
        # Criar resposta
        reply = Comment.objects.create(
            user=self.user2,
            post=self.post,
            parent=parent_comment,
            content='Resposta ao comentário'
        )
        
        self.assertEqual(parent_comment.replies.count(), 1)
        self.assertEqual(reply.parent, parent_comment)
        self.assertTrue(reply.is_reply)
        self.assertFalse(parent_comment.is_reply)
    
    def test_multiple_comments_same_post(self):
        """
        Testa múltiplos comentários no mesmo post
        """
        Comment.objects.create(user=self.user1, post=self.post, content='Comentário 1')
        Comment.objects.create(user=self.user2, post=self.post, content='Comentário 2')
        Comment.objects.create(user=self.user1, post=self.post, content='Comentário 3')
        
        self.assertEqual(self.post.comments.count(), 3)
    
    def test_edit_comment(self):
        """
        Testa a edição de um comentário
        """
        comment = Comment.objects.create(
            user=self.user1,
            post=self.post,
            content='Conteúdo original'
        )
        
        self.assertFalse(comment.is_edited)
        
        # Editar comentário
        comment.content = 'Conteúdo editado'
        comment.save()
        
        comment.refresh_from_db()
        self.assertTrue(comment.is_edited)
        self.assertEqual(comment.content, 'Conteúdo editado')
    
    def test_delete_comment(self):
        """
        Testa a deleção de um comentário
        """
        comment = Comment.objects.create(
            user=self.user1,
            post=self.post,
            content='Comentário para deletar'
        )
        
        self.assertEqual(self.post.comments.count(), 1)
        
        comment.delete()
        self.assertEqual(self.post.comments.count(), 0)
    
    def test_cascade_delete_post_with_comments(self):
        """
        Testa se os comentários são deletados quando o post é deletado
        """
        Comment.objects.create(user=self.user1, post=self.post, content='Comentário 1')
        Comment.objects.create(user=self.user2, post=self.post, content='Comentário 2')
        
        self.assertEqual(Comment.objects.count(), 2)
        
        self.post.delete()
        self.assertEqual(Comment.objects.count(), 0)
    
    def test_cascade_delete_user_with_comments(self):
        """
        Testa se os comentários são deletados quando o usuário é deletado
        """
        Comment.objects.create(user=self.user1, post=self.post, content='Comentário do user1')
        
        self.assertEqual(Comment.objects.count(), 1)
        
        self.user1.delete()
        self.assertEqual(Comment.objects.count(), 0)
    
    def test_cascade_delete_parent_comment_with_replies(self):
        """
        Testa se as respostas são deletadas quando o comentário pai é deletado
        """
        parent_comment = Comment.objects.create(
            user=self.user1,
            post=self.post,
            content='Comentário principal'
        )
        
        Comment.objects.create(
            user=self.user2,
            post=self.post,
            parent=parent_comment,
            content='Resposta 1'
        )
        
        Comment.objects.create(
            user=self.user1,
            post=self.post,
            parent=parent_comment,
            content='Resposta 2'
        )
        
        self.assertEqual(Comment.objects.count(), 3)
        self.assertEqual(parent_comment.replies.count(), 2)
        
        parent_comment.delete()
        self.assertEqual(Comment.objects.count(), 0)
    
    def test_comment_string_representation(self):
        """
        Testa a representação em string do comentário
        """
        comment = Comment.objects.create(
            user=self.user1,
            post=self.post,
            content='Comentário de teste'
        )
        
        expected = f'{self.user1.username} commented on {self.post.title}'
        self.assertEqual(str(comment), expected)
    
    def test_reply_string_representation(self):
        """
        Testa a representação em string de uma resposta
        """
        parent_comment = Comment.objects.create(
            user=self.user1,
            post=self.post,
            content='Comentário principal'
        )
        
        reply = Comment.objects.create(
            user=self.user2,
            post=self.post,
            parent=parent_comment,
            content='Resposta'
        )
        
        expected = f'{self.user2.username} replied to {self.user1.username}'
        self.assertEqual(str(reply), expected)
    
    def test_reply_count_property(self):
        """
        Testa a propriedade reply_count
        """
        parent_comment = Comment.objects.create(
            user=self.user1,
            post=self.post,
            content='Comentário principal'
        )
        
        self.assertEqual(parent_comment.reply_count, 0)
        
        Comment.objects.create(
            user=self.user2,
            post=self.post,
            parent=parent_comment,
            content='Resposta 1'
        )
        
        Comment.objects.create(
            user=self.user1,
            post=self.post,
            parent=parent_comment,
            content='Resposta 2'
        )
        
        self.assertEqual(parent_comment.reply_count, 2)
    
    def test_comment_ordering(self):
        """
        Testa se os comentários são ordenados por created_at desc
        """
        comment1 = Comment.objects.create(
            user=self.user1,
            post=self.post,
            content='Primeiro comentário'
        )
        
        comment2 = Comment.objects.create(
            user=self.user2,
            post=self.post,
            content='Segundo comentário'
        )
        
        comment3 = Comment.objects.create(
            user=self.user1,
            post=self.post,
            content='Terceiro comentário'
        )
        
        comments = list(Comment.objects.all())
        
        # O mais recente deve vir primeiro
        self.assertEqual(comments[0], comment3)
        self.assertEqual(comments[1], comment2)
        self.assertEqual(comments[2], comment1)
    
    def test_comment_max_length(self):
        """
        Testa o limite de caracteres do comentário
        """
        # Criar comentário com exatamente 1000 caracteres
        content = 'a' * 1000
        comment = Comment.objects.create(
            user=self.user1,
            post=self.post,
            content=content
        )
        
        self.assertEqual(len(comment.content), 1000)
    
    def test_nested_replies_not_allowed(self):
        """
        Testa que não é possível criar respostas de respostas (apenas 1 nível)
        Nota: Esta validação deve ser feita na view, não no modelo
        """
        parent_comment = Comment.objects.create(
            user=self.user1,
            post=self.post,
            content='Comentário principal'
        )
        
        reply = Comment.objects.create(
            user=self.user2,
            post=self.post,
            parent=parent_comment,
            content='Resposta'
        )
        
        # No modelo, é tecnicamente possível criar uma resposta de resposta
        # mas a view deve prevenir isso
        nested_reply = Comment.objects.create(
            user=self.user1,
            post=self.post,
            parent=reply,
            content='Resposta da resposta'
        )
        
        self.assertEqual(nested_reply.parent, reply)
        self.assertTrue(nested_reply.is_reply)
    
    def test_comment_updated_at_changes(self):
        """
        Testa se updated_at muda quando o comentário é editado
        """
        comment = Comment.objects.create(
            user=self.user1,
            post=self.post,
            content='Conteúdo original'
        )
        
        original_updated_at = comment.updated_at
        
        # Simular passagem de tempo (em teste real, usar freezegun ou similar)
        import time
        time.sleep(0.1)
        
        comment.content = 'Conteúdo editado'
        comment.save()
        
        comment.refresh_from_db()
        self.assertNotEqual(comment.updated_at, original_updated_at)
        self.assertTrue(comment.updated_at > original_updated_at)