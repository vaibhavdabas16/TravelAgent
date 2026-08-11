import { useState, useEffect, useCallback } from 'react';
import { toast } from 'sonner';
import { api } from '../services/api';
import { motion, AnimatePresence } from 'motion/react';
import { ArrowLeft, Check, ChevronRight } from 'lucide-react';
import { Button } from './ui/button';
import { PlanningInterface } from './planning-interface';
import { PlacesToVisitSection } from './planning-sections/places-to-visit';
import { AccommodationsSection } from './planning-sections/accommodations';
import { DiningSection } from './planning-sections/dining';
import { TransportationSection } from './planning-sections/transportation';
import { ActivitiesSection } from './planning-sections/activities';
import { ShoppingSection } from './planning-sections/shopping';
import { WellnessSection } from './planning-sections/wellness';

interface PlanningFlowProps {
  initialData?: any;
  onComplete: (data: any) => void;
  onBack: () => void;
}

const planningSteps = [
  { id: 'questionnaire', name: 'Tell Us About Your Trip', component: PlanningInterface },
  { id: 'places', name: 'Places to Visit', component: PlacesToVisitSection },
  { id: 'accommodations', name: 'Accommodations', component: AccommodationsSection },
  { id: 'dining', name: 'Dining', component: DiningSection },
  { id: 'transportation', name: 'Transportation', component: TransportationSection },
  { id: 'activities', name: 'Activities & Adventures', component: ActivitiesSection },
  { id: 'shopping', name: 'Shopping & Markets', component: ShoppingSection },
  { id: 'wellness', name: 'Wellness & Relaxation', component: WellnessSection },
];

export function PlanningFlow({ initialData, onComplete, onBack }: PlanningFlowProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [planningData, setPlanningData] = useState<any>({
    query: initialData?.query || '',
    destination: initialData?.destination || null,
    tripStyle: 'balanced', // laid-back, balanced, adventurous
    selectedItems: {},
    sessionId: null, // Track session ID
  });
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [isLoadingNext, setIsLoadingNext] = useState(false);
  const [resetCount, setResetCount] = useState(0);

  const currentStepData = planningSteps[currentStep];
  const CurrentComponent = currentStepData.component;



  const handleNext = async () => {
    if (isTransitioning || isLoadingNext) return;

    if (currentStep < planningSteps.length - 1) {
      setIsTransitioning(true);
      setIsLoadingNext(true);

      try {
        const currentStepId = planningSteps[currentStep].id;
        const nextStepId = planningSteps[currentStep + 1].id;
        const sessionId = planningData.sessionId;

        // 1. Submit selections for current step
        if (currentStepId === 'places') {
          const selectedPlaces = planningData.selectedItems.places || [];
          if (selectedPlaces.length > 0) {
            await api.selectPlaces(sessionId, selectedPlaces);
          }
        } else if (currentStepId === 'accommodations') {
          const selectedAccommodations = planningData.selectedItems.accommodations;
          console.log('Submitting accommodations:', selectedAccommodations);
          if (selectedAccommodations && selectedAccommodations.length > 0) {
            await api.selectAccommodation(sessionId, selectedAccommodations);
          }
        } else if (currentStepId === 'transportation') {
          const selectedTransport = planningData.selectedItems.transportation;
          if (selectedTransport && selectedTransport.length > 0) {
            await api.selectTransport(sessionId, selectedTransport);
          }
        } else if (currentStepId === 'dining') {
          const selectedDining = planningData.selectedItems.dining;
          if (selectedDining && selectedDining.length > 0) {
            await api.selectDining(sessionId, selectedDining);
          }
        } else if (currentStepId === 'activities') {
          const selectedActivities = planningData.selectedItems.activities;
          if (selectedActivities && selectedActivities.length > 0) {
            await api.selectActivities(sessionId, selectedActivities);
          }
        } else if (currentStepId === 'shopping') {
          const selectedShopping = planningData.selectedItems.shopping;
          if (selectedShopping && selectedShopping.length > 0) {
            await api.selectShopping(sessionId, selectedShopping);
          }
        } else if (currentStepId === 'wellness') {
          const selectedWellness = planningData.selectedItems.wellness;
          if (selectedWellness && selectedWellness.length > 0) {
            await api.selectWellness(sessionId, selectedWellness);
          }
        }

        // 2. Fetch data for next step
        let nextStepData = {};
        if (nextStepId === 'accommodations') {
          toast.info("Finding the best places to stay...");
          const response = await api.searchAccommodations(sessionId);
          nextStepData = { recommended_hotels: response.hotels };
        } else if (nextStepId === 'dining') {
          toast.info("Curating dining experiences...");
          const response = await api.searchDining(sessionId);
          nextStepData = { dining: response.restaurants }; // Mock
        } else if (nextStepId === 'transportation') {
          const response = await api.searchTransport(sessionId);
          // Map to expected format for TransportationSection
          nextStepData = {
            recommended_flights: response.transport_options?.flights || [],
            local_transport: response.transport_options?.local || {}
          };
        } else if (nextStepId === 'activities') {
          const response = await api.searchActivities(sessionId);
          nextStepData = { activities: response.activities };
        } else if (nextStepId === 'shopping') {
          const response = await api.searchShopping(sessionId);
          nextStepData = { shopping: response.shopping };
        } else if (nextStepId === 'wellness') {
          const response = await api.searchWellness(sessionId);
          nextStepData = { wellness: response.wellness_options };
        }

        // Update planning data with new fetched data
        setPlanningData((prev: any) => ({
          ...prev,
          ...nextStepData
        }));

        // Move to next step
        setTimeout(() => {
          setCurrentStep(currentStep + 1);
          setIsTransitioning(false);
          setIsLoadingNext(false);
        }, 300);

      } catch (error) {
        console.error("Error transitioning step:", error);
        setIsTransitioning(false);
        setIsLoadingNext(false);
        toast.error("Failed to load next section. Please try again.");
      }
    } else {
      // Complete planning
      if (isTransitioning) return;

      try {
        setIsTransitioning(true);
        toast.info("Generating your final itinerary...");

        // Ensure last step (wellness) is saved too!
        const currentStepId = planningSteps[currentStep].id;
        const sessionId = planningData.sessionId;
        if (currentStepId === 'wellness') {
          const selectedWellness = planningData.selectedItems.wellness;
          if (selectedWellness && selectedWellness.length > 0) {
            await api.selectWellness(sessionId, selectedWellness);
          }
        }

        const itinerary = await api.generateItinerary(planningData.sessionId);
        console.log('Planning completed with itinerary:', itinerary);
        // Merge backend itinerary with existing planning data to preserve context
        onComplete({ ...planningData, ...itinerary });
      } catch (error) {
        console.error("Error generating itinerary:", error);
        setIsTransitioning(false);
        toast.error("Failed to generate itinerary.");
      }
    }
  };

  const handlePrevious = () => {
    if (isTransitioning) return;

    if (currentStep > 0) {
      setIsTransitioning(true);
      setTimeout(() => {
        setCurrentStep(currentStep - 1);
        setIsTransitioning(false);
      }, 300);
    } else {
      onBack();
    }
  };

  const handleSectionComplete = useCallback(async (sectionData: any) => {
    // Prevent duplicate updates if data hasn't changed
    if (currentStepData.id !== 'questionnaire') {
      const currentData = planningData.selectedItems[currentStepData.id];
      if (JSON.stringify(currentData) === JSON.stringify(sectionData)) {
        return;
      }
    }

    console.log('Section completed:', currentStepData.id, sectionData);

    if (currentStepData.id === 'questionnaire') {
      // Handle questionnaire completion
      const updatedData = {
        ...planningData,
        ...sectionData,
        tripStyle: sectionData.tripStyle || 'balanced'
      };
      setPlanningData(updatedData);

      // Start transition and loading
      setIsTransitioning(true);
      // toast.info("Starting your planning session..."); // Removed toast, using spinner instead

      // Safety timeout for spinner - start BEFORE async calls
      const safetyTimer = setTimeout(() => {
        setResetCount(prev => prev + 1);
        setIsTransitioning(false);
      }, 15000);

      try {
        // 1. Start Planning Session
        const startResponse = await api.startPlanning({
          query: updatedData.query,
          destination: updatedData.destination,
          travelers: updatedData.travelers,
          budget: updatedData.budget,
          interests: updatedData.interests,
          pace: updatedData.pace,
          amenities: updatedData.amenities,
          dates: updatedData.dates,
          tripStyle: updatedData.tripStyle,
          origin: updatedData.origin // Pass origin to backend
        });

        const sessionId = startResponse.session_id;

        // 2. Discover Places (First Step)
        // toast.info(`Discovering amazing places in ${updatedData.destination}...`);
        const placesResponse = await api.discoverPlaces(sessionId, updatedData.tripStyle);

        // Update state
        setPlanningData((prev: any) => ({
          ...prev,
          sessionId: sessionId,
          pois: placesResponse.pois || [],
          // Clear legacy fields to avoid confusion
          tripId: null,
          recommended_hotels: [],
          recommended_flights: []
        }));

        // Move to next step
        setTimeout(() => {
          setCurrentStep(1);
          setIsTransitioning(false);
        }, 500);

        // Clear safety timeout on success
        clearTimeout(safetyTimer);

      } catch (error) {
        console.error('Failed to start planning:', error);
        setIsTransitioning(false);
        toast.error("Failed to start planning session. Please try again.");
        // Force reset of the current component to clear "loading/completed" state
        setResetCount(prev => prev + 1);
      }

    } else {
      // Handle specialized section completion
      const updatedData = {
        ...planningData,
        selectedItems: {
          ...planningData.selectedItems,
          [currentStepData.id]: sectionData
        }
      };
      console.log('Updated planning data after section:', updatedData);
      setPlanningData(updatedData);
    }
  }, [currentStepData, planningData]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative">
      {/* Loading Overlay for Questionnaire Transition */}
      <AnimatePresence>
        {isTransitioning && currentStep === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[60] bg-black/80 backdrop-blur-md flex flex-col items-center justify-center"
          >
            <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mb-6"></div>
            <h2 className="text-2xl font-bold text-white mb-2">Curating Your Experience</h2>
            <p className="text-white/70">Finding the best spots in {planningData.destination || 'your destination'}...</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Header with progress */}
      <motion.div
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="fixed top-0 left-0 right-0 z-50 bg-black/20 backdrop-blur-xl border-b border-white/10"
      >
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <Button
              variant="ghost"
              onClick={handlePrevious}
              className="text-white hover:bg-white/10"
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              {currentStep === 0 ? 'Back to Home' : 'Previous'}
            </Button>

            {/* Progress indicator */}
            <div className="flex items-center space-x-2">
              {planningSteps.map((step, index) => (
                <motion.div
                  key={step.id}
                  className={`w-3 h-3 rounded-full ${index <= currentStep ? 'bg-blue-400' : 'bg-white/20'
                    }`}
                  animate={{
                    scale: index === currentStep ? 1.2 : 1,
                    opacity: index <= currentStep ? 1 : 0.5
                  }}
                  transition={{ duration: 0.3 }}
                />
              ))}
            </div>

            <div className="text-white">
              <span className="text-sm opacity-70">Step {currentStep + 1} of {planningSteps.length}</span>
            </div>
          </div>

          {/* Step title */}
          <motion.h1
            key={currentStep}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-2xl text-white mt-4"
          >
            {currentStepData.name}
          </motion.h1>
        </div>
      </motion.div>

      {/* Main content */}
      <div className={`pt-32 ${currentStepData.id === 'questionnaire' ? 'pb-8' : 'pb-24'}`}>
        <AnimatePresence mode="wait">
          <motion.div
            key={`${currentStep}-${resetCount}`}
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -50 }}
            transition={{ duration: 0.5, ease: "easeInOut" }}
            className="container mx-auto px-6"
          >
            {(() => {
              const Component = CurrentComponent as any;
              return currentStepData.id === 'questionnaire' ? (
                <Component
                  onComplete={handleSectionComplete}
                  onClose={() => { }} // No close for questionnaire in flow
                  initialData={planningData}
                />
              ) : (
                <Component
                  planningData={planningData}
                  onSelectionChange={handleSectionComplete}
                  isTransitioning={isTransitioning}
                />
              );
            })()}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Footer with navigation - hide during questionnaire */}
      {currentStepData.id !== 'questionnaire' && (
        <motion.div
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.8, ease: "easeOut", delay: 0.3 }}
          className="fixed bottom-0 left-0 right-0 z-50 bg-black/20 backdrop-blur-xl border-t border-white/10"
        >
          <div className="container mx-auto px-6 py-4">
            <div className="flex justify-between items-center">
              <div className="text-white/70 text-sm">
                Choose the options that appeal to you most
              </div>

              <Button
                onClick={handleNext}
                className="bg-blue-600 hover:bg-blue-700 text-white"
                disabled={isTransitioning}
              >
                {currentStep === planningSteps.length - 1 ? 'Complete Planning' : 'Next Section'}
                {currentStep !== planningSteps.length - 1 && <ChevronRight className="w-4 h-4 ml-2" />}
                {currentStep === planningSteps.length - 1 && <Check className="w-4 h-4 ml-2" />}
              </Button>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}