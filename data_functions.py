import pandas as pd
import os


def rename_duplicates(Gemeinde: str, Landkreis: str, name_duplicates: list) -> str:
    if Gemeinde in name_duplicates:
        return f'{Gemeinde} ({Landkreis})'
    else:
        return Gemeinde


def first_setup() -> pd.DataFrame:
    mobile = pd.read_excel('data/external/bba_01_2024.xlsx', sheet_name='Fläche', skiprows=2, header=1)
    mobile = mobile[(mobile['Land'] == 'Freistaat Bayern') & (mobile['Verwaltungsebene'] != '2 - Land') & (
        ~mobile['Name'].str.contains('Bezirk'))].reset_index(drop=True)

    # Landkreis-Code auf einheitliches Format bringen
    mobile['code_fill'] = mobile['AGS'].apply(lambda x: int(str(x)[1:].ljust(6, '0')))
    mobile['Name'] = mobile['Name'].apply(lambda x: x.replace('Gemeinde ', '').replace('Landkreis ', ''))

    # Alle Doppelungen löschen -> Kreisfreie Städte tauchen nur in der Liste für Gemeinde/Städte auf
    mobile = mobile.sort_values('Verwaltungsebene', ascending=False, ignore_index=True)
    mobile.drop_duplicates('code_fill', ignore_index=True, inplace=True)

    # Jeder Gemeinde wird ihr Landkreis zugeordnen
    LK = mobile[mobile['Verwaltungsebene'] == '3 - Kreis']
    LK_dict = LK[['code_fill', 'Name']].set_index('code_fill').to_dict()['Name']
    mobile['LK_code'] = mobile['code_fill'].apply(lambda x: int(str(x)[:3] + '000'))
    mobile['Landkreis'] = mobile['LK_code'].map(LK_dict)

    # Suche nach allen mehrfach benannten Gemeinden und bei Bedarf Hinzufügen des Landkreises
    name_counts = mobile[mobile['Verwaltungsebene'] == '4 - Gemeinde']['Name'].value_counts()
    name_duplicates = name_counts[name_counts > 1].keys()
    mobile['Name'] = mobile.apply(lambda x: rename_duplicates(x.Name, x.Landkreis, name_duplicates), axis=1)

    # Datenfilter
    mobile = mobile[['code_fill', 'Name', 'Verwaltungsebene', '2G', '4G', '5G']]

    return mobile


def energy_data(code: int) -> dict:
    EE_pie = pd.read_csv('data/external/EA-B Recherche-Ergebnis_EE-Anteile.csv')
    EE_pie = EE_pie[EE_pie['Verwaltungsebene'] != 'Regierungsbezirk'].sort_values('Verwaltungsebene', ignore_index=True)

    # Alle Doppelungen löschen -> Kreisfreie Städte tauchen nur in der Liste für Gemeinde/Städte auf
    EE_pie.drop_duplicates('Verwaltungseinheit', ignore_index=True, inplace=True)

    EE_i = EE_pie[EE_pie['Verwaltungseinheit'] == code].reset_index(drop=True)

    export_energy = {
        "Wind": float(EE_i['Anteil Wind an Stromproduktion EE (%)'][0]),
        "Solar": float(EE_i['Anteil PV an Stromproduktion EE (%)'][0]),
        "Biomasse": float(EE_i['Anteil Biomasse an Stromproduktion EE (%)'][0]),
        "Wasser": float(EE_i['Anteil Wasserkraft an Stromproduktion EE (%)'][0]),
        "link": "https://www.karten.energieatlas.bayern.de/start/?c=677751,5422939&z=8.01&l=atkis,37864384-e4fe-47de-8227-619bd33e1eda&t=energie"}

    return export_energy


def kfz_data(code: int) -> dict:
    # Alle Dateien im Ordner "KFZ" werden eingelesen
    Kfz_path = 'data/external/KFZ/'
    Kfz_files = os.listdir(Kfz_path)

    # Da KFZ-Daten nur auf Kreisebene existieren, wird der Code auf Kreishierarchie gemappt
    code_lk = int(str(code)[:3] + '000')
    Kfz = pd.DataFrame([])

    for file in Kfz_files:
        Kfz_i = pd.read_csv(Kfz_path + file, encoding='latin', delimiter=';')
        # Landkreis-Code auf einheitliches Format bringen
        Kfz_i['code_fill'] = Kfz_i['1_Auspraegung_Code'].apply(lambda x: int(str(x)[1:].ljust(6, '0')))
        Kfz_i['Jahr'] = Kfz_i['Zeit'].apply(lambda x: x.split('.')[-1])
        Kfz_i = \
        Kfz_i[['code_fill', 'Jahr', '2_Auspraegung_Label', 'PKW__Personenkraftwagen_nach_Kraftstoffarten__Anzahl']][
            Kfz_i['code_fill'] == code_lk].reset_index(drop=True)
        Kfz = pd.concat([Kfz, Kfz_i], ignore_index=True, axis=0)

    Kfz.sort_values('Jahr', ignore_index=True, inplace=True)

    # Die benötigten Daten aus dem Dataframe extrahieren
    years = list(Kfz['Jahr'].unique())
    benzin = list(Kfz[Kfz['2_Auspraegung_Label'] == 'Benzin']['PKW__Personenkraftwagen_nach_Kraftstoffarten__Anzahl'])
    diesel = list(Kfz[Kfz['2_Auspraegung_Label'] == 'Diesel']['PKW__Personenkraftwagen_nach_Kraftstoffarten__Anzahl'])
    hybrid = list(Kfz[Kfz['2_Auspraegung_Label'] == 'Hybrid']['PKW__Personenkraftwagen_nach_Kraftstoffarten__Anzahl'])
    elektro = list(Kfz[Kfz['2_Auspraegung_Label'] == 'Elektro']['PKW__Personenkraftwagen_nach_Kraftstoffarten__Anzahl'])

    gesamt = \
    Kfz[(Kfz['Jahr'] == Kfz['Jahr'].max()) & (Kfz['2_Auspraegung_Label'] == 'Insgesamt')].reset_index(drop=True)[
        'PKW__Personenkraftwagen_nach_Kraftstoffarten__Anzahl'][0]

    percentage = {"Benzin": round(benzin[-1] / gesamt * 100), "Diesel": round(diesel[-1] / gesamt * 100),
                  "Hybrid": round(hybrid[-1] / gesamt * 100), "Elektro": round(elektro[-1] / gesamt * 100)}

    export_kfz = {"Jahr": years,
                  "Benzin": benzin,
                  "Diesel": diesel,
                  "Hybrid": hybrid,
                  "Elektro": elektro,
                  "Anteil": percentage,
                  "link": "https://open.bydata.de/datasets/46251-003-d?locale=de"}
    return export_kfz


def population_data(code: int) -> dict:
    Bevoelkerung = pd.read_csv('data/external/12411-001_flat.csv', encoding='latin', delimiter=';')

    # Landkreis-Code auf einheitliches Format bringen
    Bevoelkerung['code_fill'] = Bevoelkerung['1_Auspraegung_Code'].apply(lambda x: int(str(x)[1:].ljust(6, '0')))

    # Spalten anpassen
    Bevoelkerung['Jahr'] = Bevoelkerung['Zeit'].apply(lambda x: x.split('.')[-1])
    Bevoelkerung.sort_values('Jahr', ignore_index=True, inplace=True)
    Bevoelkerung['BEVSTD__Bevoelkerung__Anzahl'] = Bevoelkerung['BEVSTD__Bevoelkerung__Anzahl'].apply(
        lambda x: int(x.replace('-', '0')))

    # Datenfilter
    Bevoelkerung = Bevoelkerung[['code_fill', 'Jahr', 'BEVSTD__Bevoelkerung__Anzahl']]

    years = list(Bevoelkerung['Jahr'].unique())
    Bevoelkerung_i = Bevoelkerung[Bevoelkerung['code_fill'] == code].reset_index(drop=True)
    counts = Bevoelkerung_i['BEVSTD__Bevoelkerung__Anzahl'].to_list()
    trends = [j - i for i, j in zip(counts[:-1], counts[1:])]

    export_population = {"Jahr": years[1:], "Gesamt": counts[1:], "Entwicklung": trends,
                         "link": "https://open.bydata.de/datasets/12411-000-d?locale=de"}
    return export_population


def mobile_data(code: int, mobile: pd.DataFrame) -> dict:
    mobile_i = mobile[mobile['code_fill'] == code].reset_index(drop=True)

    export_mobile = {"2G": round(mobile_i['2G'][0], 1),
                     "4G": round(mobile_i['4G'][0], 1),
                     "5G": round(mobile_i['5G'][0], 1),
                     "link": "https://gigabitgrundbuch.bund.de/GIGA/DE/MobilfunkMonitoring/Downloads/start.html"}
    return export_mobile
