import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import DashboardPage from './pages/DashboardPage';
import EventsPage from './pages/EventsPage';
import ROIsPage from './pages/ROIsPage';
import NLPPage from './pages/NLPPage';
import CamerasPage from './pages/CamerasPage';
import SettingsPage from './pages/SettingsPage';
import { useState } from 'react';

export default function App() {
  const [refreshToken, setRefreshToken] = useState(0);

  return (
    <div className="min-h-screen bg-base-900 flex">
      <Sidebar />
      <div className="flex-1 min-w-0 flex flex-col">
        <TopBar onRefresh={() => setRefreshToken(t => t + 1)} />
        <main className="flex-1 p-6 overflow-x-hidden">
          <Routes>
            <Route path="/" element={<DashboardPage refreshKey={refreshToken} />} />
            <Route path="/events" element={<EventsPage refreshKey={refreshToken} />} />
            <Route path="/rois" element={<ROIsPage />} />
            <Route path="/nlp" element={<NLPPage />} />
            <Route path="/cameras" element={<CamerasPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
