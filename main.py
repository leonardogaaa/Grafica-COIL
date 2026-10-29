from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import requests
from scipy.interpolate import make_interp_spline

# Coordenadas exactas de las ciudades solicitadas
CIUDADES = {
    "Arequipa (Peru)": {"lat": -16.3988, "lon": -71.5350},
    "Bogota (Colombia)": {"lat": 4.7110, "lon": -74.0721},
    "Hidalgo (Mexico)": {"lat": 20.1256, "lon": -98.7364},  }

def obtener_datos_pasados(dias_atras=30):
    """
    Obtiene exactamente los datos históricos diarios reales de los últimos N días 
    para las tres ciudades (tal como en tu código original).
    """
    hoy = datetime.now().date()
    inicio = hoy - timedelta(days=dias_atras)
    
    todos_los_registros = []
    
    for nombre, coords in CIUDADES.items():
        # Consulta directa diaria de Open-Meteo Archive
        url = (
            f"https://archive-api.open-meteo.com/v1/archive?"
            f"latitude={coords['lat']}&longitude={coords['lon']}"
            f"&start_date={inicio}&end_date={hoy}"
            f"&daily=temperature_2m_mean"
        )
        
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error al obtener datos para {nombre}: {response.status_code}")
            continue
            
        data = response.json()
        fechas = data["daily"]["time"]
        temperaturas = data["daily"]["temperature_2m_mean"]
        
        for f, t in zip(fechas, temperaturas):
            if t is not None:
                todos_los_registros.append({
                    "Ubicacion": nombre,
                    "Tiempo": pd.to_datetime(f),
                    "Temperatura": t
                })
            
    return pd.DataFrame(todos_los_registros)

def generar_grafica_diaria_suavizada(df):
    """
    Mantiene el formato de tu gráfica original (las 3 ciudades juntas con sus puntos diarios),
    pero curva las líneas de manera fluida y continua.
    """
    if df.empty:
        print("No hay datos históricos para graficar.")
        return

    plt.figure(figsize=(14, 7))
    
    # Colores estándar para mantener el orden de las ubicaciones
    colores = {
        "Arequipa (Peru)": "#1f77b4", 
        "Bogota (Colombia)": "#ff7f0e", 
        "Hidalgo (Mexico)": "#2ca02c"
    }

    # Iterar sobre cada ciudad para dibujarlas en la misma gráfica
    for ubicacion, grupo in df.groupby("Ubicacion"):
        grupo = grupo.sort_values("Tiempo").reset_index(drop=True)
        
        # Convertir fechas a números ordinales para los cálculos matemáticos
        x = mdates.date2num(grupo["Tiempo"])
        y = grupo["Temperatura"].values
        color_actual = colores.get(ubicacion, "black")

        # Dibujar los puntos reales (los círculos pequeños de tus datos diarios)
        plt.scatter(grupo["Tiempo"], y, color=color_actual, s=30, zorder=3)

        # Crear una línea curva y suave que pase por los puntos diarios
        if len(x) > 3:
            x_suave = np.linspace(x.min(), x.max(), 300)
            try:
                # Spline cúbico o cuadrático para suavizar la línea
                spline = make_interp_spline(x, y, k=3)
                y_suave = spline(x_suave)
                tiempo_suave = mdates.num2date(x_suave)
                
                plt.plot(tiempo_suave, y_suave, color=color_actual, linewidth=2, label=ubicacion, zorder=2)
            except Exception:
                # Fallback si ocurre algún detalle numérico
                plt.plot(grupo["Tiempo"], y, color=color_actual, linewidth=2, label=ubicacion, zorder=2)
        else:
            plt.plot(grupo["Tiempo"], y, color=color_actual, linewidth=2, label=ubicacion, zorder=2)

    # Configuración de la gráfica idéntica a tu formato original pero con curvas
    plt.title("Evolución Histórica de Temperatura (Promedio Diario - Curvas Suavizadas)", fontsize=14, fontweight='bold')
    plt.xlabel("Fecha", fontsize=12)
    plt.ylabel("Temperatura (°C)", fontsize=12)
    
    # Formato de fechas en el eje X
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(title="Ubicaciones")
    plt.tight_layout()
    
    print("Mostrando gráfica diaria unificada con líneas curvas...")
    plt.show()

# ==========================================
# EJECUCIÓN PRINCIPAL
# ==========================================
if __name__ == "__main__":
    print("Consultando datos diarios a la API de Open-Meteo...")
    df_clima = obtener_datos_pasados(dias_atras=30)
    
    if not df_clima.empty:
        generar_grafica_diaria_suavizada(df_clima)
