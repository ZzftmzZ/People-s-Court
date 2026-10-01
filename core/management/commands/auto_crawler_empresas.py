# pyrefly: ignore [missing-import]
import csv
import time
import re
import urllib.request
import json
import urllib.parse
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import User, CompanyProfile

class Command(BaseCommand):
    help = 'Crawler e Ingestor automatizado de empresas em lote com suporte a BrasilAPI/CNPJ, Rate Limiting e Bulk Creation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            type=str,
            default='empresas_exemplo.csv',
            help='Caminho para o arquivo CSV com lista de CNPJs ou empresas (Padrão: empresas_exemplo.csv)'
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.8,
            help='Tempo de espera em segundos entre cada requisição externa para evitar HTTP 429 (Padrão: 0.8s)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Tamanho do lote para transações otimizadas no banco de dados (Padrão: 50)'
        )

    def fetch_brasil_api_cnpj(self, cnpj_clean):
        """Consulta dados oficiais de empresa via BrasilAPI para o CNPJ fornecido."""
        url = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_clean}"
        headers = {'User-Agent': 'ProtejaJaCrawler/1.0'}
        req = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    return {
                        'name': data.get('nome_fantasia') or data.get('razao_social') or f"CNPJ {cnpj_clean}",
                        'category': data.get('cnae_fiscal_descricao') or 'Serviços Gerais',
                        'description': f"Razão Social: {data.get('razao_social', '')}. Situação Cadastral: {data.get('descricao_situacao_cadastral', 'Ativa')}. Município: {data.get('municipio', '')} - {data.get('uf', '')}."
                    }
        except Exception:
            pass
        return None

    def handle(self, *args, **options):
        csv_filepath = options['csv']
        delay = options['delay']
        batch_size = options['batch_size']

        self.stdout.write(self.style.NOTICE(f"=== Iniciando Auto Crawler de Empresas ==="))
        self.stdout.write(f"Arquivo CSV: {csv_filepath}")
        self.stdout.write(f"Delay entre requisições: {delay}s | Tamanho do Lote: {batch_size}\n")

        try:
            with open(csv_filepath, mode='r', encoding='utf-8') as file:
                reader = list(csv.DictReader(file))
        except FileNotFoundError:
            raise CommandError(f"Arquivo '{csv_filepath}' não foi encontrado na raiz do projeto!")
        except Exception as e:
            raise CommandError(f"Erro ao ler arquivo CSV: {str(e)}")

        total_rows = len(reader)
        self.stdout.write(self.style.SUCCESS(f"Total de registros encontrados no CSV: {total_rows}\n"))

        batch_records = []
        processed_count = 0
        success_count = 0
        skipped_count = 0

        for row in reader:
            processed_count += 1
            cnpj_raw = row.get('cnpj', '').strip()
            nome_raw = row.get('nome', '').strip() or row.get('nome_fantasia', '').strip()
            categoria_raw = row.get('categoria', '').strip()

            cnpj_clean = re.sub(r'\D', '', cnpj_raw)
            slug = f"cnpj_{cnpj_clean}" if cnpj_clean else re.sub(r'[^a-zA-Z0-9_]', '', nome_raw.lower().replace(' ', '_'))[:25]

            # Evita duplicados no banco
            if not slug or User.objects.filter(username=slug).exists():
                skipped_count += 1
                continue

            fetched_info = None
            if cnpj_clean and len(cnpj_clean) == 14:
                fetched_info = self.fetch_brasil_api_cnpj(cnpj_clean)
                time.sleep(delay)  # Rate limiting pra respeitar limites de requisições

            name = fetched_info['name'] if fetched_info else (nome_raw or f"Empresa {cnpj_clean}")
            category = fetched_info['category'] if fetched_info else (categoria_raw or "Varejo e Serviços")
            desc = fetched_info['description'] if fetched_info else f"Empresa cadastrada via lote automatizado (CNPJ: {cnpj_raw})."

            batch_records.append({
                'slug': slug,
                'name': name[:250],
                'category': category[:95],
                'description': desc
            })

            # Processamento otimizado em lote usando transação atômica
            if len(batch_records) >= batch_size or processed_count == total_rows:
                if batch_records:
                    with transaction.atomic():
                        for item in batch_records:
                            user = User.objects.create(
                                username=item['slug'],
                                role=User.Role.COMPANY
                            )
                            user.set_password('senha123')
                            user.save()

                            CompanyProfile.objects.create(
                                user=user,
                                name=item['name'],
                                category=item['category'],
                                description=item['description']
                            )
                            success_count += 1

                    batch_records.clear()

            # Log no console
            if processed_count % 5 == 0 or processed_count == total_rows:
                self.stdout.write(f"Progresso: {processed_count}/{total_rows} processados ({success_count} inseridos no banco, {skipped_count} ignorados)...")

        self.stdout.write(self.style.SUCCESS(f"\n✅ Concluído! Total no CSV: {total_rows} | Sucesso: {success_count} empresas cadastradas | Ignorados: {skipped_count}"))
