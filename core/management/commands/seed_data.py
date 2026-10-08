# pyrefly: ignore [missing-import]
from django.core.management.base import BaseCommand
from core.models import User, CompanyProfile, ConsumerProfile, Complaint, Message

class Command(BaseCommand):
    help = 'Popula o banco de dados com mais de 100 empresas famosas do Brasil e dados de teste'

    def handle(self, *args, **kwargs):
        import os
        admin_pw = os.environ.get('SEED_ADMIN_PASSWORD', 'Admin@Veritas2026!')
        admin, created = User.objects.get_or_create(
            username='admin', defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True})
        if created:
            admin.set_password(admin_pw)
            admin.save()
            self.stdout.write("Superusuário 'admin' criado (altere a senha em produção: SEED_ADMIN_PASSWORD).")
        self.stdout.write("Gerando 100+ empresas brasileiras no banco de dados...")

        companies_list = [
            # E-commerce & Eletrônicos
            ('Mercado Livre', 'E-commerce e Marketplaces', 'Maior plataforma de e-commerce da América Latina.'),
            ('Amazon Brasil', 'E-commerce e Marketplaces', 'Líder global em e-commerce e serviços digitais.'),
            ('Magazine Luiza (Magalu)', 'Varejo e E-commerce', 'Rede varejista brasileira de eletrônicos e utilidades.'),
            ('Shopee Brasil', 'E-commerce e Marketplaces', 'Plataforma global de compras online com cupons.'),
            ('Casas Bahia', 'Varejo e E-commerce', 'Tradicional rede de móveis e eletrodomésticos.'),
            ('Americanas.com', 'E-commerce e Marketplaces', 'Grande portal de e-commerce e variedades.'),
            ('Submarino', 'E-commerce e Marketplaces', 'Loja online de livros, games e tecnologia.'),
            ('Shoptime', 'E-commerce e Marketplaces', 'Canal de TV e loja virtual de utilidades domésticas.'),
            ('Kabum!', 'Informática e E-sports', 'Maior e-commerce de tecnologia e e-sports da América Latina.'),
            ('Pichau Informática', 'Informática e Hardware', 'Loja especializada em hardware e computadores gamer.'),
            ('TerabyteShop', 'Informática e Hardware', 'E-commerce focado em hardware e PCs personalizados.'),
            ('Shein Brasil', 'Moda e E-commerce', 'Varejista global de moda e vestuário online.'),
            ('AliExpress', 'E-commerce Internacional', 'Compras internacionais com entregas diretas.'),
            ('Netshoes', 'Artigos Esportivos', 'Maior e-commerce de artigos esportivos do Brasil.'),
            ('Centauro', 'Artigos Esportivos', 'Rede de lojas de vestuário e equipamentos esportivos.'),
            ('Dafiti', 'Moda e Calçados', 'Portal de moda, calçados e acessórios.'),
            ('Enjoei', 'Marketplace C2C', 'Plataforma de compra e venda de produtos usados.'),
            ('OLX Brasil', 'Classificados Online', 'Maior plataforma de compra e venda de usados.'),
            ('Elo7', 'Artesanato e Personalizados', 'Marketplace de produtos artesanais e personalizados.'),
            ('Carrefour Brasil', 'Supermercados e E-commerce', 'Rede de hipermercados e loja virtual.'),
            ('Extra.com.br', 'Supermercados e Varejo', 'E-commerce de alimentos e eletrônicos.'),
            ('Ponto (Ponto Frio)', 'Varejo e Eletrônicos', 'Rede varejista focada em eletrodomésticos.'),

            # Bancos & Finanças
            ('Nubank', 'Bancos Digitais', 'Pioneiro em cartões sem anuidade e conta digital.'),
            ('Itaú Unibanco', 'Bancos Tradicionais', 'Maior conglomerado financeiro privado do país.'),
            ('Bradesco', 'Bancos Tradicionais', 'Uma das maiores instituições financeiras do Brasil.'),
            ('Banco do Brasil', 'Bancos Públicos', 'Primeiro banco público do país.'),
            ('Caixa Econômica Federal', 'Bancos Públicos', 'Banco responsável pela habitação e benefícios sociais.'),
            ('Santander Brasil', 'Bancos Tradicionais', 'Banco global com forte atuação no mercado brasileiro.'),
            ('Banco Inter', 'Bancos Digitais', 'Plataforma digital completa de serviços financeiros.'),
            ('C6 Bank', 'Bancos Digitais', 'Banco digital para pessoa física e jurídica.'),
            ('PagBank (PagSeguro)', 'Pagamentos Digitais', 'Soluções de pagamento, maquininhas e conta digital.'),
            ('Mercado Pago', 'Carteiras Digitais', 'Serviço de pagamentos e carteira do Mercado Livre.'),
            ('PicPay', 'Carteiras Digitais', 'Aplicativo de pagamentos instantâneos e transferência.'),
            ('Will Bank', 'Bancos Digitais', 'Banco digital com foco em crédito descomplica.'),
            ('Neon', 'Bancos Digitais', 'Conta digital e cartão de crédito sem mensalidade.'),
            ('Banco Next', 'Bancos Digitais', 'Banco digital controlado pelo Bradesco.'),
            ('XP Investimentos', 'Investimentos', 'Maior corretora e plataforma de investimentos do Brasil.'),
            ('BTG Pactual', 'Investimentos', 'Maior banco de investimentos da América Latina.'),
            ('Rico Investimentos', 'Investimentos', 'Plataforma acessível de investimentos online.'),
            ('Banco Pan', 'Financiamentos e Bancos', 'Banco focado em crédito consignado e financiamento.'),
            ('Agibank', 'Bancos Digitais', 'Banco com atendimento presencial e digital para aposentados.'),
            ('BV Financeira', 'Financiamento de Veículos', 'Líder em financiamento de veículos usados.'),

            # Telecomunicações & Internet
            ('Claro Brasil', 'Telecomunicações', 'Operadora de telefonia móvel, fixa e fibra.'),
            ('Vivo (Telefônica)', 'Telecomunicações', 'Líder em conexões móveis e fibra ótica.'),
            ('TIM Brasil', 'Telecomunicações', 'Operadora de telefonia celular e internet móvel.'),
            ('Oi Fibra', 'Telecomunicações', 'Provedor de internet fibra ótica de alta velocidade.'),
            ('Algar Telecom', 'Telecomunicações', 'Operadora de telecomunicações no interior do Brasil.'),
            ('Brisanet', 'Provedores de Internet', 'Maior provedor de fibra ótica do Nordeste.'),
            ('Desktop Internet', 'Provedores de Internet', 'Provedor de fibra no estado de São Paulo.'),
            ('Unifique', 'Provedores de Internet', 'Provedor de alta velocidade no Sul do Brasil.'),
            ('SKY Brasil', 'TV por Assinatura', 'Operadora de TV por assinatura via satélite.'),

            # Delivery & Aplicativos
            ('iFood', 'Delivery de Comida', 'Líder em delivery de refeições e mercado.'),
            ('Uber Brasil', 'Mobilidade Urbana', 'Plataforma de viagens e entregas por aplicativo.'),
            ('99 (99App)', 'Mobilidade Urbana', 'Aplicativo brasileiro de transporte e entregas.'),
            ('Zé Delivery', 'Delivery de Bebidas', 'Maior app de entrega de bebidas geladas.'),
            ('Rappi', 'Super-app Delivery', 'Aplicativo de entregas de restaurantes e farmácias.'),
            ('Loggi', 'Logística e Entregas', 'Empresa de tecnologia para logística de entregas expressas.'),
            ('Lalamove', 'Logística e Fretamento', 'Serviço de entregas e carretos por aplicativo.'),

            # Streaming & Entretenimento
            ('Netflix Brasil', 'Streaming de Vídeo', 'Serviço de streaming de filmes e séries.'),
            ('Spotify Brasil', 'Streaming de Música', 'Maior plataforma de streaming de música e podcasts.'),
            ('Prime Video (Amazon)', 'Streaming de Vídeo', 'Catálogo de filmes e séries da Amazon.'),
            ('Disney+', 'Streaming de Vídeo', 'Streaming exclusivo de produções Disney e Marvel.'),
            ('Max (HBO Max)', 'Streaming de Vídeo', 'Conteúdo da Warner Bros, HBO e Champions League.'),
            ('Globoplay', 'Streaming de Vídeo', 'Plataforma de streaming da Rede Globo.'),
            ('YouTube Premium', 'Streaming de Vídeo', 'Serviço por assinatura do YouTube sem anúncios.'),
            ('Crunchyroll', 'Streaming de Animes', 'Maior acervo de animes e cultura asiática.'),

            # Moda, Saúde & Farmácias
            ('Lojas Renner', 'Moda e Varejo', 'Rede de lojas de departamento e vestuário.'),
            ('C&A Brasil', 'Moda e Varejo', 'Multinacional de vestuário e acessórios.'),
            ('Riachuelo', 'Moda e Varejo', 'Uma das maiores redes de moda do país.'),
            ('Zara Brasil', 'Moda Fast-Fashion', 'Rede espanhola de vestuário e tendências.'),
            ('Droga Raia', 'Farmácias', 'Uma das maiores redes de farmácias do Brasil.'),
            ('Drogasil', 'Farmácias', 'Rede de drogarias com milhares de unidades.'),
            ('Ultrafarma', 'Farmácias Online', 'Lojas físicas e online com foco em genéricos.'),
            ('Pague Menos', 'Farmácias', 'Rede de farmácias com forte presença no Nordeste.'),
            ('O Boticário', 'Cosméticos e Perfumaria', 'Líder brasileira em perfumaria e cosméticos.'),
            ('Natura', 'Cosméticos e Perfumaria', 'Multinacional brasileira de produtos de beleza.'),
            ('Avon Brasil', 'Cosméticos e Perfumaria', 'Marca tradicional de vendas diretas de beleza.'),
            ('Sephora Brasil', 'Cosméticos de Luxo', 'Rede francesa de maquiagem e perfumes importados.'),

            # Viagens, Linhas Aéreas & Mobilidade
            ('LATAM Airlines Brasil', 'Companhias Aéreas', 'Maior companhia aérea da América Latina.'),
            ('Azul Linhas Aéreas', 'Companhias Aéreas', 'Companhia aérea com maior número de destinos no Brasil.'),
            ('GOL Linhas Aéreas', 'Companhias Aéreas', 'Operadora aérea de voos nacionais e internacionais.'),
            ('Decolar.com', 'Agências de Viagens', 'Maior agência de viagens online da América Latina.'),
            ('123Milhas', 'Agências de Viagens', 'Plataforma de busca de passagens e pacotes.'),
            ('CVC Viagens', 'Agências de Viagens', 'Maior operadora de turismo da América Latina.'),
            ('Booking.com', 'Reserva de Hotéis', 'Líder mundial em reservas de acomodações.'),
            ('Airbnb Brasil', 'Hospedagens', 'Plataforma de aluguel por temporada.'),
            ('Localiza', 'Aluguel de Carros', 'Maior rede de aluguel de carros da América Latina.'),
            ('Movida Aluguel de Carros', 'Aluguel de Carros', 'Empresa de locação e venda de seminovos.'),
            ('Webmotors', 'Classificados Automotivos', 'Maior portal de compra e venda de veículos.'),

            # 🚨 EMPRESAS COM ALERTA DE GOLPE (Foco Educativo Antifraude)
            ('VipPromos Eletrônicos (SUSPEITA DE GOLPE)', 'E-commerce Falso', 'Site promocional não oficial com reclamações recorrentes de Pix não entregue.'),
            ('PixLucrativo Oficial (FRAUDE IDENTIFICADA)', 'Fraude Financeira', 'Esquema de pirâmide e promessa de multiplicação rápida de dinheiro via Pix.'),
            ('OutletIphoneBarato (SUSPEITA DE GOLPE)', 'Loja Virtual Falsa', 'Perfil em rede social cobrando taxa antecipada de envio de smartphones.'),
            ('MegaDescontosBrasil (SUSPEITA DE GOLPE)', 'E-commerce Falso', 'Loja fantasma anunciando produtos com 80% de desconto sem entrega.'),
            ('MultiplicaPixBr (FRAUDE IDENTIFICADA)', 'Fraude Financeira', 'Golpe do Pix no Instagram com páginas clonadas de bancos.'),
        ]

        # Ensure a default consumer exists for complaints
        consumer_user, _ = User.objects.get_or_create(username='consumidor_demo', defaults={'role': User.Role.CONSUMER})
        consumer_user.set_password('senha123')
        consumer_user.save()
        consumer_profile, _ = ConsumerProfile.objects.get_or_create(user=consumer_user, defaults={'phone': '11999998888'})

        count = 0
        for name, category, desc in companies_list:
            slug = name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace('!', '').replace('.', '').replace('/', '_')[:30]
            user, _ = User.objects.get_or_create(username=slug, defaults={'role': User.Role.COMPANY})
            user.set_password('senha123')
            user.save()

            company, created = CompanyProfile.objects.get_or_create(
                user=user,
                defaults={
                    'name': name,
                    'category': category,
                    'description': desc
                }
            )

            # If it's a fraud company, generate unanswered complaints to activate Fraud Alert Engine!
            if 'GOLPE' in name or 'FRAUDE' in name or 'SUSPEITA' in name:
                for i in range(1, 7):
                    Complaint.objects.get_or_create(
                        consumer=consumer_profile,
                        company=company,
                        title=f'Não recebi o produto / Golpe Pix #{i}',
                        defaults={
                            'description': 'Realizei a transferência e a empresa sumiu sem enviar o comprovante ou o código de rastreio.',
                            'category': 'Golpe / Fraude',
                            'status': Complaint.Status.OPEN
                        }
                    )

            company.update_fraud_status()
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Sucesso! {count} empresas cadastradas e sinalizadas no banco de dados!"))
