#!/usr/bin/env python
"""
Script para resetar completamente o banco de dados de DESENVOLVIMENTO
ATENÇÃO: Este script vai DELETAR TODOS OS DADOS!
Uso: python reset_dev_database.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from django.core.management import call_command
from django.db import connection
from django.conf import settings

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header():
    print(f"\n{Colors.BOLD}{Colors.RED}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.RED}RESET DE BANCO DE DADOS - DESENVOLVIMENTO{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.RED}{'='*70}{Colors.ENDC}\n")
    print(f"{Colors.YELLOW}ATENÇÃO: Este script vai DELETAR TODOS OS DADOS!{Colors.ENDC}")
    print(f"{Colors.YELLOW}Use apenas em ambiente de DESENVOLVIMENTO!{Colors.ENDC}\n")

def confirm_reset():
    """Confirma se realmente quer resetar"""
    resposta = input(f"{Colors.RED}Tem certeza que deseja continuar? (digite 'SIM' em maiúsculas): {Colors.ENDC}")
    return resposta == 'SIM'

def drop_all_tables():
    """Dropa todas as tabelas do banco"""
    print(f"\n{Colors.CYAN}1. Dropando todas as tabelas...{Colors.ENDC}")
    
    with connection.cursor() as cursor:
        # PostgreSQL
        cursor.execute("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                    EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                END LOOP;
            END $$;
        """)
        print(f"   {Colors.GREEN}✓ Tabelas dropadas{Colors.ENDC}")
        
        # Dropar sequências
        cursor.execute("""
            DO $$ DECLARE
                r RECORD;
            BEGIN
                FOR r IN (SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public') LOOP
                    EXECUTE 'DROP SEQUENCE IF EXISTS ' || quote_ident(r.sequence_name) || ' CASCADE';
                END LOOP;
            END $$;
        """)
        print(f"   {Colors.GREEN}✓ Sequências dropadas{Colors.ENDC}")

def delete_migrations():
    """Deleta arquivos de migração (exceto __init__.py)"""
    print(f"\n{Colors.CYAN}2. Deletando arquivos de migração...{Colors.ENDC}")
    
    migrations_dir = os.path.join('CodeLabTest', 'migrations')
    
    if os.path.exists(migrations_dir):
        for filename in os.listdir(migrations_dir):
            if filename.endswith('.py') and filename != '__init__.py':
                filepath = os.path.join(migrations_dir, filename)
                os.remove(filepath)
                print(f"   {Colors.GREEN}✓ Deletado: {filename}{Colors.ENDC}")
    
    # Limpar __pycache__
    pycache_dir = os.path.join(migrations_dir, '__pycache__')
    if os.path.exists(pycache_dir):
        import shutil
        shutil.rmtree(pycache_dir)
        print(f"   {Colors.GREEN}✓ Cache limpo{Colors.ENDC}")

def delete_media_files():
    """Deleta arquivos de mídia (avatars, posts)"""
    print(f"\n{Colors.CYAN}3. Deletando arquivos de mídia...{Colors.ENDC}")
    
    media_root = settings.MEDIA_ROOT
    
    if os.path.exists(media_root):
        import shutil
        # Deletar conteúdo mas manter estrutura
        for item in os.listdir(media_root):
            item_path = os.path.join(media_root, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
                print(f"   {Colors.GREEN}✓ Deletado: {item}/{Colors.ENDC}")
        
        # Recriar estrutura
        os.makedirs(os.path.join(media_root, 'avatars'), exist_ok=True)
        os.makedirs(os.path.join(media_root, 'posts'), exist_ok=True)
        print(f"   {Colors.GREEN}✓ Estrutura de pastas recriada{Colors.ENDC}")

def create_migrations():
    """Cria novas migrações"""
    print(f"\n{Colors.CYAN}4. Criando novas migrações...{Colors.ENDC}")
    call_command('makemigrations', verbosity=1)
    print(f"   {Colors.GREEN}✓ Migrações criadas{Colors.ENDC}")

def apply_migrations():
    """Aplica as migrações"""
    print(f"\n{Colors.CYAN}5. Aplicando migrações...{Colors.ENDC}")
    call_command('migrate', verbosity=1)
    print(f"   {Colors.GREEN}✓ Migrações aplicadas{Colors.ENDC}")

def create_superuser():
    """Oferece criar superusuário"""
    print(f"\n{Colors.CYAN}6. Criar superusuário?{Colors.ENDC}")
    resposta = input(f"   Deseja criar um superusuário agora? (s/n): ")
    
    if resposta.lower() in ['s', 'sim', 'yes', 'y']:
        print(f"\n{Colors.YELLOW}Criando superusuário...{Colors.ENDC}")
        call_command('createsuperuser')
        print(f"   {Colors.GREEN}✓ Superusuário criado{Colors.ENDC}")
    else:
        print(f"   {Colors.YELLOW}⚠ Você pode criar depois com: python manage.py createsuperuser{Colors.ENDC}")

def print_summary():
    """Imprime resumo final"""
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.GREEN}RESET COMPLETO!{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.GREEN}{'='*70}{Colors.ENDC}\n")
    
    print(f"{Colors.CYAN}Próximos passos:{Colors.ENDC}")
    print(f"1. python manage.py runserver")
    print(f"2. Acessar: http://localhost:8000/admin/")
    print(f"3. Acessar: http://localhost:8000/api/docs/")
    print(f"\n{Colors.CYAN}Comandos úteis:{Colors.ENDC}")
    print(f"- python manage.py createsuperuser  (se não criou ainda)")
    print(f"- python run_tests_advanced.py      (rodar testes)")
    print()

def main():
    """Função principal"""
    print_header()
    
    # Confirmação
    if not confirm_reset():
        print(f"\n{Colors.YELLOW}Operação cancelada.{Colors.ENDC}\n")
        return
    
    try:
        # Executar limpeza
        drop_all_tables()
        delete_migrations()
        delete_media_files()
        create_migrations()
        apply_migrations()
        create_superuser()
        print_summary()
        
    except Exception as e:
        print(f"\n{Colors.RED}ERRO: {str(e)}{Colors.ENDC}\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
