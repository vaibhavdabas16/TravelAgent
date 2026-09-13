import { Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from './components/shared/Toaster';
import { AuthProvider } from './contexts/AuthContext';
import { HomePage } from './routes/HomePage';
import { PlanPage } from './routes/PlanPage';
import { TripPage } from './routes/TripPage';
import { TripsPage } from './routes/TripsPage';

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<HomePage />} />
        {/* A bare /plan is the brief; once the server hands back a session id
            the planner redirects to the addressable form below. */}
        <Route path="/plan" element={<PlanPage />} />
        <Route path="/plan/:sessionId" element={<Navigate to="places" replace />} />
        <Route path="/plan/:sessionId/:stepId" element={<PlanPage />} />
        <Route path="/trip/:sessionId" element={<TripPage />} />
        <Route path="/trips" element={<TripsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toaster />
    </AuthProvider>
  );
}
