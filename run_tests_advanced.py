import os
import sys
import django
import unittest
from io import StringIO

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from django.test.runner import DiscoverRunner
from django.test import TestCase

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class FormattedTestResult(unittest.TestResult):
    """TestResult customizado com output formatado"""
    
    def __init__(self, stream=None, descriptions=None, verbosity=None):
        super().__init__(stream, descriptions, verbosity)
        self.test_number = 0
        self.test_results = []
    
    def startTest(self, test):
        super().startTest(test)
        self.test_number += 1
        self.current_test = test
    
    def addSuccess(self, test):
        super().addSuccess(test)
        test_name = self.get_test_name(test)
        print(f"{Colors.CYAN}Test {self.test_number}{Colors.ENDC} - {test_name}")
        print(f"{Colors.YELLOW}Running...{Colors.ENDC}")
        print(f"{Colors.GREEN}Pass ✅{Colors.ENDC}\n")
        self.test_results.append(('PASS', test_name, None))
    
    def addError(self, test, err):
        super().addError(test, err)
        test_name = self.get_test_name(test)
        error_msg = self.format_error(err)
        print(f"{Colors.CYAN}Test {self.test_number}{Colors.ENDC} - {test_name}")
        print(f"{Colors.YELLOW}Running...{Colors.ENDC}")
        print(f"{Colors.RED}Error ❌{Colors.ENDC}")
        print(f"{Colors.RED}{error_msg}{Colors.ENDC}\n")
        self.test_results.append(('ERROR', test_name, error_msg))
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        test_name = self.get_test_name(test)
        error_msg = self.format_error(err)
        print(f"{Colors.CYAN}Test {self.test_number}{Colors.ENDC} - {test_name}")
        print(f"{Colors.YELLOW}Running...{Colors.ENDC}")
        print(f"{Colors.RED}Fail ❌{Colors.ENDC}")
        print(f"{Colors.RED}{error_msg}{Colors.ENDC}\n")
        self.test_results.append(('FAIL', test_name, error_msg))
    
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        test_name = self.get_test_name(test)
        print(f"{Colors.CYAN}Test {self.test_number}{Colors.ENDC} - {test_name}")
        print(f"{Colors.YELLOW}Skipped ⚠️{Colors.ENDC}\n")
        self.test_results.append(('SKIP', test_name, reason))
    
    def get_test_name(self, test):
        """Extrai nome legível do teste"""
        doc = test.shortDescription()
        if doc:
            return doc
        method_name = str(test).split()[0]
        return method_name.replace('test_', '').replace('_', ' ').title()
    
    def format_error(self, err):
        """Formata erro de forma concisa"""
        exc_type, exc_value, exc_tb = err
        return f"{exc_type.__name__}: {str(exc_value)[:200]}"

class FormattedTestRunner(DiscoverRunner):
    """Test Runner customizado"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.verbosity = 0
    
    def run_suite(self, suite, **kwargs):
        """Executa suite de testes com resultado formatado"""
        result = FormattedTestResult()
        suite.run(result)
        return result

def print_header():
    """Imprime cabeçalho"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}CodeLeap Backend - Automated Test Suite{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*70}{Colors.ENDC}\n")

def print_summary(result):
    """Imprime resumo dos testes"""
    total = result.testsRun
    passed = total - len(result.failures) - len(result.errors) - len(result.skipped)
    failed = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped)
    
    print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}TEST SUMMARY{Colors.ENDC}")
    print(f"{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"Total Tests: {total}")
    print(f"{Colors.GREEN}Passed: {passed} ✅{Colors.ENDC}")
    if failed > 0:
        print(f"{Colors.RED}Failed: {failed} ❌{Colors.ENDC}")
    if errors > 0:
        print(f"{Colors.RED}Errors: {errors} 💥{Colors.ENDC}")
    if skipped > 0:
        print(f"{Colors.YELLOW}Skipped: {skipped} ⚠️{Colors.ENDC}")
    
    # Calcular porcentagem
    if total > 0:
        success_rate = (passed / total) * 100
        print(f"\n{Colors.BOLD}Success Rate: {success_rate:.1f}%{Colors.ENDC}")
    
    print(f"{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def run_coverage():
    """Executa coverage e mostra relatório"""
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}COVERAGE REPORT{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.ENDC}\n")
    
    # Executar coverage report
    os.system('coverage report --skip-covered')
    
    # Gerar HTML
    print(f"\n{Colors.CYAN}Generating HTML coverage report...{Colors.ENDC}")
    os.system('coverage html')
    print(f"{Colors.GREEN}✅ HTML report: htmlcov/index.html{Colors.ENDC}\n")

def main():
    """Função principal"""
    print_header()
    
    # Limpar coverage anterior
    print(f"{Colors.YELLOW}Cleaning previous coverage data...{Colors.ENDC}\n")
    os.system('coverage erase')
    
    # Configurar test runner
    runner = FormattedTestRunner(verbosity=0, interactive=False, keepdb=False)
    
    # Executar testes com coverage
    print(f"{Colors.YELLOW}Running tests with coverage...{Colors.ENDC}\n")
    
    # Descobrir e executar testes
    suite = runner.build_suite(['CodeLabTest'])
    
    # Executar com coverage
    import coverage
    cov = coverage.Coverage(source=['.'])
    cov.start()
    
    result = runner.run_suite(suite)
    
    cov.stop()
    cov.save()
    
    # Imprimir resumo
    print_summary(result)
    
    # Mostrar coverage
    run_coverage()
    
    # Retornar código de saída
    success = result.wasSuccessful()
    
    if success:
        print(f"{Colors.GREEN}{Colors.BOLD}All tests passed! 🎉{Colors.ENDC}\n")
    else:
        print(f"{Colors.RED}{Colors.BOLD}Some tests failed. Check errors above. 😞{Colors.ENDC}\n")
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()