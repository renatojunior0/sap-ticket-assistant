---
id: KB-MM-003
titulo: Pedido de compra bloqueado aguardando liberação (estratégia de liberação)
modulo: MM
processo: pedido_compra
transacoes: [ME21N, ME22N, ME23N, ME28, ME29N, SWI1]
mensagens: []
tabelas: [EKKO, T16FS, T16FV]
objetos_autorizacao: [M_EINK_FRG]
risco_acao: alto
referencias:
  - SAP Help Portal - Release Procedure for Purchasing Documents
  - Experiência de projeto (configuração de estratégia de liberação em S/4HANA)
---
## Sintoma
Pedido de compra criado, porém não é possível imprimir, transmitir ao fornecedor nem registrar entrada de mercadoria (MIGO). Na ME23N, aba "Estratégia de liberação" do cabeçalho, o indicador mostra o pedido como bloqueado com um ou mais códigos de liberação pendentes. Mensagens típicas: "Pedido ainda não liberado" ou "Documento de compra está sujeito à liberação".

## Causas prováveis
1. O pedido atingiu os critérios da estratégia (valor líquido total, grupo de compras, tipo de documento, organização de compras) e aguarda o aprovador do código pendente.
2. O aprovador responsável não possui autorização para o código de liberação (objeto M_EINK_FRG com o grupo e código corretos).
3. O pedido foi alterado após liberação parcial e a configuração de "possibilidade de alteração" (changeability) reiniciou a estratégia, exigindo nova aprovação.
4. O workflow de aprovação (objeto BUS2012) está com erro ou parado, e o item de trabalho não chegou ao aprovador.
5. O pedido foi criado com uma classificação (CL20N / característica da classe de liberação) incorreta, caindo em estratégia inadequada.

## Verificações somente leitura
- ME23N > cabeçalho > aba Estratégia de liberação: identificar grupo, estratégia, códigos liberados e pendentes.
- ME23N > Ambiente > Alterações de cabeçalho: verificar se houve alteração de valor/quantidade após a liberação parcial (indício de reset).
- Consultar a matriz de aprovação do cliente (grupo + código → aprovador) para identificar quem deve liberar.
- SWI1 (ou SWIA): verificar se existe item de trabalho em erro para o objeto BUS2012 e o número do pedido.
- SU53 executado pelo aprovador logo após a tentativa: confirma se falta M_EINK_FRG.
- ME28 em modo exibição: listar pedidos pendentes de liberação por código.

## Ações que exigem autorização humana
- Liberar o pedido (ME28 ou ME29N): somente o aprovador designado pela política de alçadas; o suporte não deve liberar em nome do aprovador.
- Alterar a estratégia de liberação ou os critérios de classificação: exige request de configuração, transporte e aprovação do gestor de processo.
- Conceder o objeto M_EINK_FRG a um usuário: equipe de segurança/SoD, com aprovação formal.
- Reiniciar ou reprocessar workflow em erro: equipe de workflow/Basis, após análise da causa raiz.