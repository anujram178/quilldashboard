from flask import Flask, jsonify, request
import os
from supabase import create_client, Client
from flask_cors import CORS 
from datetime import datetime, timedelta



url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

app = Flask(__name__)
CORS(app)

@app.route('/dashboard/<name>', methods = ['GET'])
def dashboard(name):
    response = supabase.table('Dashboards').select('*').eq('name', name).execute()
    return jsonify(dict(response)['data'])

@app.route('/chart/<id>', methods = ['GET'])
def chart(id):
    response = supabase.table('Charts').select('*').eq('id', id).execute()
    return jsonify(dict(response)['data'])

@app.route('/charts/<dashboardName>', methods = ['GET'])
def charts(dashboardName):
    dateRange = request.args.get('dateRange')  # Example: ?dateRange=LAST_90_DAYS
    endDate = datetime.now()
    startDate = None

    if dateRange == "LAST_90_DAYS":
        startDate = endDatePrev = endDate - timedelta(90)
        startDatePrev = endDatePrev - timedelta(90)

    elif dateRange == "LAST_30_DAYS":
        startDate = endDatePrev = endDate - timedelta(30)
        startDatePrev = endDatePrev - timedelta(30)

    else:
        startDate = endDatePrev = endDate.replace(day=1)
        startDatePrev = endDatePrev.replace(day=1) 


    # convert datetime objects to strings - from datetime obj -> "2023-11-26"
    # because we send a supabase query which uses only date strings
    startDate, endDate = convertDatetimeToDate(startDate), convertDatetimeToDate(endDate)
    startDatePrev, endDatePrev = convertDatetimeToDate(startDatePrev), convertDatetimeToDate(endDatePrev)

    response = supabase.table('Charts').select('*').eq('dashboard', dashboardName).execute()
    chartInfoList = []
    bucketData = []
    for chartData in dict(response)['data']:
        id = chartData["id"]
        chartType = chartData["chartType"]
        sqlQuery = chartData["sqlQuery"]
        xAxisField = chartData["xAxisField"]
        yAxisField = chartData["yAxisField"]
        chartName = chartData["name"]

        fields = sqlQuery.split(" ")[1]
        table = chartData["dateFilterTable"]
        dateFilterField = chartData["dateFilterField"]

        chartInfo = supabase.table(table).select(fields).gte(dateFilterField, startDate).lte(dateFilterField, endDate).order(dateFilterField).execute()
        chartInfoPrev = supabase.table(table).select(fields).gte(dateFilterField, startDatePrev).lte(dateFilterField, endDatePrev).order(dateFilterField).execute()
        data = dict(chartInfo)["data"]
        dataPrev = dict(chartInfoPrev)["data"]

        bucketSize = 30 if dateRange == "LAST_90_DAYS" else 7
        bucketData = bucketizeData(data, bucketSize, endDate, dateFilterField, yAxisField)
        bucketDataPrev = bucketizeData(dataPrev, bucketSize, endDatePrev, dateFilterField, yAxisField)
        
        mergeBucketData(bucketData, bucketDataPrev, yAxisField)
        chartInfoList.append({"chartName": chartName, "xAxisField": xAxisField, "yAxisField": yAxisField, "id": id, "chartType": chartType, "data": bucketData})


    return jsonify(chartInfoList)


def convertDatetimeToDate(datetime):
    return str(datetime).split(" ")[0]

def bucketizeData(data, bucketSize, endDate, dateFilterField, yAxisField):
    endDate = datetime.strptime(endDate, '%Y-%m-%d')
    startDate = endDate - timedelta(days=bucketSize)

    newBucketedData = []
    buckets = {}

    # Iterate through data and bucket the points
    for dataPoint in data:
        dateToCheck = datetime.strptime(dataPoint[dateFilterField], '%Y-%m-%d')  # Convert string to datetime
        
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

    return newBucketedData

def mergeBucketData(bucketData, bucketDataPrev, yAxisField):
    # bucketData and bucketDataPrev will both be sorted
    # so go through bucketData and put the bucketDataPrev value inside bucketData

    # start with the last item in bucketData
    curIndex = -1
    prevLength = len(bucketDataPrev)

    for i in range(len(bucketData), -1, -1):
        if -curIndex < prevLength:
            bucketData[curIndex][yAxisField + "Prev"] = bucketDataPrev[curIndex][yAxisField]
        else:
            break
        curIndex -= 1
    
    return bucketData




    







if __name__ == '__main__':

    app.run(debug=True, port=8080)
