import requests
from bs4 import BeautifulSoup
import csv
from io import StringIO
from datetime import datetime
from google.cloud import storage
import os

URL = "https://www.bcra.gob.ar/PublicacionesEstadisticas/Evolucion_moneda.asp"
BUCKET_NAME = "rpa-poc-files"
CSV_FILENAME = "precio_dolar.csv"

def scrape_dolar():
    # Descargar la página
    resp = requests.get(URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # La tabla que nos interesa tiene filas con fechas y valores, buscamos la última fecha disponible
    # Esto depende del formato HTML, inspeccionamos para encontrar la tabla correcta.
    # Tras inspección, asumiremos que la tabla con clase "form-table" contiene los datos
    
    table = soup.find("table", {"class": "form-table"})
    if not table:
        raise Exception("No se encontró la tabla de datos")

    rows = table.find_all("tr")

    # Buscamos la última fila con fecha y precio del dólar
    # Vamos a asumir que la primera columna es la fecha, y la columna "Dólar Estadounidense" tiene el valor
    # Según inspección, la columna del dólar está con nombre "Dólar Estadounidense" o similar
    
    # Extraemos encabezados para encontrar la columna del dólar
    headers = [th.get_text(strip=True) for th in rows[0].find_all("th")]
    if not headers:
        raise Exception("No se encontraron encabezados en la tabla")

    try:
        idx_fecha = headers.index("Fecha")
        idx_dolar = headers.index("Dólar Estadounidense")
    except ValueError:
        raise Exception("No se encontraron las columnas esperadas (Fecha, Dólar Estadounidense)")

    # La última fila con datos suele ser la última (excluyendo el encabezado)
    last_data_row = rows[-1]
    cols = last_data_row.find_all("td")
    if len(cols) <= max(idx_fecha, idx_dolar):
        raise Exception("Fila de datos incompleta")

    fecha_str = cols[idx_fecha].get_text(strip=True)
    dolar_str = cols[idx_dolar].get_text(strip=True).replace(",", ".")  # Por si el decimal es coma

    # Parseamos fecha y dólar
    fecha = datetime.strptime(fecha_str, "%d/%m/%Y").date()
    dolar = float(dolar_str)

    return fecha, dolar

def guardar_csv_en_bucket(fecha, dolar):
    # Creamos el CSV en memoria
    output = StringIO()
    writer = csv.writer(output)
    # Cabecera
    writer.writerow(["fecha", "moneda", "valor"])
    # Fila
    writer.writerow([fecha.isoformat(), "Dólar Estadounidense", dolar])

    data = output.getvalue()

    # Guardar en bucket GCS
    client = storage.Client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(CSV_FILENAME)
    blob.upload_from_string(data, content_type="text/csv")

    print(f"Archivo {CSV_FILENAME} guardado en bucket {BUCKET_NAME}")

def main(request=None):
    # Función para Cloud Run, request es opcional
    try:
        fecha, dolar = scrape_dolar()
        guardar_csv_en_bucket(fecha, dolar)
        return f"Datos guardados: {fecha} - {dolar}"
    except Exception as e:
        print(f"Error: {e}")
        return f"Error: {e}", 500

if __name__ == "__main__":
    print(main())

