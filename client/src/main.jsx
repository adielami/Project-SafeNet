import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import App from './App'
import Logs from './Logs'
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Settings from './Settings'



ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <BrowserRouter>
            <Routes>
                <Route path="/" element={<App />} />
                <Route path="/logs" element={<Logs />} />
                <Route path="/settings" element={<Settings />} />
            </Routes>
        </BrowserRouter>
    </React.StrictMode>,
)
