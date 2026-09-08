import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { toast } from 'sonner';
import { api } from '../services/api';
import { motion, AnimatePresence } from 'motion/react';
import { ArrowLeft, Check, ChevronRight, RotateCcw } from 'lucide-react';
import { Button } from './ui/button';
import { PlanningProgress } from './planning-progress';
import { StepRail } from './step-rail';
import { planningSteps, stepIdByIndex, stepIndexById } from '../lib/planning-steps';
import {
  PlanningData,
  emptyPlanningData,
  loadPlanningData,
  savePlanningData,
  saveTrip,
} from '../lib/planning-storage';

/**
 * Which field on the planning data holds the results for a given step. Used to
 * decide whether a step already has what it needs, so that revisiting a step
 * (back button, refresh, deep link) does not re-hit the paid provider APIs.
 */
const STEP_DATA_KEY: Record<string, string> = {
  places: 'pois',
  accommodations: 'recommended_hotels',
  dining: 'dining',
  transportation: 'recommended_flights',
  activities: 'activities',
  shopping: 'shopping',
  wellness: 'wellness',
};

/** Human-readable line shown while a step's data is being fetched. */
const STEP_LOADING_COPY: Record<string, string> = {
  places: 'Discovering places worth your time',
  accommodations: 'Finding the best places to stay',
  dining: 'Curating dining experiences',
  transportation: 'Checking flights and local transit',
  activities: 'Rounding up activities and adventures',
  shopping: 'Looking for markets and shopping',
  wellness: 'Finding spas and quiet corners',
};

export function PlanningFlow() {
  const navigate = useNavigate();
  const location = useLocation();
  const { sessionId, stepId } = useParams<{ sessionId?: string; stepId?: string }>();

  const currentStep = sessionId ? stepIndexById(stepId) : 0;
  const currentStepData = planningSteps[currentStep];
  const CurrentComponent = currentStepData.component as any;

  const [planningData, setPlanningData] = useState<PlanningData>(() => {
    if (sessionId) {
      const restored = loadPlanningData(sessionId);
      if (restored) return restored;
    }
    return emptyPlanningData((location.state as any)?.initialData);
  });

  const [isStarting, setIsStarting] = useState(false);
  const [isLoadingStep, setIsLoadingStep] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [stepError, setStepError] = useState<string | null>(null);

  // Guards against a step's fetch firing twice under StrictMode double-effects
  // or a fast back/forward, which would double-bill the provider APIs.
  const inFlightStep = useRef<string | null>(null);

  // Persist on every change so a refresh mid-wizard resumes where we left off.
  useEffect(() => {
    if (planningData.sessionId) {
      savePlanningData(planningData.sessionId, planningData);
    }
  }, [planningData]);

  /** Fetch the data a step needs, unless we already have it. */
  const loadStepData = useCallback(
    async (targetStepId: string, sid: string, data: PlanningData) => {
      const dataKey = STEP_DATA_KEY[targetStepId];
      if (!dataKey) return; // questionnaire has nothing to fetch

      const existing = data[dataKey];
      if (Array.isArray(existing) ? existing.length > 0 : Boolean(existing)) return;

      if (inFlightStep.current === targetStepId) return;
      inFlightStep.current = targetStepId;

      setIsLoadingStep(true);
      setStepError(null);
      try {
        let patch: Partial<PlanningData> = {};
        switch (targetStepId) {
          case 'places': {
            const res = await api.discoverPlaces(sid, data.tripStyle);
            patch = { pois: res.pois || [] };
            break;
          }
          case 'accommodations': {
            const res = await api.searchAccommodations(sid);
            patch = { recommended_hotels: res.hotels || [] };
            break;
          }
          case 'dining': {
            const res = await api.searchDining(sid);
            patch = { dining: res.restaurants || [] };
            break;
          }
          case 'transportation': {
            const res = await api.searchTransport(sid);
            patch = {
              recommended_flights: res.transport_options?.flights || [],
              local_transport: res.transport_options?.local || {},
            };
            break;
          }
          case 'activities': {
            const res = await api.searchActivities(sid);
            patch = { activities: res.activities || [] };
            break;
          }
          case 'shopping': {
            const res = await api.searchShopping(sid);
            patch = { shopping: res.shopping || [] };
            break;
          }
          case 'wellness': {
            const res = await api.searchWellness(sid);
            patch = { wellness: res.wellness_options || [] };
            break;
          }
        }
        setPlanningData((prev) => ({ ...prev, ...patch }));
      } catch (error: any) {
        const detail =
          error?.response?.status === 404
            ? 'This planning session expired on the server. Start a new trip to continue.'
            : `We could not load ${currentStepData.name.toLowerCase()}.`;
        setStepError(detail);
      } finally {
        setIsLoadingStep(false);
        inFlightStep.current = null;
      }
    },
    [currentStepData.name]
  );

  // Entering a step — by Next, Back, refresh, or a pasted URL — loads its data.
  // Fetching here rather than inside handleNext is what makes deep links work.
  useEffect(() => {
    if (!sessionId || currentStepData.id === 'questionnaire') return;
    loadStepData(currentStepData.id, sessionId, planningData);
    // planningData is intentionally excluded: loadStepData reads the latest via
    // closure on each entry, and including it would refetch on every keystroke.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, currentStepData.id]);

  /** Post the selections for the step we are leaving. */
  const submitSelections = async (leavingStepId: string, sid: string) => {
    const selected = planningData.selectedItems?.[leavingStepId];
    if (!selected || (Array.isArray(selected) && selected.length === 0)) return;

    switch (leavingStepId) {
      case 'places':
        await api.selectPlaces(sid, selected);
        break;
      case 'accommodations':
        await api.selectAccommodation(sid, selected);
        break;
      case 'dining':
        await api.selectDining(sid, selected);
        break;
      case 'transportation':
        await api.selectTransport(sid, selected);
        break;
      case 'activities':
        await api.selectActivities(sid, selected);
        break;
      case 'shopping':
        await api.selectShopping(sid, selected);
        break;
      case 'wellness':
        await api.selectWellness(sid, selected);
        break;
    }
  };

  const handleNext = async () => {
    if (isSubmitting || isLoadingStep || !sessionId) return;
    setIsSubmitting(true);
    setStepError(null);

    try {
      await submitSelections(currentStepData.id, sessionId);

      if (currentStep < planningSteps.length - 1) {
        navigate(`/plan/${sessionId}/${stepIdByIndex(currentStep + 1)}`);
      } else {
        const itinerary = await api.generateItinerary(sessionId);
        const trip = { ...planningData, ...itinerary };
        saveTrip(sessionId, trip);
        navigate(`/trip/${sessionId}`, { state: { tripData: trip } });
      }
    } catch (error: any) {
      const detail =
        error?.response?.status === 404
          ? 'This planning session expired on the server. Start a new trip to continue.'
          : 'We could not save that step. Please try again.';
      setStepError(detail);
      toast.error(detail);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0 && sessionId) {
      navigate(`/plan/${sessionId}/${stepIdByIndex(currentStep - 1)}`);
    } else {
      navigate('/');
    }
  };

  /** Retry whatever failed on the current step. */
  const handleRetry = () => {
    if (!sessionId) return;
    setStepError(null);
    const dataKey = STEP_DATA_KEY[currentStepData.id];
    if (dataKey) {
      // Drop the empty result so loadStepData does not short-circuit.
      setPlanningData((prev) => ({ ...prev, [dataKey]: undefined }));
      loadStepData(currentStepData.id, sessionId, { ...planningData, [dataKey]: undefined });
    }
  };

  /** Questionnaire submit: open the session, then hand off to the URL. */
  const handleQuestionnaireComplete = useCallback(
    async (sectionData: any) => {
      if (isStarting) return;
      const merged: PlanningData = {
        ...planningData,
        ...sectionData,
        tripStyle: sectionData.tripStyle || 'balanced',
      };
      setPlanningData(merged);
      setIsStarting(true);
      setStepError(null);

      try {
        const startResponse = await api.startPlanning({
          query: merged.query,
          destination: merged.destination,
          travelers: merged.travelers,
          budget: merged.budget,
          interests: merged.interests,
          pace: merged.pace,
          amenities: merged.amenities,
          dates: merged.dates,
          tripStyle: merged.tripStyle,
          origin: merged.origin,
        });

        const newSessionId = startResponse.session_id;
        const withSession: PlanningData = { ...merged, sessionId: newSessionId };
        savePlanningData(newSessionId, withSession);
        setPlanningData(withSession);

        // replace: true so the browser Back button from step 1 returns home
        // rather than resubmitting the questionnaire.
        navigate(`/plan/${newSessionId}/places`, { replace: true });
      } catch (error) {
        setStepError('We could not start your planning session. Please try again.');
        toast.error('Failed to start planning session.');
      } finally {
        setIsStarting(false);
      }
    },
    [planningData, isStarting, navigate]
  );

  /** Section submit: record the selection, nothing else. */
  const handleSectionSelection = useCallback(
    (sectionData: any) => {
      setPlanningData((prev) => {
        const current = prev.selectedItems?.[currentStepData.id];
        if (JSON.stringify(current) === JSON.stringify(sectionData)) return prev;
        return {
          ...prev,
          selectedItems: { ...prev.selectedItems, [currentStepData.id]: sectionData },
        };
      });
    },
    [currentStepData.id]
  );

  const isLastStep = currentStep === planningSteps.length - 1;
  const busy = isStarting || isLoadingStep || isSubmitting;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative">
      <AnimatePresence>
        {isStarting && (
          <PlanningProgress
            destination={planningData.destination}
            headline="Curating your experience"
          />
        )}
      </AnimatePresence>

      {/* Header with progress */}
      <motion.div
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
        className="fixed top-0 left-0 right-0 z-50 bg-black/20 backdrop-blur-xl border-b border-white/10"
      >
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between gap-4">
            <Button variant="ghost" onClick={handlePrevious} className="text-white hover:bg-white/10 shrink-0">
              <ArrowLeft className="w-4 h-4 mr-2" />
              {currentStep === 0 ? 'Back to Home' : 'Previous'}
            </Button>

            <StepRail
              steps={planningSteps}
              currentStep={currentStep}
              onSelect={(index) => {
                // Only completed steps are navigable; jumping forward would
                // skip the selections the later searches depend on.
                if (sessionId && index < currentStep) {
                  navigate(`/plan/${sessionId}/${stepIdByIndex(index)}`);
                }
              }}
            />

            <div className="text-white shrink-0">
              <span className="text-sm opacity-70">
                Step {currentStep + 1} of {planningSteps.length}
              </span>
            </div>
          </div>

          <motion.h1
            key={currentStep}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
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
            key={currentStep}
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -40 }}
            transition={{ duration: 0.35, ease: 'easeInOut' }}
            className="container mx-auto px-6"
          >
            {stepError ? (
              <div className="max-w-lg mx-auto text-center bg-white/5 border border-white/10 rounded-2xl p-10">
                <h2 className="text-xl text-white mb-3">Something went wrong</h2>
                <p className="text-white/70 mb-8">{stepError}</p>
                <div className="flex items-center justify-center gap-3">
                  <Button onClick={handleRetry} className="bg-blue-600 hover:bg-blue-700 text-white">
                    <RotateCcw className="w-4 h-4 mr-2" />
                    Try again
                  </Button>
                  <Button variant="ghost" onClick={() => navigate('/plan')} className="text-white hover:bg-white/10">
                    Start over
                  </Button>
                </div>
              </div>
            ) : isLoadingStep ? (
              <PlanningProgress
                inline
                destination={planningData.destination}
                headline={STEP_LOADING_COPY[currentStepData.id] || 'Working on it'}
              />
            ) : currentStepData.id === 'questionnaire' ? (
              <CurrentComponent
                onComplete={handleQuestionnaireComplete}
                onClose={() => navigate('/')}
                initialData={planningData}
              />
            ) : (
              <CurrentComponent
                planningData={planningData}
                onSelectionChange={handleSectionSelection}
                isTransitioning={busy}
              />
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Footer navigation — hidden on the questionnaire, which has its own CTA */}
      {currentStepData.id !== 'questionnaire' && !stepError && (
        <motion.div
          initial={{ y: 100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.6, ease: 'easeOut', delay: 0.2 }}
          className="fixed bottom-0 left-0 right-0 z-50 bg-black/20 backdrop-blur-xl border-t border-white/10"
        >
          <div className="container mx-auto px-6 py-4">
            <div className="flex justify-between items-center">
              <div className="text-white/70 text-sm">Choose the options that appeal to you most</div>
              <Button onClick={handleNext} className="bg-blue-600 hover:bg-blue-700 text-white" disabled={busy}>
                {isSubmitting ? 'Saving…' : isLastStep ? 'Complete Planning' : 'Next Section'}
                {!isSubmitting && !isLastStep && <ChevronRight className="w-4 h-4 ml-2" />}
                {!isSubmitting && isLastStep && <Check className="w-4 h-4 ml-2" />}
              </Button>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
