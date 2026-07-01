import os
import gspread
import pandas as pd
from django.core.management.base import BaseCommand
from django.utils.timezone import make_aware
from datetime import datetime
from google.oauth2.service_account import Credentials
from helpdesk.models import Chamado 

class Command(BaseCommand):
    help = 'Puxa os dados direto do Google Sheets via API mapeando por índice físico de linha'

    def handle(self, *args, **options):
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        caminho_credenciais = r"D:\Meus projetos\erp_aletech\credenciais.json"
        
        if not os.path.exists(caminho_credenciais):
            self.stdout.write(self.style.ERROR("Arquivo credenciais.json não encontrado!"))
            return

        self.stdout.write(self.style.WARNING('Conectando à API do Google Sheets...'))
        
        try:
            creds = Credentials.from_service_account_file(caminho_credenciais, scopes=scopes)
            client = gspread.authorize(creds)
            
            id_da_planilha = "16rGSeEQ7I-qPI8NMrOl5fLDJ85xMumdCXmGWhzNr_Hk"
            planilha = client.open_by_key(id_da_planilha)
            aba = planilha.get_worksheet(0)
            
            dados = aba.get_all_records()
            df = pd.DataFrame(dados)
            df.columns = df.columns.str.strip()
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao conectar com o Google: {e}"))
            return

        self.stdout.write(self.style.WARNING(f'Sincronizando {len(df)} registros mapeados...'))

        for index, linha in df.iterrows():
            status_planilha = str(linha.get('status', '')).strip()
            
            # 🔥 Define a linha física real na planilha do Google Sheets (Pandas index 0 é a linha 2 da planilha)
            linha_real_sheets = index + 2
            id_unico_linha = f"LINHA_{linha_real_sheets}"
            
            if status_planilha.upper() == 'OK' or not status_planilha or status_planilha.lower() == 'nan':
                self.stdout.write(self.style.WARNING(f'Linha {linha_real_sheets} ignorada (Status "OK" ou vazio).'))
                continue
            
            data_criacao_str   = str(linha.get('Carimbo de data/hora', '')).strip()
            solicitante        = linha.get('Nome')
            empresa            = linha.get('Empresa')
            forma_atendimento  = linha.get('Forma de atendimento')
            equipamento        = linha.get('Qual equipamento?')
            problema           = linha.get('Descreva o problema apresentado(Modelo e Quantidade)')
            
            ultimo_comentario  = linha.get('Coluna 1')
            if not ultimo_comentario or str(ultimo_comentario).strip() == "" or str(ultimo_comentario).lower() == 'nan':
                ultimo_comentario = ""
            else:
                ultimo_comentario = str(ultimo_comentario).strip()

            # Conversão inteligente de data/hora
            data_hora_final = None
            if data_criacao_str and data_criacao_str != 'nan':
                for formato in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y"):
                    try:
                        naive_datetime = datetime.strptime(data_criacao_str, formato)
                        data_hora_final = make_aware(naive_datetime)
                        break
                    except ValueError:
                        continue

            try:
                # Busca exatamente o chamado atrelado àquela linha física
                chamado = Chamado.objects.get(id_integracao=id_unico_linha)
                chamado.status = status_planilha
                chamado.ultimo_comentario = ultimo_comentario
                chamado.save()
                self.stdout.write(self.style.SUCCESS(f'Linha {linha_real_sheets} atualizada com sucesso.'))
                
            except Chamado.DoesNotExist:
                # Se for uma linha nova, cria vinculando o ID à linha
                Chamado.objects.create(
                    id_integracao=id_unico_linha,
                    data_hora=data_hora_final if data_hora_final else datetime.now(),
                    nome_tecnico="Não atribuído",
                    empresa=empresa if (empresa and str(empresa) != 'nan') else "Não Informado",
                    solicitante=solicitante if (solicitante and str(solicitante) != 'nan') else "Não Informado",
                    forma_atendimento=forma_atendimento if (forma_atendimento and str(forma_atendimento) != 'nan') else "Presencial",
                    equipamento=equipamento if (equipamento and str(equipamento) != 'nan') else "Outros",
                    problema=problema if (problema and str(problema) != 'nan') else "",
                    status=status_planilha,
                    ultimo_comentario=ultimo_comentario
                )
                self.stdout.write(self.style.SUCCESS(f'Novo chamado criado para a Linha {linha_real_sheets}. Chave: {id_unico_linha}'))

        self.stdout.write(self.style.SUCCESS('Banco de dados sincronizado com sucesso!'))