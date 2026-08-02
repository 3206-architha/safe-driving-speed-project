import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import History from './pages/History';

function NavBar() {
  const location = useLocation();
  const token = localStorage.getItem('access_token');
  if (!token || location.pathname.startsWith('/login') || location.pathname.startsWith('/register')) {
    return null;
  }
  return (
    <div className="bg-slate-900 border-b border-slate-800 px-6 py-2 flex gap-4 text-sm">
      <Link to="/dashboard" className="text-slate-300 hover:text-white">Dashboard</Link>
      <Link to="/history" className="text-slate-300 hover:text-white">History</Link>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <NavBar />
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/history"
            element={
              <ProtectedRoute>
                <History />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Login />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
