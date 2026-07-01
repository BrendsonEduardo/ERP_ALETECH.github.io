@echo off
:: Navega até a pasta raiz do seu projeto erp_aletech
cd /d "D:\Meus projetos\erp_aletech"

:: Executa o comando de importação usando o Python do seu sistema
python manage.py importar_planilha

:: (Opcional) Grava a data e hora da última execução num arquivo de log para você acompanhar
echo Ultima sincronizacao feita em %date% as %time% >> log_sincronizacao.txt