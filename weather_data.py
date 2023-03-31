import os, json, urllib3, requests

urllib3.disable_warnings()

import datetime
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib import colors
from collections import defaultdict

DEFAULT_NUMBER_OF_POINTS = 10

class InputData():
    def __init__(self, date, points, parameters, count=DEFAULT_NUMBER_OF_POINTS):
        # Координаты начальной точки
        self.startDate = date[0]
        self.endDate = date[1]
        # Координаты конечной точки
        self.points = points
        # Извлекаемые параметры
        self.parameters = parameters
        # Кол-во точек
        self.count = count

def ConfiguratePath(startPoint, endPoint, count=DEFAULT_NUMBER_OF_POINTS):
    outputPath = []

    x1 = startPoint[1]
    y1 = startPoint[0]
    x2 = endPoint[1]
    y2 = endPoint[0]

    # Нахождение единичного вектора: unit_vec = ( (x2-x1)/len, (y2-y1)/len ) * len/count, len-длина
    unit_vec = [ (x2-x1)/(count-1), (y2-y1)/(count-1) ]

    for num in range(0, count):
        # Добавляемые значения округляем до сотых
        outputPath.append( ( round(startPoint[1] + num*unit_vec[0], 2), round(startPoint[0] + num*unit_vec[1], 2)) )
    print("coords=", outputPath)
    
    return outputPath
    

def Date2NasaFormat(date):
    
    # day.month.year(str) --> yearMonthDay(int)
    startDateList = date[0].split(".")
    startDateList.reverse()
    startDate = "".join(startDateList)

    endDateList = date[1].split(".")
    endDateList.reverse()
    endDate = "".join(endDateList)
    return startDate, endDate
    
def Downloading(inputData):

    startDate = inputData.startDate
    endDate = inputData.endDate
    #longitude = inputData.startPoint
    #latitude = inputData.endPoint
    parameters = inputData.parameters

    outputData = {}

    print(inputData.points)

    for longitude, latitude in inputData.points:
        print(longitude)
        # query_url = r"https://power.larc.nasa.gov/cgi-bin/v1/DataAccess.py?request=execute&identifier=SinglePoint&tempAverage=DAILY&parameters={parameters}&startDate={startDate}&endDate={endDate}&lat={latitude}&lon={longitude}&outputList=JSON&userCommunity=SSE"     
        query_url = r"https://power.larc.nasa.gov/api/temporal/daily/point?parameters={parameters}&community=RE&longitude={longitude}&latitude={latitude}&start={startDate}&end={endDate}&format=JSON"     
        query_url = query_url.format(longitude=longitude, latitude=latitude, startDate=startDate, endDate=endDate, parameters=parameters)
        main_response = requests.get(url=query_url, verify=False)
        json_response = json.loads(main_response.text)
        return json_response


    

# Возвращает массив суммы значений одного из параметров по каждой точке
def GetSumFromPoints(data, parameter):

    outputSum = defaultdict(list)

    for point in data:
        if point != "date":
            tmp_sum = 0
            last_value = 0
            for value in data[point][parameter]:
                if value < 0:
                    value = last_value
                tmp_sum += value
                last_value = value

            outputSum[parameter].append(tmp_sum)

    return outputSum

# Возвращает массив средних значений одного из параметров по каждой точке
def GetMeanFromPoints(data, parameter):
    #outputSum = []
    #outputSum = {}
    outputSum = defaultdict(list)

    for point in data:
        if point != "date":
            count = 0
            tmp_sum = 0
            last_value = 0
            for value in data[point][parameter]:
                if value < 0:
                    value = last_value
                tmp_sum += value
                last_value = value
                count += 1

            outputSum[parameter].append(tmp_sum/count)

    return outputSum

def DrawPlotFromData(data, point, parameters):
    point = str(float(point[0])) + "," + str(float(point[1]))
    if point != "date":
        fig, ax = plt.subplots()
        ax.set_title("Point: " + str(point.split(',')[1]) + ", " + str(point.split(',')[0]))

        for param in data[point]:
            if parameters.find(param) >= 0:
                ax.plot(data["date"], data[point][param], label = str(param))
        
        ax.legend(loc = 'right')
            
    return fig

def DrawMarginalDensity(data, point, parameters):

    point = str(float(point[0])) + "," + str(float(point[1]))
    
    fig = plt.figure()

    x = data[point][parameters.split(',')[0]]
    y = data[point][parameters.split(',')[1]]

    #ax.scatter(x, y, marker='.')
    #sns.kdeplot(x=x,y=y,cmap="Reds", shade=True, bw_adjust=.5)
    g = sns.jointplot(x=x, y=y, color=colors.to_rgba((1,1,1,1)))
    g.plot_joint(sns.kdeplot, cmap="Reds", shade=True, bw_adjust=.5)
    g.set_axis_labels("GHI, kW-hr/m^2/day", "WS10M, m/s")

    
    plt.suptitle("Point: " + str(point.split(',')[1]) + ", " + str(point.split(',')[0]), y=1)

    return fig

def DrawMarginalHistogram(data, point, parameters):

    point = str(float(point[0])) + "," + str(float(point[1]))
    print(point)
    fig = plt.figure()

    x = data[point][parameters.split(',')[0]]
    y = data[point][parameters.split(',')[1]]
    
    for i in range(0, len(x)):
        if x[i] < 0:
            if x[i-1] < 0:
                x[i] = None
            else:
                x[i] = x[i-1]
    for i in range(0, len(y)):
        if y[i] < 0:
            if y[i-1] < 0:
                y[i] = 1
            else:
                y[i] = y[i-1]
    gs = GridSpec(4,4)

    ax = fig.add_subplot(gs[1:4,0:3])
    ax_x = fig.add_subplot(gs[0,0:3])
    ax_y = fig.add_subplot(gs[1:4,3])

    ax.scatter(x, y, marker='.')
    ax_x.hist(x, bins='auto', rwidth=0.9)
    ax_y.hist(y, orientation="horizontal", rwidth=0.9)

    # Turn off tick labels on marginals
    plt.setp(ax_x.get_xticklabels(), visible=False)
    plt.setp(ax_y.get_yticklabels(), visible=False)

    # Set labels on joint
    ax.set_xlabel("DHI, kW-hr/m^2/day")
    ax.set_ylabel("GHI, kW-hr/m^2/day")
    # ax.set_xlabel(parameters.split(',')[0])
    # ax.set_ylabel(parameters.split(',')[1])

    # Set labels on marginals
    ax_y.set_xlabel('days')
    ax_x.set_ylabel('days')

    ax_x.set_title("Point: " + str(point.split(',')[1]) + ", " + str(point.split(',')[0]))

    return fig

def DrawPointPlot(*arrays):
    fig = plt.figure()
    plot_num = len(arrays)*100 + 10 + 1 # Расположение графика

    for arr in arrays:
        fig = plt.subplot(plot_num)
        y = []
        for k,v in arr.items():
            x = [np.linspace(1, len(arr[k]), len(arr[k]))]
            y.append(v)
            fig.set_ylabel(k)

        fig.plot(x, y, 'bo')

        plot_num += 1
    return fig

def DrawLollipopPlot(*arrays):
    fig = plt.figure()
    plot_num = len(arrays)*100 + 10 + 1 # Расположение графика

    for arr in arrays:
        fig = plt.subplot(plot_num)
        y = []
        
        for k,v in arr.items():
            x = np.linspace(1, len(arr[k]), len(arr[k]))
            y = v
            if k == "ALLSKY_KT":
                fig.set_ylabel("DHI, kW-hr/m^2 / 3 years")
            if k == "ALLSKY_SFC_SW_DWN":
                fig.set_ylabel("GHI, kW-hr/m^2 / 3 years")
            if k == "WS10M":
                fig.set_ylabel("WS10M, m/s")
            fig.set_ylim(min(y), max(y) + (max(y) - min(y))*0.25)


        # annotate
        for idx, val in enumerate(y):
            fig.text(idx + 1, val + (max(y)-min(y))*0.03, str(round(val, 2)), horizontalalignment='center', verticalalignment='bottom', fontsize=10)

        # draw    
        fig.stem(x, y, use_line_collection=True)

        plot_num += 1
    return fig



#Вывод данных в файл
def save_csv(points, start_date, end_date):
    for point in points:
        with open(os.path.join(folder_path, f"{point}.txt"), 'w') as file:
            json.dump(json_data,file, indent=4)

            # создаем пустой DataFrame
            df = pd.DataFrame(columns=['date', 'QV2M', 'T2M', 'WS10M', 'ALLSKY_KT', 'ALLSKY_SFC_SW_DWN'])

            # создаем пустой DataFrame
            for date in json_data['properties']['parameter']['QV2M']:
                # проверяем, что дата входит в заданный временной диапазон
                if start_date <= date <= end_date:
                    # преобразуем строку даты в формат datetime и добавляем разделители
                    date_formatted = datetime.datetime.strptime(date, '%Y%m%d').strftime('%Y.%m.%d')
                    qv2m = json_data['properties']['parameter']['QV2M'][date]
                    t2m = json_data['properties']['parameter']['T2M'][date]
                    ws10m = json_data['properties']['parameter']['WS10M'][date]
                    allsky_kt = json_data['properties']['parameter']['ALLSKY_KT'][date]
                    allsky_sfc_sw_dwn = json_data['properties']['parameter']['ALLSKY_SFC_SW_DWN'][date]
                    df = df.append({'date': date_formatted, 'QV2M': qv2m, 'T2M': t2m, 'WS10M': ws10m, 'ALLSKY_KT': allsky_kt, 'ALLSKY_SFC_SW_DWN': allsky_sfc_sw_dwn}, ignore_index=True)


            # сохраняем DataFrame в CSV файл
            df.to_csv(f'{point}.csv', index=False)


# используй функцию криэйт тейбл для создания таблицы через какую-нибудь библиотеку 

if __name__ == '__main__':

    # Координаты отрезка
    startPoint = (50.551, 55.719)
    #startPoint = (55.719, 50.551)
    endPoint = (42.357, 54.196)
    #endPoint = (54.196, 42.357)
    
    folder_path = os.path.dirname(os.path.abspath(__file__))
    # Конфигурация массива заданного кол-ва точек от стартовой до конечной
    points = ConfiguratePath(startPoint, endPoint)

    # Установка и форматирование даты
    date = ["01.01.2018", "31.12.2020"]
    date = Date2NasaFormat(date)
    outputPath = ConfiguratePath(startPoint, endPoint, count=DEFAULT_NUMBER_OF_POINTS)

    # Все параметры, которые необходимо скачать
    # QV2M  - Specific Humidity at 2 Meters - The ratio of the mass of water vapor to the total mass of air at 2 meters (g water/kg total air).
    # T2M   - Temperature at 2 Meters       - The average air (dry bulb) temperature at 2 meters above the surface of the earth
    # WS10M - Wind Speed at 10 Meters       - The average of wind speed at 10 meters above the surface of the earth
    # ALLSKY_KT - All Sky Insolation Clearness Index - A fraction representing clearness of the atmosphere; the all sky insolation that is transmitted through the atmosphere to strike the surface of the earth divided by the average of top of the atmosphere total solar irradiance incident.
    # ALLSKY_SFC_SW_DWN - All Sky Surface Shortwave Downward Irradiance - The total solar irradiance incident (direct plus diffuse) on a horizontal plane at the surface of the earth under all sky conditions. An alternative term for the total solar irradiance is the "Global Horizontal Irradiance" or GHI.

    parameters = "QV2M,T2M,WS10M,ALLSKY_KT,ALLSKY_SFC_SW_DWN"
    # parameters = "QV2M,T2M,WS10M,ALLSKY_SFC_SW_DWN"

    # Входные данные - дата, координаты, извлекаемые параметры
    inputData = InputData(date, points, parameters)
    print("startDate:", inputData.startDate, "endDate: ", inputData.endDate)
    print("startPoint:", inputData.points[0], "endPoint: ", inputData.points[-1])
    
 
    # Входные данные - дата, координаты, извлекаемые параметры
    inputData = InputData(date, points, parameters)
    print("startDate:", inputData.startDate, "endDate: ", inputData.endDate)
    print("startPoint:", inputData.points[0], "endPoint: ", inputData.points[-1])

    # Выходные данные - 
    json_data = Downloading(inputData)
    json_tables = save_csv(points,date[0], date[1])