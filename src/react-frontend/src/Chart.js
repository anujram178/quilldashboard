import React, { useState, useEffect } from 'react';
import { format, parseISO } from 'date-fns';
import './Chart.css'
import LineGraph from './LineGraph'
import BarGraph from './BarGraph'

function Chart({ name, data, chartType, xAxis, yAxis }) {

    // convert the date from a string like "2023-11-26" to November 26 2023
    const formattedData = data.map((dataPoint) => ({
        ...dataPoint,
        [xAxis]: format(parseISO(dataPoint[xAxis]), 'MMMM d yyyy')
    }));

    // LineGraph or BarGraph depending on the chartType which we get from the backend

    return (
        <div className='chart'>
            <h2> {name} </h2>
            {chartType == "line" && <LineGraph xAxis={xAxis} yAxis={yAxis} data={formattedData}/>}
            {chartType == "bar" && <BarGraph xAxis={xAxis} yAxis={yAxis} data={formattedData}/>}
        </div>
    )
}

export default Chart;