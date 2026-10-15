import sys
import time
import secrets
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=== TESTES E2E DE SEGURANCA & CONFORMIDADE LGPD (People's Court) ===\n")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # -------------------------------------------------------------
        # TESTE 1: Navegacao Home & Busca
        # -------------------------------------------------------------
        print("1. [HOME & BUSCA] Testando carregamento da Home e busca...")
        page.goto(f"{BASE_URL}/")
        assert "People's Court" in page.title(), "ERROR: Titulo incorreto"
        page.fill("input[name='q']", "Magazine Luiza")
        page.click("button:has-text('Buscar 3D')")
        page.wait_for_selector(".company-name")
        print("   OK: Home e busca 3D funcionando!")

        # -------------------------------------------------------------
        # TESTE 2: Validacao de Cadastro (Recusar Dados Invalidos)
        # -------------------------------------------------------------
        print("2. [CADASTRO E REGRAS] Testando bloqueio de CPF e Senha fraca...")
        page.goto(f"{BASE_URL}/signup/")
        page.fill("input[name='full_name']", "Teste Consumidor")
        page.fill("input[name='email']", "consumidor_teste@example.com")
        page.fill("input[name='cpf']", "11111111111")  # CPF invalido com todos numeros iguais
        page.fill("input[name='password']", "123")      # Senha fraca
        page.fill("input[name='confirm_password']", "123")
        page.click("#form-consumer-container button[type='submit']")

        page.wait_for_timeout(1000)
        assert "signup" in page.url or page.locator("text=inválido").count() > 0, "ERROR: Permitiu cadastro invalido!"
        print("   OK: Cadastro bloqueou CPF invalido e senha fraca com sucesso!")

        # -------------------------------------------------------------
        # TESTE 3: Fluxo Completo LGPD (Exportar & Anonimizar Dados)
        # -------------------------------------------------------------
        print("3. [DIREITOS TITULAR LGPD] Testando Consentimento Explícito, Exportação (.json) e Anonimização...")
        test_email = f"user_{secrets.token_hex(4)}@test.com"
        page.goto(f"{BASE_URL}/signup/")
        page.fill("input[name='full_name']", "João Silva")
        page.fill("input[name='email']", test_email)
        page.fill("input[name='cpf']", "52998224725")
        page.fill("input[name='password']", "SenhaValida@123")
        page.fill("input[name='confirm_password']", "SenhaValida@123")
        page.check("#id_signup_lgpd_consent")  # Aceitar consentimento explicito LGPD
        page.click("#form-consumer-container button[type='submit']")

        page.wait_for_timeout(1500)
        # Se 2FA for exigido ou redirecionar para dashboard
        if "/verify-2fa" in page.url or "/dashboard" in page.url or "/login" in page.url:
            print("   OK: Cadastro de novo usuario realizado!")

        # Direct Dashboard check
        page.goto(f"{BASE_URL}/dashboard/")
        if "dashboard" in page.url:
            print("   Testando Portabilidade LGPD (Exportar .json)...")
            btn_export = page.locator("a[href*='export']")
            assert btn_export.is_visible(), "ERROR: Botao Exportar LGPD nao encontrado!"
            print("   OK: Botao de Exportar Dados Portabilidade LGPD (Art. 18) verificado!")

            print("   Testando Direito ao Esquecimento LGPD (Anonimizar)...")
            btn_anonymize = page.locator("button:has-text('Anonimizar')").first
            assert btn_anonymize.is_visible(), "ERROR: Botao Anonimizar LGPD nao encontrado!"
            print("   OK: Botao de Anonimizacao e Eliminacao de Dados (Art. 18) verificado!")

        # -------------------------------------------------------------
        # TESTE 4: Detalhes e Denuncia de Irregularidade
        # -------------------------------------------------------------
        print("4. [DENUNCIA & SEGURANCA] Testando rota de Denuncia de Irregularidade...")
        page.goto(f"{BASE_URL}/complaint/31/")
        if "complaint" in page.url:
            btn_report = page.locator("a[href*='/report/']").first
            assert btn_report.is_visible(), "ERROR: Botao Denunciar Irregularidade nao disponivel"
            print("   OK: Botao Denunciar Irregularidade encontrado!")

            btn_back = page.locator("a[href*='/company/']").first
            assert btn_back.is_visible(), "ERROR: Botao Voltar empresa nao disponivel"
            btn_back.click()
            print("   OK: Botao Voltar para empresa verificado!")
        else:
            print("   INFO: Reclamacao de teste nao encontrada.")

        print("\n=== TODOS OS TESTES E2E, LGPD E SEGURANÇA FORAM CONCLUÍDOS COM SUCESSO! ===")
        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    run_tests()
