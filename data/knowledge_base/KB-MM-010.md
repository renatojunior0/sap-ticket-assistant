---
id: KB-MM-010
titulo: Avaliação separada (split valuation) — escopo e impactos
processo: dados_mestres
transacoes: [OMW0, OMWC, MM01, MM02, MM03, MBEW, MR21, CKMLCP]
mensagens: []
---
# Avaliação separada (split valuation) — escopo e impactos

## O que envolve
Permite valorar o mesmo material por tipos de avaliação (ex.: nacional/importado, novo/usado) dentro do mesmo centro. Exige ativação global (OMW0), definição de categorias e tipos de avaliação (OMWC) e extensão da visão de contabilidade do material por tipo (MM01). Afeta MBEW, lançamentos FI/CO, preços e relatórios de estoque.

## Sintomas / solicitação típica
Área pede "controlar preço diferente para material importado e nacional" ou "configurar split valuation para o material X".

## Verificações (somente leitura)
- OMW0 (exibir): avaliação separada ativa na área de avaliação.
- OMWC (exibir): categorias/tipos existentes e atribuição ao centro.
- MM03 → Contabilidade 1: categoria de avaliação atual do material; MBEW: registros por tipo.
- Verificar se o material já tem estoque/movimentos: ativar avaliação separada em material com estoque exige zerar estoque antes.

## Ação recomendada
Não executar customizing a partir de chamado de suporte. Registrar a solicitação como demanda de mudança: levantar impactos (FI/CO, MRP, relatórios), aprovar com Controladoria e executar via transporte com teste em QA.

## Requer autorização humana
- Ativar/alterar avaliação separada (OMW0/OMWC): customizing com impacto contábil global — responsável: consultor MM + Controladoria + CAB.
- Alterar categoria de avaliação do material (MM02) e zerar estoque: responsável: MDM + almoxarifado + Controladoria.