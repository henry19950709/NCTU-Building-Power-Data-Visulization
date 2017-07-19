# coding=UTF-8
# -*- coding: utf8 -*-

from EC import DataRobot
from lxml import html,etree
import time,datetime
from bokeh.plotting import figure, output_file, show,save
from bokeh.layouts import gridplot,column,row
from bokeh.models import FixedTicker,LinearAxis, Range1d
from bokeh.charts import Donut, show,Bar
from collections import OrderedDict
import pandas as pd
from pandas import DataFrame as df
import numpy as np
import ftplib
import os
import io
import sys
import requests
from bs4 import BeautifulSoup

reload(sys)
sys.setdefaultencoding("utf-8")


def update(filename):
	#----------FTP connection
	server = 'jupiter.math.nctu.edu.tw'   #here to be changed
	username = 'siteconf'
	password = 'SiteConf!@#4'
	ftp_connection = ftplib.FTP(server, username, password)
	ftp_connection.cwd('/WWW/Civil_Engineer/data')
	file = open(filename, "rb") 
	ftp_connection.storbinary('STOR ' + filename, file) 
	ftp_connection.quit()
	print ('Upload Successfully')

def stage_number():
	hour = int((time.strftime("%H", time.localtime())))
	return hour + 1

def get_month():
	d = datetime.date.today()
	return d.month

def set_figure_format(p):
	p.xaxis.axis_label_text_font_size = '20pt'
	p.xaxis.axis_label = get_flag_days_ago(0)+"整點時間"
	p.xaxis.axis_line_color = "orange"
	p.yaxis.axis_label = "電力(度)"
	p.yaxis.major_label_text_color = "orange"
	p.yaxis.axis_label_text_color = 'orange'
	p.yaxis.axis_label_text_font_size = '20pt'
	p.xaxis[0].ticker=FixedTicker(ticks=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24])
	#p.set(x_range=Range1d(left, right))

def get_flag_days_ago(flag):
	localtime = time.localtime(time.time()-86400*flag)
	year=str(localtime.tm_year)
	month=str(localtime.tm_mon)
	day=str(localtime.tm_mday)	
	#return '2016-12-02'
	return year+'-'+month+'-'+day

def get_today_date():
	localtime = time.localtime(time.time())
	month=str(localtime.tm_mon)
	day=str(localtime.tm_mday)
	if len(month) == 1:
		month = '0' + month
	if len(day) == 1:
		day = '0' + day
	return month+'/'+day

def get_temp_humidity():
	global data
	res = requests.get("http://www.cwb.gov.tw/V7/observe/24real/Data/46757.htm?_=1489544884136")
	res = res.text.encode('utf-8')
	weather = res.split('</tr>\n<tr>')[1:]
	today_date = get_today_date()
	for i in range(0,len(weather)):
		d = weather[i]
		tree = html.fromstring(d)		
		weather_time = tree.xpath('//th/text()')[0]
		if weather_time[:5] == today_date:  #today's date is the same as the data from web
			if weather_time[-2:] == '00':   #XX:00 ex:10:00
				hour = int(weather_time[6:8])
				data[hour] = {}
				if tree.xpath('//td[@class="temp1"]/text()')[0]!='-':
					temp = float(tree.xpath('//td[@class="temp1"]/text()')[0])
					humidity = int(tree.xpath('//td[@style="text-align:center"]/text()')[7])
					data[hour]['temp'] = temp
					data[hour]['humidity'] = humidity
				else:
					data[hour]['temp'] = 0
					data[hour]['humidity'] = 0

def draw_temp_humidity(data,num):
	global plot
	hour_list = []
	temp_list = []
	humidity_list = []
	i = 0
	while i < len(data):
		hour_list.append(i)
		temp_list.append(data[i]['temp'])
		humidity_list.append(data[i]['humidity'])
		i += 1

	p = figure(width=1100,height=700,title='工程'+num+'館 溫濕度',y_range = (0,40))
	p.title.text_font_size = "20pt"
	
	p.xaxis[0].ticker=FixedTicker(ticks=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24])
	p.yaxis.axis_label_text_color = 'red'
	p.yaxis.major_label_text_color = "red"
	p.yaxis.major_label_orientation = 'horizontal'
	p.yaxis.axis_label_text_font_size = '20pt'
	p.yaxis.axis_line_color = 'red'
	p.xaxis.axis_label = get_flag_days_ago(0)+'整點時間'
	p.xaxis.axis_label_text_font_size = '20pt'

	p.yaxis.axis_label = '溫度(攝氏)'

	p.circle(hour_list,temp_list,size=10,color = 'red',legend="Temperature")
	p.line(hour_list,temp_list,legend="Temperature", color = 'red')
	
	p.extra_y_ranges = {"foo": Range1d(start=0, end=100)}
	p.circle(hour_list, humidity_list, color="blue", y_range_name="foo",legend="Humidity",size = 10)
	p.line(hour_list,humidity_list,y_range_name="foo",legend="Humidity", color = 'blue')
	p.add_layout(LinearAxis(y_range_name="foo",axis_label="濕度(%)",major_label_text_color = 'blue',axis_label_text_color = 'blue',axis_label_text_font_size = '20pt'), 'right')

	p.logo = None
	p.toolbar_location = None
	p.legend.location = "bottom_left"
	plot.append(p)
	#show(p)


def draw_EC_power(num,index):
	global robot,plot
	d=robot.message.split('</tr><tr>')
	stage = stage_number()
	while(len(robot.message.split('</tr><tr>'))==stage):
		time.sleep(10)
		robot.query(1,index)
		print 'zzz'
	hour_counter = 0
	for j in range(1,stage+1):
		d=robot.message.split('</tr><tr>')[j].encode('utf-8')
		if not d:
			break			
		tree = html.fromstring(d.replace("微軟正黑體","fuck"))		
		d = tree.xpath('//font[@face="fuck"]/text()')
		power = d[5] 
		dict['power'].append(power)
		dict['time'].append(j-1)
	
	p = figure(width=1100,height=700,title='工程'+num+'館 電力')
	p.title.text_font_size = "20pt"

	p.circle(dict['time'],dict['power'],size=10,legend="Power",color = 'orange')
	p.line(dict['time'],dict['power'],legend="Power",color = 'orange')
	set_figure_format(p)
	p.legend.location = "bottom_left"
	plot.append(p)
	
		
def impute_value(data,flag):  #donut
	a=[]
	for k in range(0,len(data)):
		if flag[k] == False:
			a.append(data[k])
	return np.array(a).mean()

def impute(data,limit):   #Donut
	flag = []
	for i in range(0,len(data)):
		if i != len(data)-1:
			if data[i]/5.0 > data[i+1]:
				flag.append(True)
			else:
				flag.append(False)
	i = len(data)-1
	while(1):
		if flag[i-1]==False:
			if data[i]/5.0 > data[i-1]:
				flag.append(True)
			else:
				flag.append(False)
			break
		else:
			i -= 1
	
	total = 0
	for i in range(0,len(flag)):
		if flag[i] == True:
			data[i] = impute_value(data,flag)
		total += data[i]
	data.append(limit-total)
	return data
	


def draw_EC_donut(num,index):
	robot2 = DataRobot()
	robot2.start_time = '2017-01-01'
	robot2.current_time = get_flag_days_ago(0)
	robot2.query(3,index)
	ec_month_power = []
	for j in range(1,get_month()+1):
		d=robot2.message.split('</tr><tr>')[j].encode('utf-8')
		if not d:
			break			
		tree = html.fromstring(d.replace("微軟正黑體","fuck"))		
		d = tree.xpath('//font[@face="fuck"]/text()')
		power = d[5] 
		ec_month_power.append(float(power))
	limit_array = [0,250000,400000,2000000,3800000,3000000,2300000]
	ec_month_power = impute(ec_month_power,limit_array[index])
	

	quarter_array = []
	quarter = 0
	for i in range(0,get_month()):
		if i % 3 ==0:
			quarter += 1
			quarter_array.append(0)
		quarter_array[quarter-1]+=ec_month_power[i]
	quarter_array.append(ec_month_power[-1])

	index_array = []
	for i in range(0,quarter):
		index_array.append('Q'+str(i+1)+'\n'+str(quarter_array[i])+'度')
	index_array.append('Remain:\n'+str(quarter_array[-1])+'度')
	data = pd.Series(quarter_array, index = index_array)
	pie_chart = Donut(data,plot_width=200, plot_height=200,text_font_size='15pt',title='工程'+num+'館 年用量限額'+str(limit_array[index])+'度',color=["red","orange","yellow","green"])
	pie_chart.title.text_font_size = "20pt"
	plot.append(pie_chart)

def bar_transform(data):
	flag = []
	for i in range(0,len(data)):
		if i != len(data)-1:
			if data[i]/5.0 > data[i+1]:
				flag.append(True)
			else:
				flag.append(False)
	i = len(data)-1
	while(1):
		if flag[i-1]==False:
			if data[i]/5.0 > data[i-1]:
				flag.append(True)
			else:
				flag.append(False)
			break
		else:
			i -= 1
		
	for i in range(0,len(flag)):
		if flag[i] == True:
			data[i] = impute_value(data,flag)

	quarter_array = []
	quarter = 0
	for i in range(0,get_month()):
		if i % 3 ==0:
			quarter += 1
			quarter_array.append(0)
		quarter_array[quarter-1]+=data[i]
	return quarter_array
	

def draw_total_power():
	global plot
	robot3 = DataRobot()
	robot3.start_time = '2017-01-01'
	robot3.current_time = get_flag_days_ago(0)
	bar_dict = {}
	for i in range(1,7):
		bar_dict[i]=[]
		robot3.query(3,i)
		for j in range(1,get_month()+1):
			d=robot3.message.split('</tr><tr>')[j].encode('utf-8')
			if not d:
				break			
			tree = html.fromstring(d.replace("微軟正黑體","fuck"))		
			d = tree.xpath('//font[@face="fuck"]/text()')
			power = d[5] 
			bar_dict[i].append(float(power))
		bar_dict[i] = bar_transform(bar_dict[i])
	print bar_dict
	stack = []
	power = []
	building = []

	for i in range(1,7):
		for k in range(0,len(bar_dict[i])):
			power.append(bar_dict[i][k])
			if i == 1:
				b='工程一館'
			elif i == 2:
				b='工程二館'
			elif i == 3:
				b='工程三館'
			elif i == 4:
				b='工程四館'
			elif i == 5:
				b='工程五館'
			else:
				b='工程六館'
			building.append(b)
		for j in range(1,get_month()/3+2): #quarter#	
			stack.append('Q'+str(j))
	bar_df = OrderedDict()
	bar_df = {
		'stack':stack,
		'building':building,
		'power':power
	}
	
	bar_chart = Bar(bar_df, values='power', label='building', stack='stack',ylabel="電量(度)",xlabel='建築物', 
          title="交大工程館年度用電量", legend='top_left',color=["red","orange","yellow","green"])
	bar_chart.title.text_font_size = "20pt"
	bar_chart.yaxis.axis_label_text_font_size = '20pt'
	bar_chart.xaxis.axis_label_text_font_size = '20pt'
	
	plot.append(bar_chart)

#-------init and get current time-----------

word = [0,'一','二','三','四','五','六',]

#-------Main------
for j in range(1,7):
	robot=DataRobot()
	robot.current_time=get_flag_days_ago(0)
	robot.start_time = robot.current_time
	robot.query(1,j)
	dict={}
	dict['power']=[]
	dict['time']=[]
	data = {}
	plot=[]
	output_file('E'+str(j)+'.html',title='工程'+str(j)+'館')
	get_temp_humidity()
	draw_temp_humidity(data,word[j])
	draw_EC_donut(word[j],j)
	draw_EC_power(word[j],j)
	draw_total_power()
	grid = gridplot(plot, ncols=2, plot_width=700, plot_height=700)
	save(grid)
	update('E'+str(j)+'.html')


