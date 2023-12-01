import React, { useState, useEffect } from 'react';
import { format, parseISO } from 'date-fns';
import './Chart.css'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';


function Chart({ name, data, xAxis, yAxis }) {

    const formattedData = data.map((dataPoint) => ({
        ...dataPoint,
        [xAxis]: format(parseISO(dataPoint[xAxis]), 'MMMM d yyyy')
    }));

    return (
        <div className='chart'>
            <h2> {name} </h2>
            <LineChart width={830} height={450} data={formattedData}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey={xAxis} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="natural" dataKey={yAxis} stroke="#8884d8" dot={false} />
            </LineChart>
        </div>
    )
}

export default Chart;