import pandas as pd
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
current_dir = os.path.normpath(current_dir)
current_dir = current_dir.replace("\\", "/")

def LK_mapping(number,LK_dict):
    try:
        return LK_dict[int(str(number)[:3]+'000')]
    except:
        pass

def energy_data(city, level, year=2022):
    energy = pd.read_csv(current_dir + '/data/external/EA-B Recherche-Ergebnis_Anteil_am_Verbrauch.csv')
    EE_pie = pd.read_csv(current_dir + '/data/external/EA-B Recherche-Ergebnis_EE-Anteile.csv')

    LK = energy[energy['Verwaltungsebene']=='Landkreis']
    LK_dict = LK[['Verwaltungseinheit','Name']].set_index('Verwaltungseinheit').to_dict()['Name']

    if level == 'Lkr':
        EE_i = EE_pie[(EE_pie['Name']==city) & (EE_pie['Verwaltungsebene']=='Landkreis')].reset_index(drop=True)
        if len(EE_i.index)==0:
            EE_i = EE_pie[(EE_pie['Name'].str.contains(city)) & (EE_pie['Verwaltungsebene']=='Landkreis')].reset_index(drop=True)
    else:
        EE_i = EE_pie[(EE_pie['Name']==city) & (EE_pie['Verwaltungsebene']=='Gemeinde')].reset_index(drop=True)
        if len(EE_i.index)==0:
            EE_i = EE_pie[(EE_pie['Name'].str.contains(city)) & (EE_pie['Verwaltungsebene']!='Landkreis')].reset_index(drop=True)

    
    EE_i['Landkreis'] = EE_i['Verwaltungseinheit'].apply(lambda x: LK_mapping(x,LK_dict).split(' ')[0])

    Produktion_i = float(EE_i[f'Stromproduktion EE {year} (MWh/a)'][0])

    LK_name = EE_i['Landkreis'][0]

    if level == "Krfr.St":
        energy_i = energy[(energy['Name'].str.contains(EE_i['Landkreis'][0]))].reset_index(drop=True)['Stromverbrauch (MWh/a)'][0]
    else:
        try:
            energy_i = energy[(energy['Name']==EE_i.loc[0,'Landkreis']) & (energy['Verwaltungsebene']=='Landkreis')].reset_index(drop=True)['Stromverbrauch (MWh/a)'][0]
        except:
            energy_i = energy[(energy['Name'].str.contains(EE_i['Landkreis'][0])) & (energy['Verwaltungsebene']=='Landkreis')].reset_index(drop=True)['Stromverbrauch (MWh/a)'][0]
    
    
    energy_i = float(energy_i)
    # Print statement To make sure its the right Amberg
    
    export_energy = {
        "Wind": float(EE_i['Anteil Wind an Stromproduktion EE (%)'][0]), 
        "Solar": float(EE_i['Anteil PV an Stromproduktion EE (%)'][0]), 
        "Biomasse": float(EE_i['Anteil Biomasse an Stromproduktion EE (%)'][0]), 
        "Wasser": float(EE_i['Anteil Wasserkraft an Stromproduktion EE (%)'][0]), 
        "Anteil":round(Produktion_i/energy_i*100,1), 
        "link":"https://www.karten.energieatlas.bayern.de/start/?c=677751,5422939&z=8.01&l=atkis,37864384-e4fe-47de-8227-619bd33e1eda&t=energie"}
    print(f"LK_name: {LK_name}, Population: { EE_i["Einwohnerzahl"][0]}")
    return export_energy, LK_name


def load_kfz_table(path,file):
    df = pd.read_csv(path+file,delimiter=';',encoding='latin1',skiprows=5,skipfooter=4,engine='python')
    csv_date = df.columns[0].split(': ')[-1]
    df.columns = df.iloc[1]
    df = df[4:].reset_index(drop=True)

    column_names = df.columns.tolist()
    new_columns = ['Code','Gebiet']

    column_names[0] = new_columns[0]
    column_names[1] = new_columns[1]

    df.columns = column_names
    return df,csv_date

def kfz_data(city, LK_name, level):
    path = current_dir + '/data/external/KFZ/'
    files = os.listdir(path)
    if city not in LK_name: # What?
        level = 'Lkr'

    years = []
    benzin = []
    diesel = []
    hybrid = []
    elektro = []
    #gesamt = []

    for file in files:
        df, csv_date = load_kfz_table(path,file)
        df_LK = df[df['Gebiet'].str.contains(LK_name)].reset_index(drop=True)
        if len(df_LK.index) > 1:
            if level == 'Lkr':
                df_LK = df_LK[df_LK['Gebiet'].str.contains('Lkr')].reset_index(drop=True)
            else:
                df_LK = df_LK[df_LK['Gebiet'].str.contains('Krfr')].reset_index(drop=True)
        years.append(int(csv_date.split('.')[-1]))
        benzin_i = int(df_LK['Benzin'][0])
        diesel_i = int(df_LK['Diesel'][0])
        hybrid_i = int(df_LK['Hybrid'][0])
        elektro_i = int(df_LK['Elektro'][0])
        #gesamt_i = int(df_LK['Insgesamt'][0])

        benzin.append(benzin_i)
        diesel.append(diesel_i)
        hybrid.append(hybrid_i)
        elektro.append(elektro_i)
        #gesamt.append(gesamt_i)
        
    gesamt = int(df_LK['Insgesamt'][0])
    percentage = {'Benzin':round(benzin_i/gesamt*100), 'Diesel':round(diesel_i/gesamt*100), 'Hybrid':round(hybrid_i/gesamt*100), 'Elektro':round(elektro_i/gesamt*100)}

    export_kfz = {'Jahr':years, 
                  'Benzin':benzin, 
                  'Diesel':diesel, 
                  'Hybrid':hybrid, 
                  'Elektro':elektro, 
                  'Anteil':percentage, 
                  'link':'https://open.bydata.de/datasets/46251-003-d?locale=de'}
    return export_kfz


def population_data(city, level):
    df = pd.read_csv(current_dir + '/data/external/12411-000-D.csv',delimiter=';',encoding='latin',skiprows=6,skipfooter=4,engine='python')
    df.rename(columns={'Unnamed: 0': 'Code', 'Unnamed: 1': 'Gebiet'},inplace=True)
    df = df.dropna(subset='Gebiet').reset_index(drop=True)

    years = [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023]
    df_i = df[df['Gebiet'].str.contains(city)].reset_index(drop=True)
    if level == 'Lkr':
        df_i = df_i[df_i['Gebiet'].str.contains('Lkr')].reset_index(drop=True)
    elif level == 'Krfr.St':
        df_i = df_i[df_i['Gebiet'].str.contains('Krfr.St')].reset_index(drop=True)
    else:
        df_i = df_i[~df_i['Gebiet'].str.contains('Lkr')].reset_index(drop=True)
    if len(df_i.index) > 1:
        if sum(df['Gebiet'].str.replace(' ','')==city)>0:
            df_i = df_i[df_i['Gebiet'].str.replace(' ','')==city].reset_index(drop=True)
        else:
            df_i = df_i[df_i['Gebiet'].str.contains(city + ' ')]
    gesamt = []
    trend = []
    for year in years:
        current = int(df_i[str(year)][0])
        last = int(df_i[str(year-1)][0])
        gesamt.append(current)
        trend.append(current-last)

    export_population = {'Jahr':years, 'Gesamt':gesamt, 'Entwicklung':trend, 'link':'https://open.bydata.de/datasets/12411-000-d?locale=de'}
    return export_population


def mobile_data(city, level):
    df = pd.read_excel(current_dir + '/data/external/bba_06_2023.xlsx', sheet_name='Fläche', skiprows=2, header=1)
    df = df[df['Land'] == 'Freistaat Bayern']
    df_i = df[df['Name'].str.replace(" ", "").str.contains(city.replace(" ", ""))]
    if level == 'Lkr':
        df_i = df_i[(df_i['Verwaltungsebene'].str.contains('Kreis')) & (df_i['Name'].str.contains('Landkreis'))].reset_index(drop=True)
    elif level == 'Krfr.St':
        df_i = df_i[(df_i['Verwaltungsebene'].str.contains('Kreis')) & (df_i['Name'].str.contains('Kreisfreie Stadt'))].reset_index(drop=True)
    else:
        df_i = df_i[df_i['Verwaltungsebene'].str.contains('Gemeinde')].reset_index(drop=True)    
        if len(df_i.index) > 1:
            df_i['filter_name'] = df_i['Name'].apply(lambda x: x.split(' ')[-1])
            df_i = df_i[df_i['filter_name']==city].reset_index(drop=True)
    
    print("Mobilfunk Kreis: ", df_i["Kreis"])
    export_mobile = {'2G':round(df_i['2G'][0],1), 
                     '4G':round(df_i['4G'][0],1), 
                     '5G':round(df_i['5G'][0],1), 
                     'link':'https://gigabitgrundbuch.bund.de/GIGA/DE/MobilfunkMonitoring/Downloads/start.html'}
    return export_mobile