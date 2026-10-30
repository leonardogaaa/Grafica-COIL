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
    "Hidalgo (Mexico)": {"lat": 20.1256, "lon": -98.7364}, }


def obtener_datos_pasados(fecha_inicio, fecha_fin):
    """
    Obtiene los datos históricos diarios de Open-Meteo Archive para un rango de fechas específico.
    
    Parámetros:
    - fecha_inicio (str o datetime.date): Fecha de inicio en formato 'YYYY-MM-DD'
    - fecha_fin (str o datetime.date): Fecha de fin en formato 'YYYY-MM-DD'
    """
    # Asegurar formato de cadena si se pasan como objetos datetime o date
    if isinstance(fecha_inicio, (datetime, pd.Timestamp)):
        fecha_inicio = fecha_inicio.strftime('%Y-%m-%d')
    if isinstance(fecha_fin, (datetime, pd.Timestamp)):
        fecha_fin = fecha_fin.strftime('%Y-%m-%d')
        
    todos_los_registros = []
    
    for nombre, coords in CIUDADES.items():
        # Consulta directa diaria de Open-Meteo Archive con el rango personalizado
        url = (
            f"https://archive-api.open-meteo.com/v1/archive?"
            f"latitude={coords['lat']}&longitude={coords['lon']}"
            f"&start_date={fecha_inicio}&end_date={fecha_fin}"
            f"&daily=temperature_2m_mean"
        )
        
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error al obtener datos para {nombre}: {response.status_code}")
            continue
            
        data = response.json()
        if "daily" not in data:
            print(f"No se encontraron datos diarios para {nombre} en el rango especificado.")
            continue
            
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

def generar_grafica_diaria_suavizada(df, fecha_inicio, fecha_fin):
    """
    Mantiene el formato de la gráfica original con curvas suaves,
    actualizando el título con el rango de fechas consultado.
    """
    if df.empty:
        print("No hay datos históricos para graficar en el rango seleccionado.")
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

        # Dibujar los puntos reales
        plt.scatter(grupo["Tiempo"], y, color=color_actual, s=30, zorder=3)

        # Crear una línea curva y suave que pase por los puntos diarios
        if len(x) > 3:
            x_suave = np.linspace(x.min(), x.max(), 300)
            try:
                # Spline cúbico para suavizar la línea
                spline = make_interp_spline(x, y, k=3)
                y_suave = spline(x_suave)
                tiempo_suave = mdates.num2date(x_suave)
                
                plt.plot(tiempo_suave, y_suave, color=color_actual, linewidth=2, label=ubicacion, zorder=2)
            except Exception:
                plt.plot(grupo["Tiempo"], y, color=color_actual, linewidth=2, label=ubicacion, zorder=2)
        else:
            plt.plot(grupo["Tiempo"], y, color=color_actual, linewidth=2, label=ubicacion, zorder=2)

    # Configuración de la gráfica con el rango dinámico en el título
    plt.title(f"Evolución Histórica de Temperatura ({fecha_inicio} al {fecha_fin})", fontsize=14, fontweight='bold')
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
    # MODIFICA AQUÍ TUS FECHAS DE INICIO Y FIN (Formato 'YYYY-MM-DD')
    # Nota: La API Archive de Open-Meteo cuenta con datos históricos hasta hace unos días respecto al presente.
    FECHA_INICIO = "2026-09-25"
    FECHA_FIN = "2026-10-25"
    
    print(f"Consultando datos desde {FECHA_INICIO} hasta {FECHA_FIN} en Open-Meteo...")
    df_clima = obtener_datos_pasados(FECHA_INICIO, FECHA_FIN)
    
    if not df_clima.empty:
        generar_grafica_diaria_suavizada(df_clima, FECHA_INICIO, FECHA_FIN)
