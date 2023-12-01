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
        startDate = endDate - timedelta(90)
    elif dateRange == "LAST_30_DAYS":
        startDate = endDate - timedelta(30)
    else:
        startDate = endDate.replace(day=1)

    startDate, endDate = convertDatetimeToDate(startDate), convertDatetimeToDate(endDate)

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
        data = dict(chartInfo)["data"]

        bucketSize = 30 if dateRange == "LAST_90_DAYS" else 7
        bucketData = bucketizeData(data, bucketSize, endDate, dateFilterField, yAxisField)
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




    







if __name__ == '__main__':

    app.run(debug=True, port=8080)
