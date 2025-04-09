import os
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Reemplaza "*" con tu dominio si fuera necesario
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carga segura de credenciales desde el archivo .env
HUBSPOT_API_KEY = os.getenv("HUBSPOT_API_KEY")  # Inserta tu token real en el .env
HUBSPOT_SECRET = os.getenv("HUBSPOT_SECRET")      # Inserta tu “secreto” si lo requieres

HUBSPOT_SEARCH_URL = "https://api.hubapi.com/crm/v3/objects/contacts/search"

@app.get("/consultar-envio")
def consultar_envio(guia: str):
    """
    Consulta en HubSpot el estado del envío, basado en la propiedad "guia"
    Retorna las propiedades configuradas en HubSpot.
    """
    headers = {
        "Authorization": f"Bearer {HUBSPOT_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "filterGroups": [{
            "filters": [
                {"propertyName": "guia", "operator": "EQ", "value": guia}
            ]
        }],
        "properties": [
            "correo",
            "nombre",
            "apellidos",
            "destino",
            "estatus",
            "guia",
            "numero_de_telefono",
            "recoleccion",
            "direccion",
            "ciudad",
            "codigo_postal",
            "medidas",
            "peso",
            "direccion_de_entrega",
            "nombre_de_receptor",
            "telefono_del_receptor",
            "total"
        ]
    }

    response = requests.post(HUBSPOT_SEARCH_URL, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if data.get("results"):
            contacto = data["results"][0]["properties"]
            return contacto
        return {"error": "No se encontró un envío con esa guía."}
    else:
        return {"error": f"Error en HubSpot: {response.status_code} - {response.text}"}