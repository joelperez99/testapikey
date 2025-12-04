# check_api_keys_streamlit.py
# App en Streamlit para probar varias API keys de https://api-tennis.com/

import time
import requests
import pandas as pd
import streamlit as st


# ==========================
# Configuración de la página
# ==========================
st.set_page_config(
    page_title="🔑 Test API Keys · api-tennis.com",
    layout="centered",
)

st.title("🔑 Verificador de API keys · api-tennis.com")
st.write(
    "Pega varias API keys de **api-tennis.com** (una por línea) y haz clic en "
    "**Probar API keys** para verificar cuáles están funcionando."
)

st.markdown("---")


# ==========================
# Parámetros de entrada
# ==========================
st.subheader("1️⃣ API keys")

default_example = "APIKEY_1_AQUI\nAPIKEY_2_AQUI\nAPIKEY_3_AQUI"

keys_text = st.text_area(
    "Pega aquí tus API keys (una por línea):",
    value=default_example,
    height=150,
)

timeout_sec = st.number_input(
    "Timeout por request (segundos):",
    min_value=1.0,
    max_value=60.0,
    value=10.0,
    step=1.0,
)

st.caption(
    "Se usa el endpoint `tennis/?method=get_countries` porque es ligero y rápido."
)


# ==========================
# Funciones auxiliares
# ==========================
TEST_URL = "https://api-tennis.com/tennis/?method=get_countries&APIkey={api_key}"


def mask_key(key: str, visible_start: int = 4, visible_end: int = 3) -> str:
    """
    Enmascara la API key para no mostrarla completa.
    Ej: ABCD****XYZ
    """
    key = key.strip()
    if len(key) <= visible_start + visible_end:
        return "*" * len(key)
    return f"{key[:visible_start]}****{key[-visible_end:]}"


def check_api_key(key: str, timeout: float = 10.0) -> dict:
    """
    Hace un request a api-tennis.com para verificar una API key.
    Devuelve un diccionario con ok, status_code, elapsed, msg.
    """
    url = TEST_URL.format(api_key=key.strip())
    t0 = time.time()

    try:
        resp = requests.get(url, timeout=timeout)
        elapsed = time.time() - t0
        status_code = resp.status_code

        # Intentar parsear JSON, pero no es obligatorio
        try:
            data = resp.json()
        except Exception:
            data = {}

        # Lógica básica de validación
        if status_code == 200:
            if isinstance(data, dict) and "result" in data:
                ok = True
                msg = "OK (200 con 'result' en la respuesta)"
            else:
                ok = False
                msg = "200 pero sin campo 'result' en la respuesta"
        elif status_code == 401:
            ok = False
            msg = "401 Unauthorized (API key inválida o sin permisos)"
        elif status_code == 403:
            ok = False
            msg = "403 Forbidden (acceso denegado)"
        elif status_code == 429:
            ok = False
            msg = "429 Too Many Requests (límite de llamadas alcanzado)"
        else:
            ok = False
            msg = f"Error HTTP {status_code}"

        return {
            "ok": ok,
            "status_code": status_code,
            "elapsed": elapsed,
            "msg": msg,
        }

    except requests.exceptions.Timeout:
        elapsed = time.time() - t0
        return {
            "ok": False,
            "status_code": None,
            "elapsed": elapsed,
            "msg": "Timeout (no hubo respuesta dentro del límite)",
        }
    except Exception as e:
        elapsed = time.time() - t0
        return {
            "ok": False,
            "status_code": None,
            "elapsed": elapsed,
            "msg": f"Excepción: {e}",
        }


# ==========================
# Lógica principal
# ==========================
st.subheader("2️⃣ Ejecutar prueba")

if st.button("🚀 Probar API keys"):
    # Parsear el text area en líneas limpias
    raw_lines = keys_text.splitlines()
    api_keys = [line.strip() for line in raw_lines if line.strip()]

    if not api_keys:
        st.warning("No se encontró ninguna API key. Pega al menos una.")
    else:
        st.info(f"Probando {len(api_keys)} API key(s)…")

        progress_bar = st.progress(0)
        status_placeholder = st.empty()

        results = []

        for idx, key in enumerate(api_keys, start=1):
            status_placeholder.write(f"Probando key {idx}/{len(api_keys)}…")

            result = check_api_key(key, timeout=timeout_sec)

            results.append(
                {
                    "API Key (enmascarada)": mask_key(key),
                    "¿Funciona?": "✅ Sí" if result["ok"] else "❌ No",
                    "HTTP Status": result["status_code"]
                    if result["status_code"] is not None
                    else "N/A",
                    "Tiempo (s)": round(result["elapsed"], 3)
                    if result["elapsed"] is not None
                    else None,
                    "Detalle": result["msg"],
                }
            )

            progress_bar.progress(idx / len(api_keys))

        status_placeholder.write("Prueba finalizada ✔")

        # Mostrar resultados en tabla
        df = pd.DataFrame(results)

        st.subheader("3️⃣ Resultados")
        st.dataframe(df, use_container_width=True)

        # Resumen
        ok_count = sum(1 for r in results if r["¿Funciona?"] == "✅ Sí")
        fail_count = len(results) - ok_count

        st.success(
            f"API keys OK: {ok_count} · API keys con error: {fail_count}"
        )

        # Botón para descargar CSV
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="💾 Descargar resultados en CSV",
            data=csv_bytes,
            file_name="resultado_api_keys_api_tennis.csv",
            mime="text/csv",
        )
