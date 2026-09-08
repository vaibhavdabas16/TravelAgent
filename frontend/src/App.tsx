import { Navigate, Route, Routes } from 'react-router-dom';
import { Toaster } from './components/ui/sonner';
import { AuthProvider } from './contexts/AuthContext';
import { HomePage } from './routes/HomePage';
import { TripPage } from './routes/TripPage';
import { PlanningFlow } from './components/planning-flow';

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<HomePage />} />
        {/* A bare /plan opens the questionnaire; once the server hands back a
            session id the wizard redirects to the addressable form below. */}
        <Route path="/plan" element={<PlanningFlow />} />
        <Route path="/plan/:sessionId" element={<Navigate to="places" replace />} />
        <Route path="/plan/:sessionId/:stepId" element={<PlanningFlow />} />
        <Route path="/trip/:sessionId" element={<TripPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toaster />
    </AuthProvider>
  );
}
