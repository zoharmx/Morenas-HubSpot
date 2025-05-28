"""
Morenas-HubSpot API
-------------------
•  Endpoint  GET /consultar-envio?guia=...      →  consulta un contacto en HubSpot por Nº de guía
•  Endpoint POST /webhook                       →  recibe eventos de HubSpot (webhooks)
•  Endpoint GET  /ver-webhooks                  →  lista los eventos recibidos
•  Endpoint GET  /                              →  health-check para Render
"""

import os, json, datetime, hmac, hashlib, requests
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# ---------- Cargar variables de entorno ----------
load_dotenv()
HUBSPOT_API_KEY   = os.getenv("HUBSPOT_API_KEY")      # Token privado (PAT)
HUBSPOT_SECRET    = os.getenv("HUBSPOT_SECRET")       # Client Secret (para firmar webhooks) – opcional
HUBSPOT_SEARCH_URL = "https://api.hubapi.com/crm/v3/objects/contacts/search"

# ---------- Crear app ----------
app = FastAPI(title="Morenas-HubSpot API", version="1.0.0")

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],            # cámbialo por tu dominio en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Health check (para Render) ----------
@app.get("/", tags=["health"])
async def root():
    return {"status": "ok"}

# ---------- Consulta de envíos ----------
@app.get("/consultar-envio", tags=["envios"])
def consultar_envio(guia: str):
    """
    Devuelve las propiedades de un contacto cuyo campo 'guia' coincide con el parámetro.
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
            "correo", "nombre", "apellidos", "destino", "estatus", "guia",
            "numero_de_telefono", "recoleccion", "direccion", "ciudad", "codigo_postal",
            "medidas", "peso", "direccion_de_entrega", "nombre_de_receptor",
            "telefono_del_receptor", "total"
        ]
    }

    resp = requests.post(HUBSPOT_SEARCH_URL, json=payload, headers=headers)
    if resp.status_code != 200:
        return {"error": f"HubSpot error {resp.status_code}: {resp.text}"}

    data = resp.json()
    if not data.get("results"):
        return {"error": "No se encontró un envío con esa guía."}

    return data["results"][0]["properties"]

# ---------- Recepción de Webhooks ----------
@app.post("/webhook", tags=["webhooks"])
async def webhook_hubspot(req: Request):
    """
    Recibe eventos de HubSpot.  Guarda cada uno en 'webhook_log.json'.
    Si HUBSPOT_SECRET está definido, valida la firma HMAC.
    """
    body = await req.body()           # bytes
    if HUBSPOT_SECRET:
        sig_header = req.headers.get("X-HubSpot-Signature")
        computed = hmac.new(
            HUBSPOT_SECRET.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig_header or "", computed):
            raise HTTPException(status_code=401, detail="Invalid signature")

    payload = json.loads(body)

    with open("webhook_log.json", "a", encoding="utf-8") as f:
        json.dump({"ts": str(datetime.datetime.now()), "data": payload}, f, ensure_ascii=False)
        f.write("\n")

    print("📨 Webhook recibido:", payload)
    return {"status": "ok"}

# ---------- Visualizar webhooks almacenados ----------
@app.get("/ver-webhooks", tags=["webhooks"])
async def ver_webhooks():
    """
    Devuelve todos los eventos guardados en 'webhook_log.json'.
    """
    try:
        with open("webhook_log.json", encoding="utf-8") as f:
            return {"events": [json.loads(line) for line in f]}
    except FileNotFoundError:
        return {"events": []}
