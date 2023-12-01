import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Chart from './Chart';
import Dropdown from 'react-dropdown';
import 'react-dropdown/style.css';
import "./Dashboard.css";

function Dashboard({ dashboardName }) {
    const [dashboardData, setDashboardData] = useState([]);
    const [dateFilter, setDateFilter] = useState("");
    const [previousDateFilter, setPreviousDateFilter] = useState("");


    useEffect(() => {
        axios.get(`http://localhost:8080/dashboard/${dashboardName}`).then((response) => {
            if (response.data.length !== 0) {
                setDateFilter(response.data[0].initialDateRange);
                setPreviousDateFilter(response.data[0].initialDateRange);

                axios.get(`http://localhost:8080/charts/${dashboardName}?dateRange=${dateFilter}`).then((chartsResponse) => {
                    if (chartsResponse.data.length !== 0) {
                        setDashboardData(chartsResponse.data);
                    }
                });
            }
        });
    }, []);

    const dateFilterOptions = ["LAST_90_DAYS", "LAST_30_DAYS", "CURRENT_MONTH"];
    const prevDateFilterOptions = {
        "LAST_90_DAYS": "PREVIOUS_90_DAYS",
        "LAST_30_DAYS": "PREVIOUS_30_DAYS",
        "CURRENT_MONTH": "LAST_MONTH"
    };

    function changeDateFilter(selectedDateFilter) {
        const curDateFilter = selectedDateFilter.value;
        axios.get(`http://localhost:8080/charts/${dashboardName}?dateRange=${curDateFilter}`).then((chartsResponse) => {
            if (chartsResponse.data.length !== 0) {
                setDashboardData(chartsResponse.data);
            }
        });
        setDateFilter(curDateFilter);
    }

    return (
        <div className='dashboard'>
            <div className="dropdown">
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
                        options={dateFilterOptions}
                        value={prevDateFilterOptions[dateFilter]} 
                        onChange={changeDateFilter}
                        disabled={true}
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

export default Dashboard;
