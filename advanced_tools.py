#######################
# Agente Económico    #
# Herramientas        #
#######################

import requests

class EconomicTools:

    def __init__(self):
        pass

    # Herramienta para consultar indicadores económicos del Banco Mundial
    def consultar_indicador_banco_mundial(self, pais: str, indicador: str):
        print(f"Herramienta consultar_indicador_banco_mundial llamada con pais: {pais}, indicador: {indicador}")

        if not pais or not indicador:
            return "Error: Se requiere el código de país y el código de indicador."

        url = (
            f"https://api.worldbank.org/v2/country/{pais}/indicator/{indicador}"
            f"?format=json&per_page=5&mrnev=1"
        )

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            print(f"Error al consultar_indicador_banco_mundial: {pais}, {indicador}. Error: {e}")
            return f"ERROR: No se pudo consultar el indicador {indicador} para el país {pais}"

    # Herramienta para consultar el precio de una criptomoneda
    def consultar_precio_cripto(self, moneda_cripto: str, moneda_fiat: str = "usd"):
        print(f"Herramienta consultar_precio_cripto llamada con moneda_cripto: {moneda_cripto}, moneda_fiat: {moneda_fiat}")

        if not moneda_cripto:
            return "Error: Se requiere el nombre de la criptomoneda (ejemplo: bitcoin, ethereum)."

        url = (
            f"https://api.coingecko.com/api/v3/simple/price"
            f"?ids={moneda_cripto.lower()}&vs_currencies={moneda_fiat.lower()}"
        )

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            if not data:
                return f"No se encontró información para la criptomoneda: {moneda_cripto}"
            return data
        except Exception as e:
            print(f"Error al consultar_precio_cripto: {moneda_cripto}. Error: {e}")
            return f"ERROR: No se pudo consultar el precio de {moneda_cripto}"

    # Herramienta para convertir un monto entre dos monedas
    def convertir_moneda(self, monto: float, moneda_origen: str, moneda_destino: str):
        print(f"Herramienta convertir_moneda llamada con monto: {monto}, moneda_origen: {moneda_origen}, moneda_destino: {moneda_destino}")

        if not moneda_origen or not moneda_destino:
            return "Error: Se requiere la moneda de origen y la moneda de destino."

        url = f"https://open.er-api.com/v6/latest/{moneda_origen.upper()}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            rates = data.get("rates", {})
            tasa = rates.get(moneda_destino.upper())
            if tasa is None:
                return f"No se encontró tasa de conversión de {moneda_origen} a {moneda_destino}"
            resultado = round(monto * tasa, 2)
            return {
                "monto_original": monto,
                "moneda_origen": moneda_origen.upper(),
                "moneda_destino": moneda_destino.upper(),
                "tasa": tasa,
                "resultado": resultado
            }
        except Exception as e:
            print(f"Error al convertir_moneda: {moneda_origen} a {moneda_destino}. Error: {e}")
            return f"ERROR: No se pudo convertir {moneda_origen} a {moneda_destino}"

    # Herramienta para consultar las top criptomonedas por valor de mercado
    def consultar_top_criptomonedas(self, cantidad: int = 5):
        print(f"Herramienta consultar_top_criptomonedas llamada con cantidad: {cantidad}")

        url = (
            f"https://api.coingecko.com/api/v3/coins/markets"
            f"?vs_currency=usd&order=market_cap_desc&per_page={cantidad}&page=1"
        )

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            resumen = [
                {"nombre": c["name"], "simbolo": c["symbol"], "precio_usd": c["current_price"]}
                for c in data
            ]
            return resumen
        except Exception as e:
            print(f"Error al consultar_top_criptomonedas. Error: {e}")
            return f"ERROR: No se pudo consultar el top de criptomonedas"
