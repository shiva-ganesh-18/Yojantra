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

function App() {
  const { token, user } = useAuthStore();

  if (!token) return <Login />;

  // Role-based admin access check
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin';

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/onboarding" element={<Onboarding />} />
        <Route path="/schemes" element={<Schemes />} />
        <Route path="/matches" element={<Matches />} />
        <Route path="/applications" element={<Applications />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/csc" element={<CSCLocator />} />
        <Route path="/notifications" element={<Notifications />} />
        <Route path="/profile" element={<Profile />} />
        {isAdmin && <Route path="/admin" element={<AdminDashboard />} />}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}

export default App;
