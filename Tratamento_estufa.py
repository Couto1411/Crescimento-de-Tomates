import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os

def smooth_curve(values, points_per_hour=60):
    interpolated = np.interp(
        np.linspace(0, len(values)-1, len(values) * points_per_hour),
        np.arange(len(values)),
        values
    )
    return interpolated

def group_by_season(date):
    seasons = {
        'Verao': (datetime(2024, 1, 1), datetime(2024, 3, 20)),
        'Outono': (datetime(2024, 3, 21), datetime(2024, 6, 20)),
        'Inverno': (datetime(2024, 6, 21), datetime(2024, 9, 22)),
        'Primavera': (datetime(2024, 9, 23), datetime(2024, 12, 31))
    }
    for season, (start, end) in seasons.items():
        if date>=start  and date<end:
            return season
    return season

def group_by_month(date):
    seasons = {
        'Janeiro': (datetime(2024, 1, 1), datetime(2024, 1, 31)),
        'Fevereiro': (datetime(2024, 2, 1), datetime(2024, 2, 29)),
        'Marco': (datetime(2024, 3, 1), datetime(2024, 3, 31)),
        'Abril': (datetime(2024, 4, 1), datetime(2024, 4, 30)),
        'Maio': (datetime(2024, 5, 1), datetime(2024, 5, 31)),
        'Junho': (datetime(2024, 6, 1), datetime(2024, 6, 30)),
        'Julho': (datetime(2024, 7, 1), datetime(2024, 7, 31)),
        'Agosto': (datetime(2024, 8, 1), datetime(2024, 8, 31)),
        'Setembro': (datetime(2024, 9, 1), datetime(2024, 9, 30)),
        'Outubro': (datetime(2024, 10, 1), datetime(2024, 10, 31)),
        'Novembro': (datetime(2024, 11, 1), datetime(2024, 11, 30)),
        'Dezembro': (datetime(2024, 12, 1), datetime(2024, 12, 31)),
    }
    for season, (start, end) in seasons.items():
        if date>=start  and date<end:
            return season
    return season

def GuardarImages(category,data,cidade):
    dados = ['Temp Med','Humid Med','Radiacao','Variacao']
    csv_data = []

    for index, (season, values) in enumerate(data.groupby(level=category)):
        dir='graph/'+cidade+'/'+category+'/'+str(index+1).zfill(2)+'_'+season
        os.makedirs(dir, exist_ok=True)

        smoothed_values = {category: season}
        
        for index,dado in enumerate(dados):
            if dado=='Variacao':
                smoothed = smooth_curve(values['Temp Med'])
                smoothed = np.diff(smoothed)
            else:
                smoothed = smooth_curve(values[dado])
            plt.figure(figsize=(10, 6))
            plt.plot(smoothed, label=dado+' (suavizada)')
            plt.title(f"{dado} - {season} Dados", fontsize=14)
            x_ticks = np.arange(0, 1440, 60)
            x_labels = [f"{str(hour).zfill(2)}:00" for hour in [21,22,23,00,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]]
            plt.xticks(ticks=x_ticks, labels=x_labels, rotation=45)
            plt.xlabel("Hora")
            if index==0:
                plt.ylabel("\u00b0C", fontsize=12)
            elif index==1:
                plt.ylabel("%", fontsize=12)
            elif index==2:
                plt.ylabel("W", fontsize=12)
            elif index==3:
                plt.ylabel("\u00b0C/min", fontsize=12)
            plt.grid(True)
            plt.savefig(f"{dir}/{dado}_data_plot.png")
            plt.close()

            smoothed = np.where(np.isnan(smoothed), '', smoothed)
            smoothed_values[dado] = smoothed.tolist()
        csv_data.append(smoothed_values)
    df = pd.DataFrame(csv_data)
    os.makedirs(f"cidades_data/{cidade}", exist_ok=True)
    df.to_csv(f"cidades_data/{cidade}/{cidade}_{category}_data.csv", index=False, sep=';', decimal=',')

def Dados_Reais(cidades):
    data=pd.DataFrame()
    for i in cidades:
        # Carregar o CSV
        data = pd.read_csv('cidades/'+i, sep=';', decimal=',')

        # Conversão de colunas de data e hora para um único timestamp
        data['Timestamp'] = pd.to_datetime(data['Data'] + ' ' + data['Hora (UTC)'], format="%d/%m/%Y %H:%M")

        # Cálculo de Temperatura e Umidade Médias, radiacao em w, mes e estacao
        data['Temp Med'] = (data['Temp. Max. (C)'] + data['Temp. Min. (C)']) / 2
        data['Humid Med'] = (data['Umi. Max. (%)'] + data['Umi. Min. (%)']) / 2
        data['Radiacao'] = data['Radiacao1'] / 3.6
        data['Estacao'] = data['Timestamp'].apply(group_by_season)
        data['Mes'] = data['Timestamp'].apply(group_by_month)

        # Agrupa por estacao e mes
        seasonal_data = data.groupby([data['Estacao'],data['Timestamp'].dt.hour])[['Temp Med', 'Humid Med', 'Radiacao']].mean()
        monthly_data = data.groupby([data['Mes'],data['Timestamp'].dt.hour])[['Temp Med', 'Humid Med', 'Radiacao']].mean()

        GuardarImages('Estacao',seasonal_data,i[:-4])
        GuardarImages('Mes',monthly_data,i[:-4])
    return data

def Dados_Ideais():
    temp_peak = 25
    temp_valley = 19.75
    humid_peak = 70
    humid_valley = 60

    # Generate ideal temperature vector
    n_points = 1440
    time = np.arange(n_points) / n_points  # Normalized time

    # Temp Ideal: Valley at 600th point, Peak at 1200th point
    temp_ideal = temp_valley + (temp_peak - temp_valley) * (np.sin(2 * np.pi * (time - 600 / n_points - 0.1)) + 1) / 2

    # Humid Ideal: Peak at 540th point, Valley at 1100th point
    humid_ideal = humid_valley + (humid_peak - humid_valley) * (np.cos(2 * np.pi * (time - 540 / n_points)) + 1) / 2

    dados = ['Temp Med','Humid Med','Variacao']
    ideal=pd.DataFrame(columns=dados)
    ideal['Temp Med']=temp_ideal
    ideal['Humid Med']=humid_ideal

    smoothed_values = {'ideal': 'ideal'}
    os.makedirs('ideal', exist_ok=True)
    csv_data = []
    for index,dado in enumerate(dados):
        if dado=='Variacao':
            smoothed = smooth_curve(ideal['Temp Med'])
            smoothed = np.diff(smoothed)
        else:
            smoothed = ideal[dado]
        plt.figure(figsize=(10, 6))
        plt.plot(smoothed, label=dado+' (suavizada)')
        plt.title(f"{dado} - Ideal", fontsize=14)
        x_ticks = np.arange(0, 1440, 60)
        x_labels = [f"{str(hour).zfill(2)}:00" for hour in [21,22,23,00,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20]]
        plt.xticks(ticks=x_ticks, labels=x_labels, rotation=45)
        plt.xlabel("Hora")
        if index==0:
            plt.ylabel("\u00b0C", fontsize=12)
        elif index==1:
            plt.ylabel("%", fontsize=12)
        elif index==2:
            plt.ylabel("\u00b0C/min", fontsize=12)
        plt.grid(True)
        plt.savefig(f"ideal/{dado}_data_plot.png")
        plt.close()
        smoothed = np.where(np.isnan(smoothed), '', smoothed)
        smoothed_values[dado] = smoothed.tolist()
    csv_data.append(smoothed_values)
    df = pd.DataFrame(csv_data)
    df.to_csv(f"ideal/ideal_data.csv", index=False, sep=';', decimal=',')
    
#cidades = os.listdir('cidades')
#Dados_Reais(cidades)
#Dados_Ideais()
