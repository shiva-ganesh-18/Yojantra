import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './hooks/useAuth';
import Layout from './components/Layout';
import Onboarding from './pages/Onboarding';
import Dashboard from './pages/Dashboard';
import Schemes from './pages/Schemes';
import Matches from './pages/Matches';
import Applications from './pages/Applications';
import Documents from './pages/Documents';
import Chat from './pages/Chat';
import Profile from './pages/Profile';
import CSCLocator from './pages/CSCLocator';
import Notifications from './pages/Notifications';
import AdminDashboard from './pages/AdminDashboard';
import Login from './pages/Login';
import Institutions from './pages/Institutions';

function App() {
  const { token, user } = useAuthStore();

  if (!token) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="*" element={<Login />} />
      </Routes>
    );
  }

  // Role-based admin & partner officer access check
  const isOfficerOrAdmin = ['admin', 'super_admin', 'partner_officer', 'nodal_officer'].includes(user?.role);

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/login" element={<Navigate to="/" replace />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/schemes" element={<Schemes />} />
        <Route path="/matches" element={<Matches />} />
        <Route path="/applications" element={<Applications />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/csc" element={<CSCLocator />} />
        <Route path="/csc-locator" element={<CSCLocator />} />
        <Route path="/institutions" element={<Institutions />} />
        <Route path="/partners" element={<Institutions />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/profile" element={<Profile />} />

        {isOfficerOrAdmin && <Route path="/admin" element={<AdminDashboard />} />}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default App;
