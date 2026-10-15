<div align="center">

# 🏛️ People's Court

**Plataforma de resolução de conflitos de consumo, transparência corporativa e conformidade com a LGPD.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![LGPD](https://img.shields.io/badge/LGPD-Compliant-success)](https://www.gov.br/cidadania/pt-br/acesso-a-informacao/lgpd)

</div>

---

## 📖 Sobre o Projeto

O **People's Court** conecta consumidores e empresas em um ambiente transparente e seguro para registrar, responder e avaliar reclamações. A plataforma foi construída com foco em **proteção de dados pessoais (LGPD)**, **prevenção de fraudes** e **rastreabilidade de ações**, com uma interface minimalista em modo escuro.

---

## 🌟 Recursos Principais

| Pilar | Descrição |
| :--- | :--- |
| 🎨 **Design Minimalista Dark Mode** | Interface responsiva em modo escuro, com paleta monocromática: preto `#000000`, branco `#ffffff` e cinza `#27272a`. |
| 🔐 **Autenticação Segura** | Cadastro, login, recuperação de senha por token e **verificação em duas etapas (2FA)** por e-mail. |
| 🪪 **Cadastro de Consumidor (LGPD)** | Validação de **CPF** pelo algoritmo Módulo 11, senha com regras de complexidade e **máscara de privacidade** na exibição do CPF (`***.456.789-**`). |
| 🏢 **Cadastro de Empresa** | Perfil de empresa com CNPJ, status de verificação e pontuação de reputação calculada a partir das reclamações. |
| 🔄 **Máquina de Estados de Casos** | Fluxo completo: `Em Aberto` → `Respondida` → `Contrarresposta` → `Avaliada` (nota de 0 a 10). |
| 🛡️ **Segurança de Sessão e Web** | Cookies `HttpOnly`, proteção CSRF, `X-Frame-Options: DENY`, `nosniff` e sanitização de conteúdo com **Bleach**. |
| 🔑 **Hashing de Senhas** | Hashers configurados: PBKDF2, Argon2 e BCrypt (SHA-256). |
| 🕵️ **Auditoria e Anti-Fraude** | Registro em `AuditLog` de ações relevantes, denúncias de reclamações (`Report`) e alertas de risco por empresa. |
| 🔎 **Busca e Autocomplete** | Busca de empresas com endpoint de autocomplete e cache para respostas rápidas. |
| 📰 **Conteúdo e Suporte** | Dicas de segurança, notícias e sistema de tickets de suporte. |

---

## 📋 Requisitos do Sistema

### ✅ Requisitos Funcionais

| ID | Requisito | Descrição |
| :--- | :--- | :--- |
| **RF01** | Cadastro de consumidor | O sistema deve permitir o cadastro de consumidores com nome, CPF válido (Módulo 11), e-mail e senha. |
| **RF02** | Cadastro de empresa | O sistema deve permitir o cadastro de empresas com perfil próprio, incluindo CNPJ e status de verificação. |
| **RF03** | Autenticação | O sistema deve permitir login e logout de usuários, com perfis distintos de consumidor e empresa. |
| **RF04** | Verificação em duas etapas (2FA) | O sistema deve enviar um código por e-mail e exigir sua confirmação para concluir o login. |
| **RF05** | Recuperação de senha | O usuário deve poder redefinir a senha por meio de um token enviado por e-mail. |
| **RF06** | Busca de empresas | O sistema deve permitir buscar empresas por nome, com autocomplete durante a digitação. |
| **RF07** | Perfil público da empresa | O sistema deve exibir o perfil da empresa com reputação, reclamações e alertas de risco. |
| **RF08** | Registro de reclamação | O consumidor autenticado deve poder abrir uma reclamação contra uma empresa, com título, descrição e categoria. |
| **RF09** | Detecção de duplicidade | O sistema deve identificar reclamações duplicadas do mesmo consumidor contra a mesma empresa em um intervalo de 7 dias. |
| **RF10** | Resposta da empresa | A empresa deve poder responder apenas às reclamações direcionadas a ela. |
| **RF11** | Contrarresposta do consumidor | O consumidor deve poder replicar a resposta da empresa. |
| **RF12** | Avaliação final | O consumidor deve poder avaliar o caso encerrado com nota de 0 a 10; a avaliação só é aceita após a empresa responder. |
| **RF13** | Máquina de estados | O sistema deve controlar o ciclo `Em Aberto` → `Respondida` → `Contrarresposta` → `Avaliada`. |
| **RF14** | Denúncia de reclamações | Usuários devem poder denunciar reclamações abusivas ou suspeitas, com motivo informado. |
| **RF15** | Pontuação de reputação | O sistema deve calcular automaticamente a reputação da empresa com base nas respostas e avaliações. |
| **RF16** | Alertas de fraude | O sistema deve calcular um índice de risco e sinalizar empresas com comportamento suspeito. |
| **RF17** | Suporte | Usuários devem poder abrir tickets de suporte e trocar mensagens. |
| **RF18** | Conteúdo informativo | O sistema deve disponibilizar páginas de dicas de segurança e notícias. |
| **RF19** | Paginação | Listagens de reclamações e resultados de busca devem ser paginadas (10 itens por página). |
| **RF20** | Feedback ao usuário | O sistema deve exibir mensagens de sucesso e erro após as principais ações. |

### 🛡️ Requisitos Não Funcionais

| ID | Categoria | Requisito |
| :--- | :--- | :--- |
| **RNF01** | Segurança | As senhas devem ser armazenadas apenas como hash, com regras de complexidade (mínimo de 8 caracteres, maiúsculas, minúsculas, números e caracteres especiais). |
| **RNF02** | Segurança | Cookies de sessão e CSRF devem usar `HttpOnly`; a aplicação deve enviar `X-Frame-Options: DENY` e `nosniff`. |
| **RNF03** | Segurança | Todo conteúdo enviado por usuários deve ser sanitizado (Bleach) para prevenir XSS. |
| **RNF04** | Segurança | Rotas sensíveis devem exigir autenticação e respeitar o perfil do usuário (consumidor ou empresa). |
| **RNF05** | Privacidade (LGPD) | O CPF deve ser exibido mascarado (`***.456.789-**`) e apenas dados estritamente necessários devem ser coletados. |
| **RNF06** | Auditabilidade | Ações relevantes (login, cadastro, denúncias e mudanças de status) devem ser registradas em `AuditLog`. |
| **RNF07** | Desempenho | Consultas frequentes devem usar índices de banco de dados, e o autocomplete deve usar cache (5 minutos). |
| **RNF08** | Usabilidade | A interface deve ser responsiva, minimalista e em modo escuro, com paleta monocromática. |
| **RNF09** | Portabilidade | O sistema deve rodar de forma nativa em Windows, Linux e macOS e também via Docker Compose. |
| **RNF10** | Compatibilidade | O sistema deve funcionar com Python 3.11+, Django 4.2 e PostgreSQL 15 (SQLite em desenvolvimento). |
| **RNF11** | Manutenibilidade | O código deve ser organizado em app Django modular (`core`) e coberto por testes automatizados. |
| **RNF12** | Configurabilidade | Banco de dados e envio de e-mail devem ser configuráveis por variáveis de ambiente. |

---

## 🛠️ Tecnologias Utilizadas

### Backend

- Python 3.11+
- Django 4.2 (ORM, autenticação e sistema de migrações)

### Banco de Dados

- SQLite (padrão no desenvolvimento local, sem configuração adicional)
- PostgreSQL 15 (ativado automaticamente ao definir a variável `POSTGRES_DB`, como no Docker Compose)

### Frontend

- HTML5 semântico com Django Templates
- CSS puro (Vanilla CSS) em tema escuro minimalista
- JavaScript

### Segurança

- Bleach (sanitização de HTML)
- Argon2 e BCrypt (hashers de senha configurados)
- Validação de CPF (Módulo 11) e máscara de privacidade LGPD
- Proteções nativas do Django (CSRF, XSS, clickjacking)

### Infraestrutura

- Docker e Docker Compose

---

## 🚀 Guia de Execução

Primeiro, clone o repositório e entre na pasta do projeto:

```bash
git clone https://github.com/SEU_USUARIO/People-s-Court.git
cd People-s-Court
```

> Substitua `SEU_USUARIO` pelo seu usuário do GitHub.

Escolha uma das duas opções abaixo.

---

### 🅰️ Opção A: Execução Nativa (Sem Docker)

**Pré-requisitos:** [Python 3.11+](https://www.python.org/downloads/) e `pip`.

Por padrão, o projeto usa **SQLite**, então não é necessário instalar o PostgreSQL.

#### 1. Criar e ativar o ambiente virtual

<details open>
<summary><b>🪟 Windows (PowerShell)</b></summary>

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Se o PowerShell bloquear a ativação, execute uma vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

No **Prompt de Comando (CMD)**, use:

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

</details>

<details>
<summary><b>🐧 Linux</b></summary>

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Em distribuições Debian/Ubuntu, se o módulo `venv` não existir:

```bash
sudo apt install python3-venv
```

</details>

<details>
<summary><b>🍎 macOS</b></summary>

```bash
python3 -m venv .venv
source .venv/bin/activate
```

</details>

Com o ambiente ativo, o terminal exibirá o prefixo `(.venv)`.

#### 2. Instalar as dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Aplicar as migrações

```bash
python manage.py migrate
```

#### 4. (Opcional) Popular o banco com dados de exemplo

```bash
python manage.py seed_data
```

#### 5. Iniciar o servidor

```bash
python manage.py runserver
```

Acesse: **http://127.0.0.1:8000**

> 💡 **Código 2FA em desenvolvimento:** por padrão, os e-mails são enviados para o **console**. O código de verificação em duas etapas aparecerá no terminal onde o servidor está rodando.

---

### 🅱️ Opção B: Execução com Docker (Docker Compose)

**Pré-requisito:** [Docker](https://docs.docker.com/get-docker/) com Docker Compose (Docker Desktop no Windows e macOS; Docker Engine no Linux).

O comando é o mesmo em **Windows, Linux e macOS**.

#### 1. Construir e subir o ambiente completo

```bash
docker-compose up --build
```

Em versões recentes do Docker, o equivalente é `docker compose up --build`.

Isso inicia dois serviços:

| Serviço | Descrição | Porta no host |
| :--- | :--- | :--- |
| `db` | PostgreSQL 15 | `5433` |
| `web` | Aplicação Django | `8001` |

#### 2. Aplicar as migrações (em outro terminal)

Na primeira execução, com os containers ativos:

```bash
docker-compose exec web python manage.py migrate
```

#### 3. Acessar a aplicação

Acesse: **http://localhost:8001**

#### Comandos úteis

```bash
# Parar os containers
docker-compose down

# Parar e remover também o volume do banco de dados
docker-compose down -v
```

---

## 🧪 Testes Automatizados

Com o ambiente configurado (Opção A com o `.venv` ativo, ou dentro do container), execute:

```bash
python manage.py test core
```

Com Docker:

```bash
docker-compose exec web python manage.py test core
```

A suíte cobre validação de formulários, permissões de acesso, cálculo de reputação, paginação, mensagens do sistema, validação de CPF, política de senhas e máscara LGPD.

---

## 📁 Estrutura do Projeto

```text
People-s-Court/
├── config/              # Configurações do projeto Django (settings, urls, wsgi/asgi)
├── core/                # App principal (models, views, forms, urls, testes)
│   ├── management/      # Comandos personalizados (seed_data, auto_crawler_empresas)
│   └── migrations/      # Migrações do banco de dados
├── templates/           # Templates HTML (base e páginas do app core)
├── Dockerfile           # Imagem da aplicação
├── docker-compose.yml   # Orquestração (web + PostgreSQL)
├── requirements.txt     # Dependências Python
└── manage.py            # Utilitário de linha de comando do Django
```

---

## ⚠️ Aviso para Produção

As configurações atuais são voltadas ao **desenvolvimento**. Antes de publicar, defina `DEBUG = False`, configure `ALLOWED_HOSTS`, mova a `SECRET_KEY` e as credenciais do banco para variáveis de ambiente e configure um backend SMTP real para o envio dos códigos 2FA.

---

<div align="center">

Feito com 🖤 e Django.

</div>
