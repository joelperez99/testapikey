# check_api_keys_streamlit.py
# App en Streamlit para probar varias API keys de https://api-tennis.com/

import time
import requests
import pandas as pd
import streamlit as st

# --------------------------------------------------------------
# Configuración básica de la página
# --------------------------------------------------------------
st.set_page_config(
    page_title="🔑 Test API Keys · api-tennis.com",
    layout="centered"
)

st.title("🔑 Verificador de API keys · api-tennis.com")
st.write(
    "Pega abajo varias API keys de **api-tennis.com** (una por línea) y "
    "haz clic en **Probar API keys** para verificar cuáles están funcionando."
)

# --------------------------------------------------------------
# Entrada de API keys
# --------------------------------------------------------------
st.subheader("1️⃣ API keys")

default_example = "APIKEY_1_AQUI\nAPIKEY_2_AQUI\nAPIKEY_3_AQUI"

keys_text = st.text_area(
    "Pega aquí tus API keys (una por línea):",
    value=default_example,
    height=150,
    help="Cada línea debe contener solo una API key."
)

timeout_sec = st.number_input(
    "Timeout por request (segundos):",
    min_value=1.0,
    max_value=60.0,
    value=10.0,
    step=1.0
)

st.caption("El test usa el endpoint: `tennis/?method=get_countries` (es ligero y rápido).")


# --------------------------------------------------------------
# Función para probar una API key
# --------------------------------------------------------------
TEST_URL = "https://api-tennis.com/tennis/?method=get_countries&APIkey={api_key}"


def mask_key(key: str, visible_start: int = 4, visible_end: int = 3) -> str:
    """Enmascara la API key para no mostrarla completa en la interfaz."""
    key = key.strip()
    if len(key) <= visible_start + visible_end:
        return "*" * len(key)
    return f"{key[:visible_start]}****{key[-visible_end:]}"


def check_api_key(key: str, timeout: float = 10.0):
    """Hace un request de prueba a api-tennis.com para verificar la key."""
    url = TEST_URL.format(api_key=key.strip())
    t0 = time.time()
    try:
        resp = requests.get(url, timeout=timeout)
        elapsed = time.time() - t0

        status_code = resp.status_code

        # Intentamos leer JSON, pero la respuesta podría no serlo si hay error raro
        try:
            data = resp.json()
        except Exception:
            data = {}

        # Lógica simple de validación
        if status_code == 200:
            if isinstance(data, dict) and "result" in data:
                return {
                    "ok": True,
                    "status_code": status_code,
                    "elapsed": elapsed,
                    "msg": "OK (200 con 'result' en la respuesta)"
                }
            else:
                return {
                    "ok": False,
                    "status_code": status_code,
                    "elapsed": elapsed,
                    "msg": "200 pero sin campo 'result' en la respuesta"
                }

        elif status_code == 401:
            return {
                "ok": False,
                "status_code": status_code,
                "elapsed": elapsed,
                "msg": "401 Unauthorized (API key inválida o sin permisos)"
            }
        elif status_code == 403:
            return {
                "ok": False,
                "status_code": status_code,
                "elapsed": elapsed,
                "msg": "403 Forbidden (acceso denegado)"
            }
        elif status_code == 429:
            return {
                "ok": False,
                "status_code": status_code,
                "elapsed": elapsed,
                "msg": "429 Too Many Requests (límite de llamadas alcanzado)"
            }
        else:
            return {
                "ok": False,
                "status_code": status_code,
                "elapsed": elapsed,
                "msg": f"Error HTTP {status_code}"
            }

    except requests.exceptions.Timeout:
        elapsed = time.time() - t0
        return {
            "ok": False,
            "status_code": None,
            "elapsed": elapsed,
            "msg": "Timeout (no hubo respuesta dentro del límite)"
        }
    except Exception as e:
        elapsed = time.time() - t0
        return {
            "ok": False,
            "status_code": None,
            "elapsed": elapsed,
            "msg": f"Excepción: {e}"
        }


# --------------------------------------------------------------
# Botón para ejecutar la prueba
# --------------------------------------------------------------
st.subheader("2️⃣ Ejecutar prueba")

if st.button("🚀 Probar API keys"):
    # Procesar el texto en una lista de keys
    raw_lines = keys_text.splitlines()
    api_keys = [line.strip() for line in raw_lines if line.strip()]

    if not api_keys:
        st.warning("No se encontró ninguna API key. Asegúrate de pegar al menos una.")
    else:
        st.info(f"Probando {len(api_keys)} API key(s)…")

        results = []
        progress = st.progress(0)
        status_placeholder = st.empty()

        for idx, key in enumerate(api_keys, start=1):
            status_placeholder.write(f"Probando key {idx}/{len(api_keys)}…")
            result = check_api_key(key, timeout=timeout_sec)

            results.append({
                "API Key (enmascarada)": mask_key(key),
                "¿Funciona?": "✅ Sí" if result["ok"] else "❌ No",
                "HTTP Status": result["status_code"] if result["status_code"] is not None else "N/A",
                "Tiempo (s)": round(result["elapsed"], 3) if result["elapsed"] is not None else None,
                "Detalle": result["msg"],
            })

            progress.progress(idx / len(api_keys))

        status_placeholder.write("Prueba finalizada ✔")

        # Convertimos a DataFrame para mostrar tabla bonita
        df_results = pd.DataFrame(results)

        st.subheader("3️⃣ Resultados")
        st.dataframe(df_results, use_container_width=True)

        # Resumen rápido
        ok_count = sum(1 for r in results if r["¿Funciona?"] == "✅ Sí")
        fail_count = len(results) - ok_count

        st.success(f"API keys OK: {ok_count} · API keys con error: {fail_count}")

        # Opción para descargar resultados a CSV
        csv_bytes = df_results.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="💾 Descargar resultados en CSV",
            data=csv_bytes,
            file_name="resultado_api_keys_api_tennis.csv",
            mime="text/csv",
        )
