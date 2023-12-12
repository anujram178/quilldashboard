from flask import Flask, jsonify, request
import os
from supabase import create_client, Client
from flask_cors import CORS 
from datetime import datetime, timedelta
import psycopg2



url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
password: str = os.environ.get("SUPABASE_PASSWORD")
supabase: Client = create_client(url, key)

chartSqlQuery = """
WITH data as ({})
SELECT *
FROM data
WHERE "{}" >= %s AND "{}" <= %s
"""

# Replace [YOUR-PASSWORD] with your actual Supabase password
connection_info = {
    'user': 'postgres',
    'password': '?qkz$KGby3JmP8$',
    'host': 'db.jlsrybflmjghqyyoinak.supabase.co',
    'port': '5432',
    'database': 'postgres'
}

app = Flask(__name__)
CORS(app)

def getSupabaseConnection():
    conn = psycopg2.connect(**connection_info)
    cursor = conn.cursor()
    return cursor

@app.route('/dashboard/<name>', methods = ['GET'])
def dashboard(name):
    cursor = getSupabaseConnection()
    sqlQuery = 'SELECT * FROM "Dashboards" WHERE name = %s;'
    cursor.execute(sqlQuery, (name, ))
    rows = cursor.fetchall()

    dashboardMetadata = []

    for row in rows:
        dashboardMap = {"id": row[0], "name": row[1], "initialDateRange": row[2], "chartsList": row[3]}
        dashboardMetadata.append(dashboardMap)

    return jsonify(dashboardMetadata)

@app.route('/chart/<id>', methods = ['GET'])
def chart(id):
    # get query params
    dateRange = request.args.get('dateRange')  # Example: ?dateRange=LAST_90_DAYS
    prevDateRange = request.args.get('prevDateRange')  # Example: ?prevDateRange=PREVIOUS_30_DAYS
    startDate = request.args.get('startDate') 
    endDate = request.args.get('endDate') 
    isFromDatePicker = request.args.get('isFromDatePicker')

    # get dates for filtering the data in sql query
    dates = getDatesForFiltering(dateRange, prevDateRange, startDate, endDate, isFromDatePicker)
    startDate, endDate = dates["startDate"], dates["endDate"]
    startDatePrev, endDatePrev = dates["startDatePrev"], dates["endDatePrev"]
    bucketSize = dates["bucketSize"]

    # set up db connection and queries
    cursor = getSupabaseConnection()
    sqlQuery = 'SELECT * FROM "Charts" WHERE id = %s;'
    cursor.execute(sqlQuery, (id, ))
    rows = cursor.fetchall()

    chartInfo = []

    for row in rows:
        chartData = []
        chartDataPrev = []
        
        chartDataMap = {
            "id": row[0],
            "dashboard": row[1],
            "chartName": row[2],
            "chartType": row[3],
            "sqlQuery": row[4],
            "xAxisField": row[5],
            "yAxisField": row[6],
            "dateFilterTable": row[7],
            "dateFilterField": row[8]
        }

        sqlQuery = chartDataMap["sqlQuery"]
        dateFilterTable = chartDataMap["dateFilterTable"]
        dateFilterField = chartDataMap["dateFilterField"]
        yAxisField = chartDataMap["yAxisField"]

        cursor.execute(chartSqlQuery.format(sqlQuery, dateFilterField, dateFilterField), (startDate, endDate))
        chartRows = cursor.fetchall()

        column_names = [desc[0] for desc in cursor.description]  # Get column names
        for chartRow in chartRows:
            chartData.append(dict(zip(column_names, chartRow)))

        cursor.execute(chartSqlQuery.format(sqlQuery, dateFilterField, dateFilterField), (startDatePrev, endDatePrev))
        chartRowsPrev = cursor.fetchall()

        for chartRow in chartRowsPrev:
            chartDataPrev.append(dict(zip(column_names, chartRow)))
        
        chartData = bucketizeData(chartData, bucketSize, endDate, dateFilterField, yAxisField)
        chartDataPrev = bucketizeData(chartDataPrev, bucketSize, endDatePrev, dateFilterField, yAxisField)
        mergeBucketData(chartData, chartDataPrev, yAxisField)


        chartDataMap["data"] =  chartData
        chartInfo.append(chartDataMap)

    return jsonify(chartInfo)

@app.route('/charts/<dashboardName>', methods = ['GET'])
def charts(dashboardName):
    dateRange = request.args.get('dateRange')  # Example: ?dateRange=LAST_90_DAYS
    prevDateRange = request.args.get('prevDateRange')  # Example: ?prevDateRange=PREVIOUS_30_DAYS
    startDate = request.args.get('startDate') 
    endDate = request.args.get('endDate') 
    isFromDatePicker = request.args.get('isFromDatePicker')

    # get dates for filtering the data in sql query
    dates = getDatesForFiltering(dateRange, prevDateRange, startDate, endDate, isFromDatePicker)
    startDate, endDate = dates["startDate"], dates["endDate"]
    startDatePrev, endDatePrev = dates["startDatePrev"], dates["endDatePrev"]
    bucketSize = dates["bucketSize"]

    response = supabase.table('Charts').select('*').eq('dashboard', dashboardName).execute()
    chartInfoList = []
    bucketData = []

    # set up db connection and queries
    cursor = getSupabaseConnection()

    for chartInfo in dict(response)['data']:
        chartData = []
        chartDataPrev = []

        id = chartInfo["id"]
        chartType = chartInfo["chartType"]
        sqlQuery = chartInfo["sqlQuery"]
        xAxisField = chartInfo["xAxisField"]
        yAxisField = chartInfo["yAxisField"]
        chartName = chartInfo["name"]
        table = chartInfo["dateFilterTable"]
        dateFilterField = chartInfo["dateFilterField"]

        cursor.execute(chartSqlQuery.format(sqlQuery, dateFilterField, dateFilterField), (startDate, endDate))
        chartRows = cursor.fetchall()

        column_names = [desc[0] for desc in cursor.description]  # Get column names
        for chartRow in chartRows:
            chartData.append(dict(zip(column_names, chartRow)))

        cursor.execute(chartSqlQuery.format(sqlQuery, dateFilterField, dateFilterField), (startDatePrev, endDatePrev))
        chartRowsPrev = cursor.fetchall()

        for chartRow in chartRowsPrev:
            chartDataPrev.append(dict(zip(column_names, chartRow)))
        
        chartData = bucketizeData(chartData, bucketSize, endDate, dateFilterField, yAxisField)
        chartDataPrev = bucketizeData(chartDataPrev, bucketSize, endDatePrev, dateFilterField, yAxisField)
        mergeBucketData(chartData, chartDataPrev, yAxisField)
    
        chartInfoList.append({"chartName": chartName, "xAxisField": xAxisField, "yAxisField": yAxisField, "id": id, "chartType": chartType, "data": chartData})


    return jsonify(chartInfoList)


def convertDatetimeToDateString(datetime):
    return str(datetime).split(" ")[0]

def convertDateStringToDatetime(datestring):
    return datetime.strptime(datestring, '%Y-%m-%d')

def bucketizeData(data, bucketSize, endDate, dateFilterField, yAxisField):
    newBucketedData = []
    buckets = {}

    # Iterate through data and bucket the points
    for dataPoint in data:
        dateToCheck = dataPoint[dateFilterField]
        if type(dateToCheck) == str:
            dateToCheck = datetime.strptime(dataPoint[dateFilterField], '%Y-%m-%d')  # Convert string to datetime
        
        bucket_start = dateToCheck - timedelta(days=dateToCheck.day)
        if bucketSize == 7:
            bucket_start = dateToCheck - timedelta(days=dateToCheck.weekday())  # Align to the start of the week
        
        if bucket_start not in buckets:
            buckets[bucket_start] = {'count': 1, yAxisField: dataPoint[yAxisField]}
        else:
            buckets[bucket_start]['count'] += 1
            buckets[bucket_start][yAxisField] += dataPoint[yAxisField]

    # Convert buckets dictionary back to a list
    for key, value in buckets.items():
        bucket_data = {dateFilterField: key.strftime('%Y-%m-%d'), yAxisField: value[yAxisField], 'count': value['count']}
        newBucketedData.append(bucket_data)

    return sorted(newBucketedData, key= lambda x: x["Date"])

def mergeBucketData(bucketData, bucketDataPrev, yAxisField):
    # bucketData and bucketDataPrev will both be sorted
    # so go through bucketData and put the bucketDataPrev value inside bucketData

    # start with the last item in bucketData
    curIndex = -1
    prevLength = len(bucketDataPrev)

    for i in range(len(bucketData)):
        if -curIndex <= prevLength:
            bucketData[curIndex][yAxisField + "Prev"] = bucketDataPrev[curIndex][yAxisField]
        else:
            break
        curIndex -= 1
    
    return bucketData

def getDatesForFiltering(dateRange, prevDateRange, startDate, endDate, isFromDatePicker):
    # create datetime object from scratch since user did not provide a custom date range
    if startDate == 'null' or endDate == 'null' or not(startDate and endDate) or isFromDatePicker == "false":
        endDate = datetime.now()
        startDate = None

        if dateRange == "LAST_90_DAYS":
            startDate = endDatePrev = endDate - timedelta(90)

        elif dateRange == "LAST_30_DAYS":
            startDate = endDatePrev = endDate - timedelta(30)

        else:
            startDate = endDatePrev = endDate.replace(day=1)
        
    
    # user provided date range is a string
    # so convert it to a datetime object for future logic
    else:
        startDate = convertDateStringToDatetime(startDate)
        endDate = convertDateStringToDatetime(endDate)

    
    endDatePrev = startDate

    if prevDateRange == "PREVIOUS_90_DAYS":
        startDatePrev = endDatePrev - timedelta(90)

    elif prevDateRange == "PREVIOUS_30_DAYS":
        startDatePrev = endDatePrev - timedelta(30)

    else:
        startDatePrev = endDatePrev.replace(day=1) 

    bucketSize = getBucketSize(startDate, endDate)

    # convert datetime objects to strings ,ie, from datetime obj -> "2023-11-26"
    # because we send a supabase query which uses only date strings
    startDate, endDate = convertDatetimeToDateString(startDate), convertDatetimeToDateString(endDate)
    startDatePrev, endDatePrev = convertDatetimeToDateString(startDatePrev), convertDatetimeToDateString(endDatePrev)

    return {"startDate": startDate, "endDate": endDate, "startDatePrev": startDatePrev, "endDatePrev": endDatePrev, "bucketSize": bucketSize}


def getBucketSize(startDate, endDate):
    if endDate - startDate <= timedelta(30):
        return 7
    return 30
    







if __name__ == '__main__':

    app.run(debug=True, port=8080)
