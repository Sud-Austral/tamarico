import pandas as pd
from datetime import datetime
import re
import os
import time
import requests
from bs4 import BeautifulSoup

def getURLDetalle(name):
    return f"https://snifa.sma.gob.cl/SeguimientoAmbiental/Ficha/{name}"

def getDatos(url):
    response = requests.get(url)
    idFicha = url[-7:]
    # Verificar si la solicitud fue exitosa
    if response.status_code == 200:
        # Obtener el contenido HTML de la respuesta
        html_content = response.text
        # Parsear el contenido HTML con BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        titulo = soup.select_one('body > div:nth-of-type(6) > div:nth-of-type(3) > div > div:nth-of-type(1) > div > div > h3') \
                #.get_text(strip=True)
        titulo = [text.strip() for text in titulo.stripped_strings]
        titulo = ' '.join(titulo)
        periodo = soup.select_one('body > div:nth-of-type(6) > div:nth-of-type(3) > div > div:nth-of-type(1) > div > div > h4:nth-of-type(1)') \
                .get_text(strip=True)
        frecuencia = soup.select_one('body > div:nth-of-type(6) > div:nth-of-type(3) > div > div:nth-of-type(1) > div > div > h4:nth-of-type(2)') \
                .get_text(strip=True)
        subComponente = soup.select_one('body > div:nth-of-type(6) > div:nth-of-type(3) > div > div:nth-of-type(1) > div > div > h4:nth-of-type(3)') \
                .get_text(strip=True)
        list_items = soup.select('body > div:nth-of-type(6) > div:nth-of-type(3) > div > div:nth-of-type(2) > div > div > div > div:nth-of-type(4) > div > ul > li')
        UnidadFiscalizable = list_items[0].get_text(strip=True)
        UnidadFiscalizable = [text.strip() for text in list_items[0].stripped_strings]
        UnidadFiscalizable = ' '.join(UnidadFiscalizable)
        urlUnidadFiscalizable = "https://snifa.sma.gob.cl/" + list_items[0].find('a').get('href')
        descripcions = soup.select('body > div:nth-of-type(6) > div:nth-of-type(4) > div > div')
        descripcion = [text.strip() for text in descripcions[0].stripped_strings]
        descripcion = ' '.join(descripcion)
        
        acumular = []
        table = soup.find('table')
        for row in table.find_all('tr')[1:]:
            # Extraer todas las celdas de la fila
            cells = row.find_all(['td', 'th'])

            # Inicializar una lista para almacenar el texto de las celdas y los enlaces
            cell_texts = []
            hrefs = []

            # Iterar sobre las celdas de la fila
            for cell in cells:
                # Extraer el texto de la celda
                cell_text = cell.get_text(strip=True)
                cell_texts.append(cell_text)

                # Verificar si la celda contiene un enlace
                link = cell.find('a')
                if link:
                    href = link.get('href')
                    hrefs.append(href)
            #cell_texts.append(hrefs)
            acumular.append(cell_texts+ hrefs)
        df = pd.DataFrame(acumular)
        df["idFicha"] = idFicha
        df[4] = df[4].apply(lambda x: f"https://snifa.sma.gob.cl{x}")
        
        return [idFicha,titulo,periodo,frecuencia,subComponente,UnidadFiscalizable,urlUnidadFiscalizable,descripcion,df]
    else:
        return [None,None,None,None,None,None,None,None,None]

if __name__ == '__main__':
    url = "https://snifa.sma.gob.cl/SeguimientoAmbiental/Resultado"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-CL,es;q=0.8,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://snifa.sma.gob.cl",
        "Connection": "keep-alive",
        "Referer": "https://snifa.sma.gob.cl/SeguimientoAmbiental/RCA",
        "Cookie": "_ga_H7DTM3S58G=GS1.1.1716839341.1.1.1716839343.0.0.0; _ga=GA1.1.1660087163.1716839341",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1"
    }
    data = {
        "nombre": "tamarico",
        "categoria": "",
        "numero": "",
        "anno": "",
        "idsea": ""
    }

    #response = requests.post(url, headers=headers, data=data)
    response = requests.post(url, data=data)
    print("Primer data")
    df = pd.read_html(response.text)
    dfMaster = df[0].copy()
    dfMaster["URL"] = dfMaster["#"].apply(getURLDetalle)
    dfMaster[["idFicha","Titulo","Periodo","Frecuencia","SubComponente","UnidadFiscalizable","urlUnidadFiscalizable","descripcion","df"]] = dfMaster["URL"].apply(getDatos).apply(pd.Series)
    dfDescarga = pd.concat(list(dfMaster["df"]))
    for i in dfDescarga.itertuples():
        directorio = i[6]
        name = i[2]
        url = i[5]
        idFile = url[61:]
        try:
            os.mkdir(directorio)
        except:
            pass
        respuesta = requests.get(f"https://api-ssa.sma.gob.cl/api/v1/GetDocumentoById/{idFile}")
        #print(respuesta.json()["data"]["InternalFileName"])
        params = {
            "nombre": respuesta.json()["data"]["InternalFileName"]
        }
        response2 = requests.get("https://api-ssa.sma.gob.cl/api/v1/documentos/incidente/descargar", params=params)
        with open(f"{directorio}/{name}", "wb") as f:
            f.write(response2.content)
    dfMaster  .to_excel("Master.xlsx"  ,index=False)
    dfDescarga.to_excel("Archivos.xlsx",index=False)

    
