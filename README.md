# ERP ALETECH 

O **ERP ALETECH** é um sistema de gestão integrada (Enterprise Resource Planning) desenvolvido para centralizar, automatizar e otimizar as operações comerciais e de suporte técnico. O sistema conta com módulos robustos de CRM/Comercial, Helpdesk para gerenciamento de chamados e controle de acessos de usuários.

---

##  Tecnologias Utilizadas

O projeto foi construído utilizando as seguintes tecnologias e frameworks:

* **Backend:** Python (v3.14) & Django Framework
* **Banco de Dados:** SQLite (Ambiente de Desenvolvimento)
* **Frontend:** HTML5, CSS3, Bootstrap (Interfaces Responsivas)
* **Automação/Scripts:** Scripts em lote (`.bat`) para sincronização de dados e rotinas Python para importação de planilhas.

---

## 📦 Módulos do Sistema

### 💼 1. Módulo Comercial (CRM)
Focado no gerenciamento de clientes e no funil de vendas:
* **Painel Comercial (Kanban):** Visualização e movimentação de oportunidades de negócio por estágios.
* **Gestão de Clientes:** Cadastro completo, edição e listagem de clientes vinculados a vendedores específicos.
* **Fichas Cadastrais e Propostas:** Upload e gerenciamento de documentos em PDF (como contratos e propostas comerciais).
* **Central de Relatórios:** Geração de relatórios gerenciais e telas otimizadas para impressão.

### 🛠️ 2. Módulo Helpdesk (Suporte Técnico)
Dedicado ao atendimento ao cliente e controle de incidentes:
* **Abertura e Painel de Chamados:** Fluxo completo para criação, edição e monitoramento de chamados técnicos.
* **Controle de Prioridades e Status:** Classificação de chamados por urgência e nível de atendimento.
* **Atribuição de Técnicos:** Vinculação direta de colaboradores responsáveis por cada chamado.
* **Módulo de Integração:** Scripts dedicados para importação e sincronização automatizada de planilhas de chamados externos (`importar_planilha.py`).

### 👥 3. Módulo de Usuários e Colaboradores
Camada de segurança e organização interna:
* **Autenticação:** Sistema seguro de login e controle de sessões.
* **Níveis de Acesso:** Diferenciação de permissões com base no Setor e Cargo do colaborador.

---

## 🚀 Como Rodar o Projeto Localmente

### Pré-requisitos
Antes de começar, você precisará ter instalado em sua máquina:
* Python 3.14 ou superior
* Git

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/BrendsonEduardo/ERP_ALETECH.github.io.git](https://github.com/BrendsonEduardo/ERP_ALETECH.github.io.git)
   cd ERP_ALETECH.github.io
