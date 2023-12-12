import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Chart from './Chart';
import Dropdown from 'react-dropdown';
import 'react-dropdown/style.css';
import "./Dashboard.css";
import * as dayjs from 'dayjs';
import SingleInputDateRangePicker from './DateRangePicker';

const dateFilterOptions = ["LAST_90_DAYS", "LAST_30_DAYS", "CURRENT_MONTH"];
const prevDateFilterOptions = ["PREVIOUS_90_DAYS", "PREVIOUS_30_DAYS", "PREVIOUS_MONTH"];

const prevDateFilterOptionsMap = {
    "LAST_90_DAYS" : "PREVIOUS_90_DAYS",
    "LAST_30_DAYS" : "PREVIOUS_30_DAYS",
    "CURRENT_MONTH" : "PREVIOUS_MONTH"
}

function Dashboard({ dashboardName }) {
    const [dashboardData, setDashboardData] = useState([]);
    const [dateFilter, setDateFilter] = useState("");
    const [previousDateFilter, setPreviousDateFilter] = useState("");
    const [selectedDateRange, setSelectedDateRange] = useState([null, null]);
    const [isFromDatePicker, setIsFromDatePicker] = useState(false)
    const [chartsList, setChartsList] = useState([]);

    const handleDateChange = (newDateRange) => {
        console.log(newDateRange);
        setSelectedDateRange(newDateRange);
    };


    useEffect(() => {
        axios.get(`http://localhost:8080/dashboard/${dashboardName}`).then((response) => {
            if (response.data.length !== 0) {
                let currentDateRange = response.data[0].initialDateRange;
                let prevDateRange = prevDateFilterOptionsMap[currentDateRange];
                const chartsList = response.data[0].chartsList;
                const url = constructChartDataURL(dashboardName, currentDateRange, prevDateRange, selectedDateRange, false);
                
                axios.get(url).then((chartsResponse) => {
                    if (chartsResponse.data.length !== 0) {
                        setDashboardData(chartsResponse.data);
                    }
                });

                setDateFilter(currentDateRange);
                setPreviousDateFilter(prevDateRange);
                setChartsList(chartsList);
            }
        });
    }, []);

    useEffect(() => {
        // when you have not selected an end date - do not send backend request 

        if (selectedDateRange[1] != null) {

            const url = constructChartDataURL(dashboardName, dateFilter, previousDateFilter, selectedDateRange, true);

            axios.get(url).then((chartsResponse) => {
                if (chartsResponse.data.length !== 0) {
                    setDashboardData(chartsResponse.data);
                    setIsFromDatePicker(true);
                }
            });
        }
    },
        [selectedDateRange])

    function changeDateFilter(selectedDateFilter) {
        // use the current selected value when fetching from backend
        const curDateFilter = selectedDateFilter.value;

        const url = constructChartDataURL(dashboardName, curDateFilter, previousDateFilter, selectedDateRange, false)
        axios.get(url).then((chartsResponse) => {
            if (chartsResponse.data.length !== 0) {
                setDashboardData(chartsResponse.data);
            }
        });
        setDateFilter(curDateFilter);
        setIsFromDatePicker(false);
    }

    function changePrevDateFilter(selectedDateFilter) {
        // use the current selected value when fetching from backend
        const curDateFilter = selectedDateFilter.value;

        const url = constructChartDataURL(dashboardName, dateFilter, curDateFilter, selectedDateRange, isFromDatePicker)
        axios.get(url).then((chartsResponse) => {
            if (chartsResponse.data.length !== 0) {
                setDashboardData(chartsResponse.data);
            }
        });
        setPreviousDateFilter(curDateFilter);
    }

    return (
        <div className='dashboard'>
            <div className="dropdown">
                <SingleInputDateRangePicker handleDateChange={handleDateChange} selectedDateRange={selectedDateRange} />
                <div className='dropdownBar'>
                    <Dropdown
                        options={dateFilterOptions}
                        value={dateFilter}
                        onChange={changeDateFilter}
                    />
                </div>
                <h4> compared to</h4>
                <div className="dropdownBar">
                    <Dropdown
                        options={prevDateFilterOptions}
                        value={previousDateFilter}
                        onChange={changePrevDateFilter}
                    />
                </div>
            </div>

            {dashboardData.map((chart) => (
                <Chart
                    key={chart.id} // Ensure a unique key for each Chart component
                    name={chart.chartName}
                    data={chart.data}
                    chartType={chart.chartType}
                    xAxis={chart.xAxisField}
                    yAxis={chart.yAxisField}
                />
            ))}
        </div>
    );
}

function convertDateObjectToString(date) {
    return date.format('YYYY-MM-DD')
}

function constructChartDataURL(dashboardName, dateFilter, previousDateFilter, selectedDateRange, isFromDatePicker) {
    let url = `http://localhost:8080/charts/${dashboardName}`;
    let startDate = null;
    let endDate = null;
    if (selectedDateRange[0] != null && selectedDateRange[1] != null) {
        startDate = convertDateObjectToString(selectedDateRange[0]);
        endDate = convertDateObjectToString(selectedDateRange[1]);
    }
    url += `?dateRange=${dateFilter}&prevDateRange=${previousDateFilter}`
    url += `&startDate=${startDate}&endDate=${endDate}&isFromDatePicker=${isFromDatePicker}`;

    return url;
}

function constructChartDataURLbyID(chartId, dateFilter, previousDateFilter, selectedDateRange, isFromDatePicker) {
    let url = `http://localhost:8080/chart/${chartId}`;
    let startDate = null;
    let endDate = null;
    if (selectedDateRange[0] != null && selectedDateRange[1] != null) {
        startDate = convertDateObjectToString(selectedDateRange[0]);
        endDate = convertDateObjectToString(selectedDateRange[1]);
    }
    url += `?dateRange=${dateFilter}&prevDateRange=${previousDateFilter}`
    url += `&startDate=${startDate}&endDate=${endDate}&isFromDatePicker=${isFromDatePicker}`;

    return url;
}

// function useCachedDashboardData(currentDateRange, newDateRange, dashboardData, setDashboardData) {
//     const dashboardDataCopy = JSON.parse(JSON.stringify(dashboardData));
//     let today = dayjs();

//     if (currentDateRange == "LAST_90_DAYS") {
//         if (newDateRange == "LAST_30_DAYS") {
//             filterChartDataByDateRange(dashboardDataCopy, today.subtract(30, 'day') , today);
//         }
//         else if 
//     }
// }

// // Function to filter chart data by date range
// function filterChartDataByDateRange(chartData, startDate, endDate) {
//     return chartData.map(chart => ({
//       ...chart,
//       data: chart.data.filter(entry => {
//         const currentDate = new Date(entry.Date);
//         return currentDate >= startDate && currentDate <= endDate;
//       })
//     }));
//   }
  


export default Dashboard;
