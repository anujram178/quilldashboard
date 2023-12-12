import React, { useState, useEffect } from 'react';
import { format, parseISO } from 'date-fns';
import './Chart.css'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';


function BarGraph({ data, xAxis, yAxis }) {
    return (
            <BarChart width={830} height={450} data={data}
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey={xAxis} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey={yAxis} fill="#8884d8" />
                <Bar dataKey={yAxis+"Prev"} fill="#82ca9d" />
            </BarChart>
    )
}

export default BarGraph;