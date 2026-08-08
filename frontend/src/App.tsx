import { useState } from 'react';
import { Toaster } from './components/ui/sonner';
import { AuthProvider } from './contexts/AuthContext';
import { HeroSection } from './components/hero-section';
import { Navbar } from './components/navbar';
import { TripsCarousel } from './components/trips-carousel';
import { FeatureHighlightSection } from './components/FeatureHighlightSection';
import { ExperienceScrollSection } from './components/ExperienceScrollSection';
import { FeatureImageSection } from './components/FeatureImageSection';
import { Footer } from './components/Footer';
import { TripPlan } from './components/trip-plan';
import { PlanningFlow } from './components/planning-flow';
import { MediaShowcaseSection } from './components/MediaShowcaseSection';

export default function App() {
  const [currentView, setCurrentView] = useState<'home' | 'planning' | 'trip-plan'>('home');
  const [tripData, setTripData] = useState(null);
  const [planningData, setPlanningData] = useState(null);

  const handleStartPlanning = (initialData?: any) => {
    setPlanningData(initialData);
    setCurrentView('planning');
  };

  const handlePlanningComplete = (data: any) => {
    setTripData(data);
    setCurrentView('trip-plan');
  };

  const handleViewTripPlan = (data?: any) => {
    setTripData(data);
    setCurrentView('trip-plan');
  };

  const handleBackToHome = () => {
    setCurrentView('home');
    setTripData(null);
    setPlanningData(null);
  };

  return (
    <AuthProvider>
      {currentView === 'planning' && (
        <PlanningFlow
          initialData={planningData}
          onComplete={handlePlanningComplete}
          onBack={handleBackToHome}
        />
      )}

      {currentView === 'trip-plan' && (
        <TripPlan
          tripData={tripData}
          onEdit={(section, data) => console.log('Edit:', section, data)}
          onClose={handleBackToHome}
        />
      )}

      {currentView === 'home' && (
        <div className="min-h-screen bg-white relative">
          <Navbar />
          <HeroSection onStartPlanning={handleStartPlanning} onViewTripPlan={handleViewTripPlan} />
          <TripsCarousel />
          <FeatureImageSection />
          <Toaster />
        </div>
      )}
    </AuthProvider>
  );
}
