#######################
# Agente Económico    #
# Núcleo del agente   #
#######################

# Este archivo solo contiene la lógica del agente (sin input/print de consola),
# para poder usarlo desde la app de Streamlit.

# Importacion para el LLM
from groq import Groq

# Importacion para el uso de formato JSON
import json

# Importacion de herramientas #
from intermediate_tools import IntermediateTools as ExchangeTools
from intermediate_tools_example import IntermediateTools as WeatherTools
from advanced_tools import EconomicTools

MODEL = "openai/gpt-oss-120b"


SYSTEM_PROMPT = """
Eres un Agente Económico que habla en español y responde de manera breve y concisa.

Tu objetivo específico es: ayudar al usuario a tomar decisiones financieras informadas,
combinando tipo de cambio, conversión de montos, indicadores macroeconómicos (inflación, PIB)
y clima como dato de contexto. Siempre que el usuario pregunte por tipo de cambio, inflación,
PIB, una conversión de montos, o el clima de una ciudad, DEBES usar la herramienta
correspondiente para responder con datos reales, en vez de decir que no tienes la información.

Herramientas disponibles:

1. consultar_tipo_cambio_api
- Te da el tipo de cambio actual de una moneda respecto al quetzal de Guatemala.
- La moneda es obligatoria (ejemplo: USD, EUR).

2. consultar_indicador_banco_mundial
- Te da el valor más reciente de un indicador económico del Banco Mundial para un país.
- Requiere el código de país ISO de 2 letras (ejemplo: GT para Guatemala, MX para México).
- Requiere el código del indicador (ejemplo: FP.CPI.TOTL.ZG para inflación anual,
  NY.GDP.MKTP.CD para PIB en dólares).
- Si el usuario pide "inflación" o "PIB" sin dar el código exacto, usa estos códigos.

3. convertir_moneda
- Convierte un monto de una moneda a otra usando el tipo de cambio actual.
- Requiere el monto, la moneda de origen y la moneda de destino.

4. obtener_lat_long
- Te da la latitud y longitud de una ciudad. Se usa como paso previo a obtener_clima_api.
- Requiere el nombre de la ciudad.

5. obtener_clima_api
- Te da el clima actual de un lugar usando su latitud y longitud.
- SIEMPRE debes llamar primero a obtener_lat_long para conseguir esos datos,
  antes de llamar a obtener_clima_api.

Si no tienes el código de un indicador que el usuario pide, dile que no lo tienes disponible,
no inventes un código.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "consultar_tipo_cambio_api",
            "description": (
                "Llama a esta funcion para consultar el tipo de cambio de una moneda "
                "respecto al quetzal de Guatemala. "
                "Se debe enviar como argumento el codigo de la moneda que se desea consultar."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "moneda": {
                        "type": "string",
                        "description": "Codigo de la moneda que se desea consultar, por ejemplo USD"
                    }
                },
                "required": ["moneda"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_indicador_banco_mundial",
            "description": (
                "Llama a esta funcion para consultar el valor mas reciente de un indicador "
                "economico del Banco Mundial para un pais. Se debe enviar el codigo de pais "
                "en formato ISO de 2 letras (ejemplo GT para Guatemala) y el codigo del "
                "indicador (ejemplo FP.CPI.TOTL.ZG para inflacion anual, NY.GDP.MKTP.CD para PIB)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pais": {
                        "type": "string",
                        "description": "Codigo de pais ISO de 2 letras, por ejemplo GT"
                    },
                    "indicador": {
                        "type": "string",
                        "description": "Codigo del indicador del Banco Mundial, por ejemplo FP.CPI.TOTL.ZG"
                    }
                },
                "required": ["pais", "indicador"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "convertir_moneda",
            "description": (
                "Llama a esta funcion para convertir un monto de una moneda a otra "
                "usando el tipo de cambio actual. Se debe enviar el monto, la moneda "
                "de origen y la moneda de destino."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "monto": {
                        "type": "number",
                        "description": "Cantidad a convertir"
                    },
                    "moneda_origen": {
                        "type": "string",
                        "description": "Codigo de la moneda de origen, por ejemplo USD"
                    },
                    "moneda_destino": {
                        "type": "string",
                        "description": "Codigo de la moneda de destino, por ejemplo GTQ"
                    }
                },
                "required": ["monto", "moneda_origen", "moneda_destino"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_lat_long",
            "description": (
                "Llama a esta funcion para obtener la latitud y longitud de cualquier ciudad. "
                "Se debe enviar como argumento el nombre de la ciudad."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "ciudad": {
                        "type": "string",
                        "description": "El nombre de la ciudad para la cual se desea obtener la latitud y longitud"
                    }
                },
                "required": ["ciudad"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_clima_api",
            "description": (
                "Llama a esta funcion para obtener el clima actual en cualquier lugar. "
                "Se debe enviar como argumento la latitud y longitud."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {
                        "type": "string",
                        "description": "La latitud del lugar del cual se desea obtener el clima"
                    },
                    "long": {
                        "type": "string",
                        "description": "La longitud del lugar del cual se desea obtener el clima"
                    }
                },
                "required": ["lat", "long"]
            }
        }
    }
]

def process_response(client: Groq, memory_messages: list[dict], user_text: str):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(memory_messages)
    messages.append({"role": "user", "content": user_text})

    while True:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            parallel_tool_calls=False
        )

        msg = resp.choices[0].message

        # Si no hay llamados a herramientas, entonces ya regresamos la respuesta
        if not getattr(msg, "tool_calls", None):
            return msg.content or ""

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [tc.model_dump() for tc in msg.tool_calls]
        })

        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments or "{}")

            if name == "consultar_tipo_cambio_api":
                tools = ExchangeTools()
                result = tools.consultar_tipo_cambio_api(
                    moneda=args["moneda"]
                )
            elif name == "consultar_indicador_banco_mundial":
                tools = EconomicTools()
                result = tools.consultar_indicador_banco_mundial(
                    pais=args["pais"],
                    indicador=args["indicador"]
                )
            elif name == "convertir_moneda":
                tools = EconomicTools()
                result = tools.convertir_moneda(
                    monto=args["monto"],
                    moneda_origen=args["moneda_origen"],
                    moneda_destino=args["moneda_destino"]
                )
            elif name == "obtener_lat_long":
                tools = WeatherTools()
                result = tools.obtener_lat_long(
                    ciudad=args["ciudad"]
                )
            elif name == "obtener_clima_api":
                tools = WeatherTools()
                result = tools.obtener_clima_api(
                    lat=args["lat"],
                    long=args["long"]
                )
            else:
                print(f"Se intentó llamar a una herramienta desconocida {name}")
                result = {"error": f"Herramienta desconocida: {name}"}

            # Agregar a los mensajes el resultado del llamado de la herramienta
            # Esto lo recibirá el modelo al continuar la iteración
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False)
            })
