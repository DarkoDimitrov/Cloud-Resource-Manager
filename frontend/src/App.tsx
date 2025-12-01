import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import Providers from './components/Providers';
import Instances from './components/Instances';
import InstanceDetails from './components/InstanceDetails';
import AIChat from './components/AIChat';
import CostForecast from './components/CostForecast';
import Anomalies from './components/Anomalies';

function Navigation() {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname === path ? 'bg-primary-700 text-white' : 'text-gray-300 hover:bg-primary-600 hover:text-white';
  };

  return (
    <nav className="bg-primary-700 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className="text-white text-xl font-bold flex items-center">
                <svg className="w-8 h-8 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
                </svg>
                Cloud Resource Manager
              </h1>
            </div>
            <div className="ml-10 flex items-baseline space-x-4">
              <Link
                to="/"
                className={`${isActive('/')} px-3 py-2 rounded-md text-sm font-medium transition-colors`}
              >
                Dashboard
              </Link>
              <Link
                to="/providers"
                className={`${isActive('/providers')} px-3 py-2 rounded-md text-sm font-medium transition-colors`}
              >
                Providers
              </Link>
              <Link
                to="/instances"
                className={`${isActive('/instances')} px-3 py-2 rounded-md text-sm font-medium transition-colors`}
              >
                Instances
              </Link>
              <Link
                to="/ai-chat"
                className={`${isActive('/ai-chat')} px-3 py-2 rounded-md text-sm font-medium transition-colors flex items-center`}
              >
                <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
                AI Chat
              </Link>
              <Link
                to="/forecast"
                className={`${isActive('/forecast')} px-3 py-2 rounded-md text-sm font-medium transition-colors`}
              >
                Cost Forecast
              </Link>
              <Link
                to="/anomalies"
                className={`${isActive('/anomalies')} px-3 py-2 rounded-md text-sm font-medium transition-colors`}
              >
                Anomalies
              </Link>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/providers" element={<Providers />} />
            <Route path="/instances" element={<Instances />} />
            <Route path="/instances/:id" element={<InstanceDetails />} />
            <Route path="/ai-chat" element={<AIChat />} />
            <Route path="/forecast" element={<CostForecast />} />
            <Route path="/anomalies" element={<Anomalies />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
