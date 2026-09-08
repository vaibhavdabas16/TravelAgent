import { useNavigate } from 'react-router-dom';
import { HeroSection } from '../components/hero-section';
import { Navbar } from '../components/navbar';
import { TripsCarousel } from '../components/trips-carousel';
import { FeatureImageSection } from '../components/FeatureImageSection';

export function HomePage() {
  const navigate = useNavigate();

  // The hero hands us whatever the visitor typed. It travels as router state so
  // the questionnaire can prefill without putting a free-text query in the URL.
  const handleStartPlanning = (initialData?: any) => {
    navigate('/plan', { state: { initialData } });
  };

  const handleViewTripPlan = (data?: any) => {
    navigate('/trip/preview', { state: { tripData: data } });
  };

  return (
    <div className="min-h-screen bg-white relative">
      <Navbar />
      <HeroSection onStartPlanning={handleStartPlanning} onViewTripPlan={handleViewTripPlan} />
      <TripsCarousel />
      <FeatureImageSection />
    </div>
  );
}
