import React, { useState, useEffect } from 'react';
import { format, parseISO } from 'date-fns';
import './Chart.css'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';


function LineGraph({ data, xAxis, yAxis }) {
    console.log(data);

    return (
            <LineChart width={830} height={450} data={data}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey={xAxis} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="natural" dataKey={yAxis} stroke="#8884d8" dot={false} />
                <Line type="natural" dataKey={yAxis+"Prev"} stroke="#82ca9d" dot={false} />
            </LineChart>
    )
}

export default LineGraph;