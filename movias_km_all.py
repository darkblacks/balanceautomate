import requests
import pandas as pd
import time
import calendar
from datetime import datetime, timedelta

# ===================== 1. CONFIGURAÇÕES E ENTRADA DO USUÁRIO =====================
BASE_URL = "https://www.movias.com.br:8443/ws"
USERNAME = "vferreira@grupobraido.com"
PASSWORD = "vferreira@"

# Meses em Português
MESES_PT = {
    1:  "Janeiro",
    2:  "Fevereiro",
    3:  "Março",
    4:  "Abril",
    5:  "Maio",
    6:  "Junho",
    7:  "Julho",
    8:  "Agosto",
    9:  "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro"
}

# Pergunta ao usuário qual ano e mês deseja processar
while True:
    try:
        ano = int(input("Qual ano (por exemplo, 2024, 2025)? ").strip())
        if ano < 2000 or ano > 2100:
            raise ValueError
        break
    except ValueError:
        print("Por favor, insira um ano válido.")

while True:
    try:
        mes = int(input("Qual mês (1–12)? ").strip())
        if mes < 1 or mes > 12:
            raise ValueError
        break
    except ValueError:
        print("Por favor, insira um número de mês entre 1 e 12.")

nome_mes = MESES_PT[mes]

# Monta o intervalo completo do mês escolhido (do dia 1 às 00:00:00 até o último dia às 23:59:59)
dt_inicio = datetime(ano, mes, 1, 0, 0, 0)
ultimo_dia = calendar.monthrange(ano, mes)[1]
dt_fim = datetime(ano, mes, ultimo_dia, 23, 59, 59)

start_str = dt_inicio.strftime("%d/%m/%Y %H:%M:%S")
end_str   = dt_fim.strftime("%d/%m/%Y %H:%M:%S")

# Nome do arquivo no formato frota_<mês>_<ano>.xlsx
OUTPUT_FILE = f"frota_{mes:02d}_{ano}.xlsx"
PAUSA = 0.2  # pausa em segundos entre chamadas para evitar 429

print(f"\nIntervalo selecionado: {start_str} até {end_str}")
print(f"O resultado será salvo em '{OUTPUT_FILE}'.\n")

# ===================== 2. AUTENTICAÇÃO =====================
print("1) Autenticando…")
resp_login = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": USERNAME, "password": PASSWORD}
)
resp_login.raise_for_status()
token = resp_login.json().get("id_token")
if not token:
    print("❌ Falha ao obter token. Verifique usuário/senha.")
    exit(1)

headers = {"Authorization": f"Bearer {token}"}
print("✔ Autenticado com sucesso.\n")

# ===================== 3. OBTER LISTA DE VEÍCULOS =====================
print("2) Recuperando lista completa de veículos…")
resp_veiculos = requests.get(f"{BASE_URL}/v1/vehicle", headers=headers)
resp_veiculos.raise_for_status()
veiculos = resp_veiculos.json()

lista_veiculos = []
for v in veiculos:
    idv = v.get("idVehicle")
    placa = v.get("licensePlate", "").strip()
    if idv and placa:
        lista_veiculos.append((idv, placa))

print(f"   → Encontrados {len(lista_veiculos)} veículos.\n")

# ===================== 4. PARA CADA VEÍCULO, SOMAR KM DO MÊS =====================
registros = []
total = len(lista_veiculos)

for idx, (id_veic, placa) in enumerate(lista_veiculos, start=1):
    print(f"[{idx}/{total}] Processando id={id_veic} | placa='{placa}'")

    url_trip = f"{BASE_URL}/v1/telemetry/trip"
    params = {
        "idVehicle":    id_veic,    # case-sensitive
        "licensePlate": placa,      # case-sensitive
        "startDh":      start_str,
        "endDh":        end_str
    }

    resp_trip = requests.get(url_trip, headers=headers, params=params)

    # Se qualquer status diferente de 200, considera 0 km, mas NÃO interrompe
    if resp_trip.status_code != 200:
        total_km = 0.0
    else:
        dados_trip = resp_trip.json()
        total_km = 0.0

        if isinstance(dados_trip, list) and dados_trip:
            for bloco in dados_trip[0].get("telemetry", []):
                dist = bloco.get("distanceTraveled", 0)
                data = bloco.get("startDate", "")
                try:
                    dt = datetime.strptime(data, "%d/%m/%Y %H:%M:%S")
                except Exception:
                    continue
                if dt.year == ano and dt.month == mes:
                    total_km += float(dist)

    print(f"   → {nome_mes}/{ano}: {total_km:.2f} km\n")
    registros.append({
        "Placa":  placa,
        "Id":     id_veic,
        nome_mes: round(total_km, 2)
    })

    time.sleep(PAUSA)

# ===================== 5. MONTAR DATAFRAME E SALVAR EXCEL =====================
df = pd.DataFrame(registros, columns=["Placa", "Id", nome_mes])
df.to_excel(OUTPUT_FILE, index=False)
print(f"✔ Planilha gerada: {OUTPUT_FILE}")
