import json
import requests
import xml.etree.ElementTree as ET
import psycopg2 as pg
import datetime
from tkinter import *
from tkinter.ttk import Combobox
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,NavigationToolbar2Tk)

# def fillArchive():
#     conn = connection()
#     cursor = conn.cursor()
#     urls = ["http://www.cbr.ru/scripts/XML_daily.asp?date_req=18/12/2023",
#             "http://www.cbr.ru/scripts/XML_daily.asp?date_req=17/12/2023",
#             "http://www.cbr.ru/scripts/XML_daily.asp?date_req=16/12/2023",
#             "http://www.cbr.ru/scripts/XML_daily.asp?date_req=15/12/2023"]
#     dates = ["2023-12-18", "2023-12-17", "2023-12-16", "2023-12-15"]
#     for i in range(len(urls)):
#         response = requests.get(urls[i])
#
#         xml_tree_root = ET.fromstring(response.text)
#
#         val_names = []
#         val_values = []
#         for valute in xml_tree_root.findall("Valute"):
#             val_names.append(valute.find("Name").text)
#             val_values.append(valute.find("Value").text)
#         l = list(json.loads(json.dumps(dict(zip(val_names, val_values)), ensure_ascii=False)).values())
#
#         archive_exec = f"Select id_val from Archive_exc_rate where date = '{dates[i]}'::DATE"
#         cursor.execute(archive_exec)
#         if not cursor.fetchone():
#             for j in range(len(l)):
#                 exec = f"INSERT INTO Archive_Exc_rate VALUES ({j + 1},'{l[j]}','{dates[i]}')"
#                 cursor.execute(exec)

def getValutes():
    url = "http://www.cbr.ru/scripts/XML_daily.asp?VAL_NM_RQ=R01235"

    response = requests.get(url)

    xml_tree_root = ET.fromstring(response.text)

    val_names = []
    val_values = []
    for valute in xml_tree_root.findall("Valute"):
        val_names.append(valute.find("Name").text)
        val_values.append(valute.find("Value").text)

    return json.dumps(dict(zip(val_names,val_values)), ensure_ascii=False)

def getRez(dict,combo,label,cur):
    global window
    if(combo.get() != ""):
        label.configure(text=dict[combo.get()])
        statistic(window, cur, combo.get())

def connection():
    try:
        conn = pg.connect(user="postgres",
                         password="postpass",
                         host="localhost",
                         port="5432")
        conn.autocommit = True
    except (Exception, pg.DatabaseError) as error:
        print("Ошибка при работе с БД", error)
        return
    print("Подключение к БД выполнено успешно")
    return conn

def fillTabValutes(cursor, l):
    check_exec = "SELECT count(id_val) FROM Valutes"
    cursor.execute(check_exec)
    if cursor.fetchone()[0] == 1:
        for i in range(len(l)):
            exec = f"INSERT INTO Valutes VALUES ({i+1},'{l[i]}')"
            cursor.execute(exec)
    else:
        print("Список валют не пустой")

def fillTabExcRate(cursor, l):
    check_exec = "Select date from Exchange_rate where id_val = 1"
    cursor.execute(check_exec)
    date = datetime.date.today()
    if not cursor.fetchone():
        for i in range(len(l)):
            exec = f"INSERT INTO Exchange_rate VALUES ({i+1},'{l[i]}','{date}')"
            cursor.execute(exec)
    else:
        print("Список курсов валют не пустой")

    archive_exec = f"Select id_val from Archive_exc_rate where date = '{date}'::DATE"
    cursor.execute(archive_exec)
    if not cursor.fetchone():
        for i in range(len(l)):
            exec = f"INSERT INTO Archive_Exc_rate VALUES ({i+1},'{l[i]}','{date}')"
            cursor.execute(exec)
    else:
        print("Список архива валют не пустой")

    del_exec = "DELETE FROM Exchange_rate"
    cursor.execute(del_exec)

def createGraphic(window,x0,y):
    x = [elem.strftime('%d.%m') for elem in x0]
    x.reverse()
    y.reverse()
    # print(y)
    fig = Figure(figsize=(6, 3),
                 dpi=100)

    plot1 = fig.add_subplot(111)
    plot1.plot(x,y)
    canv = FigureCanvasTkAgg(fig, master=window)
    canv.draw()
    canv.get_tk_widget().place(x=10, y=130)


def statistic(window, cursor, name):
    today = datetime.date.today()
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    find_id = f"Select id_val from Valutes where name = '{name}'"
    cursor.execute(find_id)
    id_val = cursor.fetchone()[0]
    #среднее
    avg_exec = f"Select avg(exc_rate::numeric::float8) from Archive_exc_rate where id_val = {id_val}"
    cursor.execute(avg_exec)
    avg_val = round(cursor.fetchone()[0],4)
    lbl = Label(window, text="Усредненное значение валюты за все время:")
    lbl.place(x=10, y=70)
    avg_lbl = Label(window, text=avg_val)
    avg_lbl.place(x=270, y=70)
    #процент роста
    rate_exec = f"Select exc_rate::numeric::float8 from Archive_exc_rate where id_val = {id_val} and date = '{today}'::DATE"
    cursor.execute(rate_exec)
    rate = cursor.fetchone()[0]
    prev_rate_exec = f"Select exc_rate::numeric::float8 from Archive_exc_rate where id_val = {id_val} and date = '{yesterday}'::DATE"
    cursor.execute(prev_rate_exec)
    prev_rate = cursor.fetchone()[0]
    percent = round(100 - prev_rate/rate*100,4)
    lbl2 = Label(window, text="Процент роста:")
    lbl2.place(x=10, y=100)
    percent_lbl = Label(window, text=f"{percent} %")
    percent_lbl.place(x=150, y=100)
    #график изменения
    graphic_exec = f"SELECT exc_rate::numeric::float8,date from Archive_exc_rate where id_val = {id_val}"
    cursor.execute(graphic_exec)
    val_data = cursor.fetchall()
    x=[]
    y=[]
    for i in range(len(val_data)):
        y.append(val_data[i][0])
        x.append(val_data[i][1])
    createGraphic(window,x,y)


    check_exec = f"Select id_val from Statistic where id_val = {id_val} and date = '{today}'::DATE"
    cursor.execute(check_exec)
    if not cursor.fetchone():
        insert_avg = "INSERT INTO Statistic VALUES (%s,%s,%s,%s)"
        cursor.execute(insert_avg,(id_val,avg_val,percent,today))



def start():
    global window
    response_dict = json.loads(getValutes())
    conn = connection()
    cur = conn.cursor()
    fillTabValutes(cur, list(response_dict.keys()))
    fillTabExcRate(cur, list(response_dict.values()))
    for i in window.place_slaves():
        i.destroy()

    #Показ курса валют
    lbl = Label(window, text="Выберите валюту:")
    lbl.place(x=10, y=10)
    valutesCombo = Combobox(window)
    valutesCombo['values'] = list(response_dict.keys())
    valutesCombo.place(x=120, y=10, width=180)
    lbl2 = Label(window, text="Курс:")
    lbl2.place(x=10, y=40)
    btn = Button(window, text="Получить", command= lambda : getRez(response_dict,valutesCombo, ratelabel,cur))
    btn.place(x=310, y=8)
    ratelabel = Label(window, text="")
    ratelabel.place(x=50, y=40)

    #Показ статистики




window = Tk()
if __name__ == "__main__":
    window.title("Курсы валют")
    window.geometry("640x480")
    lbl = Label(window, text="Получить данные о курсах валют")
    lbl.place(x=10, y=10)
    btn = Button(window, text="Получить", command=start)
    btn.place(x=220, y=8)
    # lbl = Label(window, text="Курс")
    # lbl.place(x=10, y=10)
    # valutesCombo = Combobox(window)
    # valutesCombo['values'] = list(response_dict.keys())
    # valutesCombo.place(x=45, y=10, width=180)
    # lbl2 = Label(window, text="к рублю")
    # lbl2.place(x=225, y=10)
    # btn = Button(window, text="Получить", command=getRez)
    # btn.place(x=280, y=10)
    #
    # rezlabel = Label(window, text="", font=("Comic Sans", 50))
    # rezlabel.place(x=45, y=40)

    window.mainloop()
