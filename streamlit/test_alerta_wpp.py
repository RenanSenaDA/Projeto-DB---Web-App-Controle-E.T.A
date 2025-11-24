from alerts_whatsapp import enviar_alerta_whatsapp, enviar_alerta_whatsapp_para_destinatarios_padrao
from datetime import datetime


print("\n====== TESTE DE ALERTA WHATSAPP - ETA ======\n")

# DADOS FAKE PARA TESTE
equipamento = "TESTE DE ALERTA"
valor_kpi = "123.45"
limite = "limite de teste"
timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")

# OPÇÃO 1 — Testar um número específico:
numero_teste = "5583996172285"    # coloque aqui o seu número

print("➡ Enviando alerta para número específico:", numero_teste)
ok1 = enviar_alerta_whatsapp(numero_teste, equipamento, valor_kpi, limite, timestamp)

print("\nResultado envio individual:", ok1)

# OPÇÃO 2 — Testar envio para os destinatários padrão do .env
print("\n➡ Enviando para destinatários padrão (WPP_DESTINATARIOS_PADRAO)...")
ok2 = enviar_alerta_whatsapp_para_destinatarios_padrao(
    equipamento, valor_kpi, limite, timestamp
)

print("\nResultado envio para destinatários padrão:", ok2)

print("\n====== FIM DO TESTE ======\n")
