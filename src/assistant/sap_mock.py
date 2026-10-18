"""Simula consultas SOMENTE LEITURA ao SAP. Em produção: OData/RFC read-only via BTP Destination,
usuário técnico com menor privilégio, sem serviços de escrita expostos ao assistente."""

PURCHASE_ORDERS = {
    "4500012345": {
        "tipo": "NB", "fornecedor": "100234 - Fornecedor Alfa Ltda", "valor_total": 185000.00, "moeda": "BRL",
        "estrategia_liberacao": {"grupo": "02", "estrategia": "S2", "status": "BLOQUEADO",
                                 "codigos": {"01": "liberado", "02": "pendente"}, "aprovador_pendente": "GERENTE_COMPRAS"},
        "historico": [], "status_entrega": "sem EM",
    },
    "4500012346": {
        "tipo": "NB", "fornecedor": "100877 - Fornecedor Beta S.A.", "valor_total": 12000.00, "moeda": "BRL",
        "estrategia_liberacao": {"status": "LIBERADO"},
        "itens": [{"item": "10", "material": "MAT-1001", "qtd_pedido": 100, "qtd_recebida": 0,
                   "tolerancia_excesso_pct": 5, "indicador_entrega_ilimitada": False}],
        "historico": [], "status_entrega": "sem EM",
    },
}

INVOICES = {
    "5105600123": {"pedido": "4500012346", "valor": 12600.00, "moeda": "BRL", "status_pagamento": "BLOQUEADO",
                   "motivo_bloqueio": "Bloqueio de preço (R) — diferença acima da tolerância PP",
                   "valor_pedido": 12000.00, "data_lancamento": "2026-10-10"},
}

POSTING_PERIODS = {
    "1000": {"periodo_aberto_atual": "010/2026", "periodo_anterior_aberto": False, "variante": "1000"},
}

IDOCS = {
    "0000000123456": {"tipo_mensagem": "ORDERS", "status": "51", "texto_status":
                      "Erro de aplicação: fornecedor 100999 não cadastrado para org. compras 1000", "direcao": "entrada"},
}


def lookup_documents(numbers: list[str]) -> dict:
    found = {}
    for number in numbers:
        clean = number.strip()
        if clean in PURCHASE_ORDERS:
            found[f"pedido_{clean}"] = PURCHASE_ORDERS[clean]
        if clean in INVOICES:
            found[f"fatura_{clean}"] = INVOICES[clean]
        if clean in IDOCS:
            found[f"idoc_{clean}"] = IDOCS[clean]
    return found


def lookup_posting_period(company_code: str = "1000") -> dict:
    return POSTING_PERIODS.get(company_code, {})