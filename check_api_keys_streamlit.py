# check_api_keys_streamlit.py
# App en Streamlit para probar varias API keys de https://api.api-tennis.com/

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

st.caption(
    "Según la documentación oficial, la URL es "
    "`https://api.api-tennis.com/tennis/?method=...&APIkey=...`."
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
    "Se usa el método `get_events` porque sólo requiere `APIkey` (no fechas ni parámetros extra)."
)

# ==========================
# Funciones auxiliares
# ==========================
# OJO: dominio correcto según documentación: api.api-tennis.com
# Ver doc: https://api.api-tennis.com/tennis/?method=get_events&APIkey=!_your_account_APIkey_!
TEST_URL = "https://api.api-tennis.com/tennis/?method=get_events&APIkey={api_key}"


def mask_key(key: str, visible_start: int = 4, visible_end: int = 3) -> str:
    """Enmascara la API key para no mostrarla completa."""
    key = key.strip()
    if len(key) <= visible_start + visible_end:
        return "*" * len(key)
    return f"{key[:visible_start]}****{key[-visible_end:]}"


def check_api_key(key: str, timeout: float = 10.0) -> dict:
    """
    Hace un request a api.api-tennis.com para verificar una API key.
    Usa el método get_events (no requiere parámetros extra).
    Devuelve: ok, status_code, elapsed, msg, success, raw_error.
    """
    url = TEST_URL.format(api_key=key.strip())
    t0 = time.time()

    try:
        resp = requests.get(url, timeout=timeout)
        elapsed = time.time() - t0
        status_code = resp.status_code

        raw_text = resp.text  # por si la respuesta no es JSON

        # Intentar parsear JSON
        data = None
        try:
            data = resp.json()
        except Exception:
            data = None

        # Si no es 200, ya es error HTTP
        if status_code != 200:
            return {
                "ok": False,
                "status_code": status_code,
                "elapsed": elapsed,
                "msg": f"Error HTTP {status_code}",
                "success_field": None,
                "raw_error": raw_text[:300],  # recortado para debug
            }

        # Si es 200, revisar estructura de JSON
        if isinstance(data, dict):
            success_field = data.get("success")
            # Según doc, success=1 significa OK
            if success_field == 1:
                msg = "OK (success=1, API key válida y método permitido)"
                ok = True
            else:
                msg = f"Respuesta 200 pero success={success_field} (posible API key sin plan adecuado o error lógico)"
                ok = False
        else:
            success_field = None
            msg = "200 pero respuesta no es JSON válido o no es dict"
            ok = False

        return {
            "ok": ok,
            "status_code": status_code,
            "elapsed": elapsed,
            "msg": msg,
            "success_field": success_field,
            "raw_error": None if ok else raw_text[:300],
        }

    except requests.exceptions.Timeout:
        elapsed = time.time() - t0
        return {
            "ok": False,
            "status_code": None,
            "elapsed": elapsed,
            "msg": "Timeout (no hubo respuesta dentro del límite)",
            "success_field": None,
            "raw_error": None,
        }
    except Exception as e:
        elapsed = time.time() - t0
        return {
            "ok": False,
            "status_code": None,
            "elapsed": elapsed,
            "msg": f"Excepción: {e}",
            "success_field": None,
            "raw_error": None,
        }

# ==========================
# Lógica principal
# ==========================
st.subheader("2️⃣ Ejecutar prueba")

if st.button("🚀 Probar API keys"):
    raw_lines = keys_text.splitlines()
    api_keys = [line.strip() for line in raw_lines if line.strip()]

    if not api_keys:
        st.warning("No se encontró ninguna API key. Pega al menos una.")
    else:
        st.info(f"Probando {len(api_keys)} API key(s)…")

        progress_bar = st.progress(0)
        status_placeholder = st.empty()

        results = []
        debug_rows = []

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
                    "success (JSON)": result.get("success_field"),
                    "Tiempo (s)": round(result["elapsed"], 3)
                    if result["elapsed"] is not None
                    else None,
                    "Detalle": result["msg"],
                }
            )

            if result.get("raw_error"):
                debug_rows.append(
                    {
                        "API Key (enmascarada)": mask_key(key),
                        "Raw response (recortada)": result["raw_error"],
                    }
                )

            progress_bar.progress(idx / len(api_keys))

        status_placeholder.write("Prueba finalizada ✔")

        df = pd.DataFrame(results)

        st.subheader("3️⃣ Resultados")
        st.dataframe(df, use_container_width=True)

        ok_count = sum(1 for r in results if r["¿Funciona?"] == "✅ Sí")
        fail_count = len(results) - ok_count

        st.success(
            f"API keys OK: {ok_count} · API keys con error: {fail_count}"
        )

        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="💾 Descargar resultados en CSV",
            data=csv_bytes,
            file_name="resultado_api_keys_api_tennis.csv",
            mime="text/csv",
        )

        if debug_rows:
            st.subheader("🐞 Debug de respuestas con error (opcional)")
            st.write(
                "Aquí se muestran los primeros caracteres de la respuesta cuando no fue claramente success=1."
            )
            st.dataframe(pd.DataFrame(debug_rows), use_container_width=True)
