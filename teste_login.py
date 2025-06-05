import requests

USERNAME = "vferreira@grupobraido.com"
PASSWORD = "vferreira@"            # ← senha corrigida, sem “FRP3B72”

URL_LOGIN = "https://www.movias.com.br:8443/ws/auth/login"

def obter_token(usuario: str, senha: str) -> str:
    payload = {
        "username": usuario,
        "password": senha
    }
    resp = requests.post(URL_LOGIN, json=payload, verify=True)
    print("Status code:", resp.status_code)
    print("Corpo de resposta (raw):")
    print(resp.text)
    resp.raise_for_status()
    data = resp.json()
    return data.get("id_token", "<sem id_token>")

def main():
    try:
        token = obter_token(USERNAME, PASSWORD)
        print("Token obtido:", token)
    except Exception as e:
        print("Falha ao obter token:", e)

if __name__ == "__main__":
    main()
