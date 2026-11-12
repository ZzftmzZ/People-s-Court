<div align="center">

# ⚖️ People's Court

**Plataforma de Resolução de Conflitos, Mediação 3D e Governança Corporativa com Conformidade à LGPD**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/ZzftmzZ/People-s-Court/actions)
[![W3C Validation](https://img.shields.io/badge/W3C-Valid_HTML5-success?style=for-the-badge&logo=w3c&logoColor=white)](https://validator.w3.org/nu/?doc=https%3A%2F%2Fpeople-s-court.onrender.com%2F)
[![Lighthouse](https://img.shields.io/badge/Lighthouse-Passing-00CC66?style=for-the-badge&logo=lighthouse&logoColor=white)](https://github.com/ZzftmzZ/People-s-Court/actions)

<br>

### 🌐 Demonstração Online em Produção

<a href="https://people-s-court.onrender.com/">
  <img src="https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=https://people-s-court.onrender.com/&color=ffffff&bgcolor=0d1117" alt="QR Code People's Court" width="160" height="160" style="border-radius: 8px;">
</a>

<p align="center">
  📱 <b>Escaneie o QR Code ou clique no botão abaixo para acessar o sistema:</b><br><br>
  <a href="https://people-s-court.onrender.com/">
    <img src="https://img.shields.io/badge/🚀_ACESSAR_APLICAÇÃO_NO_RENDER-0070F3?style=for-the-badge&logo=render&logoColor=white" alt="Abrir Demonstração">
  </a>
</p>

</div>

---

## 📖 Sobre o Projeto

O **People's Court** é uma plataforma concebida para aproximar consumidores e corporações em um ambiente digital transparente, confiável e imersivo para registrar, gerenciar, responder e auditar reclamações. O ecossistema foi projetado segundo os mais rigorosos padrões da indústria:

- 🛡️ **Conformidade com a LGPD:** Máscaras de dados sensíveis (CPF mascarado como `***.456.789-**`) e coleta mínima de dados.
- 🕵️ **Auditoria e Rastreabilidade:** Registro de eventos críticos em `AuditLog` com assinatura criptográfica SHA-256 imutável.
- ⚖️ **Mecanismos Antifraude:** Avaliação algorítmica de risco e detecção de duplicidades.
- 🎨 **Interface Imersiva 3D:** Experiência visual Dark Minimalista desenvolvida com **Three.js** e animações de alta performance com **GSAP (ScrollTrigger)**.

---

## 🌟 Funcionalidades e Arquitetura

| Módulo | Descrição Técnica |
| :--- | :--- |
| 🎨 **Design 3D Dark** | Interface responsiva com partículas WebGL (Three.js), microinterações GSAP e cards com efeito tilt 3D. |
| 🔐 **Segurança & 2FA** | Autenticação robusta com recuperação segura de senha e verificação em duas etapas (2FA) via e-mail. |
| 🏢 **SSO Corporativo** | Integração empresarial com suporte a login federado (OAuth2 / SAML). |
| 🤖 **Mediação Assistida por IA** | Auxílio ao consumidor na descrição objetiva e estruturada de incidentes de consumo. |
| 🔄 **Ciclo de Mediação** | Máquina de estados finitos: `Em Aberto` ➔ `Respondida` ➔ `Contrarresposta` ➔ `Avaliada` (0 a 10). |
| 🌐 **Busca Inteligente** | Autocomplete em tempo real com cache e fallback para indexação dinâmica. |
| 📜 **Certificação Digital** | Certificado imutável para reclamações resolvidas com identificador único e hash SHA-256. |
| 🛡️ **Segurança Defensiva** | Senhas protegidas com algoritmo **Argon2**, proteção contra CSRF/XSS, headers HSTS e Content Security Policy (CSP). |

---

## 📋 Requisitos do Sistema

### ✅ Requisitos Funcionais (RF)

| ID | Requisito | Descrição |
| :--- | :--- | :--- |
| **RF01** | Cadastro de Consumidor | Cadastro de cidadãos com validação estrita de CPF (Módulo 11) e senhas fortes. |
| **RF02** | Cadastro de Empresa | Cadastro corporativo com CNPJ verificado e painel de reputação auditada. |
| **RF03** | Controle de Acesso | Perfis e permissões granulares entre Consumidor, Empresa e Administrador. |
| **RF04** | Autenticação 2FA | Envio de código dinâmico descartável para validação de identidade no login. |
| **RF05** | Recuperação de Conta | Redefinição de credenciais por tokens criptográficos temporários. |
| **RF06** | Busca Preditiva | Busca por empresas com autocomplete otimizado e crawler auxiliar. |
| **RF07** | Perfil Corporativo | Painel público exibindo pontuação, histórico de atendimento e selos de conformidade. |
| **RF08** | Abertura de Casos | Registro estruturado de reclamações com categoria, empresa e evidências. |
| **RF09** | Filtro de Duplicidade | Bloqueio de reclamações idênticas consecutivas para a mesma empresa. |
| **RF10** | Réplica e Tréplica | Canal bilateral de diálogo entre o consumidor e a ouvidoria da empresa. |
| **RF11** | Encerramento e Nota | Avaliação de resolução com pontuação de 0 a 10 impactando a reputação da empresa. |
| **RF12** | Certificado de Resolução | Emissão de comprovante em PDF com hash SHA-256 para fins jurídicos e de compliance. |

### 🛡️ Requisitos Não Funcionais (RNF)

| ID | Categoria | Especificação |
| :--- | :--- | :--- |
| **RNF01** | Segurança | Armazenamento de senhas exclusivamente via **Argon2** com fator de custo elevado. |
| **RNF02** | Proteção de Dados | Conformidade com a **LGPD** mascarando identificadores fiscais e dados pessoais. |
| **RNF03** | Headers HTTP | `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff` e `Strict-Transport-Security`. |
| **RNF04** | Qualidade de Código | Pipeline com validação W3C HTML5 oficial e Lighthouse CI com score superior a 85%. |
| **RNF05** | Portabilidade | Totalmente containerizado via Docker e orquestrado por Docker Compose. |
| **RNF06** | Desempenho | Assets otimizados localmente e estratégia de cache em memória para requisições frequentes. |

---

## 🛠️ Tecnologias e Ferramental

```text
├── Back-End: Python 3.11+, Django 4.2+, Gunicorn, Argon2
├── Front-End: HTML5 Semântico, CSS3 Moderno, JavaScript (ES6+), Three.js (WebGL), GSAP
├── Banco de Dados: PostgreSQL 15 (Produção), SQLite (Desenvolvimento)
├── DevOps & Cloud: Docker, Docker Compose, GitHub Actions (CI/CD), Render Blueprint
└── Qualidade: Lighthouse CI, Nu W3C HTML Validator, Django Test Framework
```

---

## 🚀 Guia de Execução Local

### Pré-requisitos
* Git instalado
* Python 3.11+ ou Docker & Docker Compose

```bash
# Clone o repositório
git clone https://github.com/ZzftmzZ/People-s-Court.git
cd People-s-Court
```

### 🅰️ Opção 1: Execução Nativa com Python

```powershell
# 1. Crie e ative o ambiente virtual (Windows PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Instale as dependências
pip install --upgrade pip
pip install -r requirements.txt

# 3. Execute as migrações do banco
python manage.py migrate

# 4. (Opcional) Popule o banco com dados demonstrativos
python manage.py seed_data

# 5. Inicie o servidor
python manage.py runserver
```
> Acesse: **http://127.0.0.1:8000**

---

### 🅱️ Opção 2: Execução com Docker Compose

```bash
# Constrói a imagem e sobe a aplicação + PostgreSQL
docker-compose up --build
```
> Acesse: **http://localhost:8001**

---

## 🧪 Testes Automatizados

A aplicação possui suíte de testes unitários e de integração cobrindo fluxos de permissão, validação de CPF, integridade LGPD e cálculo de reputação:

```bash
# Execução nativa:
python manage.py test core

# Execução dentro do container Docker:
docker-compose exec web python manage.py test core
```

---

## 📁 Estrutura de Diretórios

```text
People-s-Court/
├── .github/              # Workflows de CI/CD (Lighthouse, W3C Validator)
├── config/               # Configurações centrais do Django (settings, urls, wsgi)
├── core/                 # Aplicação central (models, views, forms, urls, testes)
│   ├── management/       # Comandos CLI personalizados (seed_data, crawler)
│   └── migrations/       # Versionamento do esquema de banco de dados
├── static/               # Assets estáticos (estilos, cenas 3D, ícones)
│   ├── css/              # Estilos modulares em tema dark
│   ├── js/               # Scripts de cena (pc-scene.js) e animação (pc-motion.js)
│   └── vendor/           # Three.js, GSAP, ScrollTrigger locais
├── templates/            # Templates HTML semânticos renderizados pelo Django
├── Dockerfile            # Configuração de build do contêiner Docker
├── docker-compose.yml    # Orquestração do ambiente Web + Banco PostgreSQL
├── render.yaml           # Infraestrutura como código (IaC) para o Render
└── requirements.txt      # Manifesto de dependências do Python
```

---

<div align="center">

Desenvolvido por **[Cauê Mateus Gil](https://github.com/ZzftmzZ)**  
*Engenheiro de Software & Desenvolvedor Full Stack*

</div>
