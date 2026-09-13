import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { toast } from 'sonner';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { Footer } from '../components/shared/Footer';
import { api } from '../services/api';
import { Navbar } from '../components/shared/Navbar';
import type { Command } from '../components/shared/CommandPalette';
import { TripPrompt } from '../components/planning/TripPrompt';
import { TripBrief } from '../components/planning/TripBrief';
import { SelectionStep } from '../components/planning/SelectionStep';
import { StepRail } from '../components/planning/StepRail';
import { PlanningProgress, type ProgressStage } from '../components/planning/PlanningProgress';
import { ErrorState } from '../components/shared/States';
import { Note } from '../components/shared/Agent';
import { planningSteps, stepIdByIndex, stepIndexById } from '../lib/planning-steps';
import {
  type PlanningData,
  emptyPlanningData,
  loadPlanningData,
  savePlanningData,
  saveTrip,
} from '../lib/planning-storage';

/**
 * The planner. Step 0 is the brief (no session yet); every later step is
 * addressable at /plan/:sessionId/:stepId so a refresh or back button lands
 * where you were. Each step's search runs when the step is entered and is
 * cached on the planning data, so revisiting never re-bills the providers.
 */
export function PlanPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { sessionId, stepId } = useParams<{ sessionId?: string; stepId?: string }>();

  const currentStep = sessionId ? stepIndexById(stepId) : 0;
  const step = planningSteps[currentStep];
  const isBrief = step.id === 'brief';

  const [planningData, setPlanningData] = useState<PlanningData>(() => {
    if (sessionId) {
      const restored = loadPlanningData(sessionId);
      if (restored) return { ...restored, sessionId };
      return emptyPlanningData({ sessionId });
    }
    const fromLink = new URLSearchParams(location.search).get('q') ?? '';
    return emptyPlanningData({ query: (location.state as any)?.query ?? fromLink });
  });

  const [isStarting, setIsStarting] = useState(false);
  const [isLoadingStep, setIsLoadingStep] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [stepError, setStepError] = useState<string | null>(null);
  const [generationStages, setGenerationStages] = useState<ProgressStage[] | null>(null);

  // Guards against a step's fetch firing twice under StrictMode double-effects.
  const inFlightStep = useRef<string | null>(null);

  useEffect(() => {
    const activeId = sessionId ?? planningData.sessionId;
    if (activeId) savePlanningData(activeId, planningData);
  }, [planningData, sessionId]);

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [currentStep]);

  /** Fetch the data a step needs, unless we already have it. */
  const loadStepData = useCallback(
    async (targetStepId: string, sid: string, data: PlanningData) => {
      const target = planningSteps.find((s) => s.id === targetStepId);
      const dataKey = target?.dataKey;
      if (!dataKey) return;

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
            patch = { pois: res.pois || [], summaries: { ...data.summaries, places: res.summary } };
            break;
          }
          case 'accommodations': {
            const res = await api.searchAccommodations(sid);
            patch = { recommended_hotels: res.hotels || [], summaries: { ...data.summaries, accommodations: res.summary } };
            break;
          }
          case 'dining': {
            const res = await api.searchDining(sid);
            patch = { dining: res.restaurants || [], summaries: { ...data.summaries, dining: res.summary } };
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
            patch = { activities: res.activities || [], summaries: { ...data.summaries, activities: res.summary } };
            break;
          }
          case 'shopping': {
            const res = await api.searchShopping(sid);
            patch = { shopping: res.shopping || [], summaries: { ...data.summaries, shopping: res.summary } };
            break;
          }
          case 'wellness': {
            const res = await api.searchWellness(sid);
            patch = { wellness: res.wellness_options || [], summaries: { ...data.summaries, wellness: res.summary } };
            break;
          }
        }
        setPlanningData((prev) => ({ ...prev, ...patch }));
      } catch (error: any) {
        setStepError(
          error?.response?.status === 404
            ? 'This planning session has expired on the server. Start a new trip to continue.'
            : `We could not load ${target?.name.toLowerCase()}. The provider may be busy — try again in a moment.`
        );
      } finally {
        setIsLoadingStep(false);
        inFlightStep.current = null;
      }
    },
    []
  );

  useEffect(() => {
    if (!sessionId || isBrief) return;
    loadStepData(step.id, sessionId, planningData);
    // planningData intentionally excluded: loadStepData reads the latest via
    // closure on each entry; including it would refetch on every selection.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId, step.id]);

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

  const generateItinerary = async (sid: string) => {
    setGenerationStages([]);
    const itinerary = await api.streamItinerary(sid, (event) => {
      if (event.type === 'stages' && event.stages) {
        setGenerationStages(event.stages.map((s) => ({ id: s.id, label: s.label, status: 'pending' as const })));
      } else if (event.type === 'stage' && event.stage) {
        setGenerationStages((prev) =>
          (prev ?? []).map((s) =>
            s.id === event.stage ? { ...s, status: event.status === 'done' ? 'done' : 'active' } : s
          )
        );
      }
    });
    if (itinerary?.error) throw new Error(itinerary.error);
    const trip = { ...planningData, ...itinerary };
    saveTrip(sid, trip);
    navigate(`/trip/${sid}`, { state: { tripData: trip } });
  };

  const advance = async (buildNow: boolean) => {
    if (isSubmitting || isLoadingStep || !sessionId) return;
    setIsSubmitting(true);
    setStepError(null);
    try {
      await submitSelections(step.id, sessionId);
      if (!buildNow && currentStep < planningSteps.length - 1) {
        navigate(`/plan/${sessionId}/${stepIdByIndex(currentStep + 1)}`);
      } else {
        await generateItinerary(sessionId);
      }
    } catch (error: any) {
      setGenerationStages(null);
      const detail =
        error?.response?.status === 404
          ? 'This planning session has expired on the server. Start a new trip to continue.'
          : error?.message === 'No items selected'
            ? 'Pick at least one place before building the itinerary.'
            : 'We could not save that step. Please try again.';
      setStepError(detail);
      toast.error(detail);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1 && sessionId) navigate(`/plan/${sessionId}/${stepIdByIndex(currentStep - 1)}`);
    else navigate('/plan');
  };

  const handleRetry = () => {
    if (!sessionId) return;
    setStepError(null);
    const dataKey = step.dataKey;
    if (dataKey) {
      setPlanningData((prev) => ({ ...prev, [dataKey]: undefined }));
      loadStepData(step.id, sessionId, { ...planningData, [dataKey]: undefined });
    }
  };

  /** Brief confirmed: open the session, then hand off to the URL. */
  const handleBriefContinue = useCallback(
    async (request: any) => {
      if (isStarting) return;
      const merged: PlanningData = {
        ...planningData,
        ...request,
        tripStyle: request.tripStyle || 'balanced',
      };
      setPlanningData(merged);
      setIsStarting(true);
      setStepError(null);
      try {
        const startResponse = await api.startPlanning(request);
        const newSessionId = startResponse.session_id;
        const withSession: PlanningData = { ...merged, sessionId: newSessionId };
        savePlanningData(newSessionId, withSession);
        setPlanningData(withSession);
        navigate(`/plan/${newSessionId}/places`, { replace: true });
      } catch {
        setStepError('We could not start your planning session. Check the backend is running and try again.');
      } finally {
        setIsStarting(false);
      }
    },
    [planningData, isStarting, navigate]
  );

  const handleSelection = useCallback(
    (ids: string[]) => {
      setPlanningData((prev) => {
        const current = prev.selectedItems?.[step.id];
        if (JSON.stringify(current) === JSON.stringify(ids)) return prev;
        return { ...prev, selectedItems: { ...prev.selectedItems, [step.id]: ids } };
      });
    },
    [step.id]
  );

  const isLast = currentStep === planningSteps.length - 1;
  const busy = isStarting || isLoadingStep || isSubmitting;
  const selectedCount = (planningData.selectedItems?.[step.id] ?? []).length;
  const canBuildNow = currentStep >= 2; // places have been chosen

  // ⌘K: completed steps are jumpable; the build action when it is allowed.
  const stepCommands: Command[] = [
    ...planningSteps
      .slice(1, currentStep)
      .map((s) => ({ id: `step-${s.id}`, label: s.name, hint: 'back to step', group: 'This trip', run: () => navigate(`/plan/${sessionId}/${s.id}`) })),
    ...(canBuildNow ? [{ id: 'build', label: 'Build itinerary now', hint: 'with what is selected', group: 'This trip', run: () => advance(true) }] : []),
  ];

  // What the agent did on this step: the API's own summary when it sent one,
  // otherwise the count and the brief it ranked against. Never invented.
  const agentLine = (() => {
    const summary = planningData.summaries?.[step.id];
    if (typeof summary === 'string' && summary.trim() && summary.length < 320 && !/error/i.test(summary)) {
      return summary.replace(/\s*\(score:[^)]*\)/g, '').trim();
    }
    const key = step.dataKey;
    const v = key ? (planningData as any)[key] : null;
    const count = Array.isArray(v) ? v.length : 0;
    if (!count) return null;
    const against = [
      planningData.interests?.length ? planningData.interests.join(', ') : null,
      planningData.budget ? `${planningData.budget} budget` : null,
    ]
      .filter(Boolean)
      .join(' · ');
    return `${count} results for ${planningData.destination}${against ? `, ranked against ${against}` : ''}.`;
  })();

  // ---- Brief (no session) -------------------------------------------------
  if (isBrief) {
    return (
      <div className="flex min-h-screen flex-col bg-paper">
        <Navbar />
        {isStarting && <PlanningProgress headline="Setting up your trip" destination={planningData.destination} />}
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-6 sm:py-14">
          {stepError && (
            <div className="mx-auto mb-6 max-w-2xl">
              <ErrorState title="We could not start planning" body={stepError} onRetry={() => setStepError(null)} />
            </div>
          )}
          {planningData.query ? (
            <TripBrief
              key={planningData.query}
              query={planningData.query}
              busy={isStarting}
              onChangeQuery={(q) => setPlanningData((p) => ({ ...p, query: q }))}
              onContinue={handleBriefContinue}
            />
          ) : (
            <div className="mx-auto max-w-2xl">
              <h1 className="lc text-[length:var(--text-xl)]">Where to?</h1>
              <p className="mt-1 text-[13px] text-muted">Destination, dates, who is going, what you like.</p>
              <div className="mt-5">
                <TripPrompt autoFocus onSubmit={(q) => setPlanningData((p) => ({ ...p, query: q }))} />
              </div>
            </div>
          )}
        </main>
        <Footer />
      </div>
    );
  }

  // ---- Selection steps ----------------------------------------------------
  return (
    <div className="min-h-screen bg-paper pb-24">
      {generationStages && (
        <PlanningProgress headline="Building your itinerary" destination={planningData.destination} stages={generationStages} />
      )}

      <Navbar
        commands={stepCommands}
        context={
          <div className="flex items-center gap-2">
            <button onClick={handlePrevious} className="btn btn-ghost btn-icon" aria-label="Back">
              <ArrowLeft className="h-4 w-4" />
            </button>
            <StepRail
              steps={planningSteps}
              currentStep={currentStep}
              onSelect={(index) => {
                if (sessionId && index < currentStep) navigate(`/plan/${sessionId}/${stepIdByIndex(index)}`);
              }}
            />
          </div>
        }
      />

      <main className="mx-auto max-w-6xl px-4 pt-8 sm:px-6">
        <div className="mb-5">
          <p className="label">{planningData.destination}</p>
          <h1 className="lc mt-1 text-[length:var(--text-xl)]">{step.name}</h1>
          {step.intro && <p className="mt-1 max-w-2xl text-[13px] text-muted">{step.intro}</p>}
        </div>
        {!stepError && !isLoadingStep && agentLine && <Note className="mb-4">{agentLine}</Note>}

        {stepError ? (
          <ErrorState title="That did not work" body={stepError} onRetry={handleRetry} secondary={{ label: 'Start a new trip', to: '/plan' }} />
        ) : isLoadingStep ? (
          <PlanningProgress inline headline={step.loadingCopy ?? 'Working on it'} destination={planningData.destination} />
        ) : (
          <SelectionStep key={step.id} stepId={step.id} planningData={planningData} onSelectionChange={handleSelection} />
        )}
      </main>

      {!stepError && (
        <footer className="fixed inset-x-0 bottom-0 z-40 border-t border-rule bg-paper">
          <div className="mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 px-4 sm:px-6">
            <p className="text-[13px] text-muted">
              {selectedCount > 0 ? `${selectedCount} selected` : step.optional ? 'Nothing selected. That is fine.' : 'Select at least one.'}
            </p>
            <div className="flex items-center gap-1">
              {canBuildNow && !isLast && (
                <button onClick={() => advance(true)} disabled={busy} className="btn btn-ghost hidden sm:inline-flex">
                  Build itinerary now
                </button>
              )}
              <button onClick={() => advance(false)} disabled={busy || (!step.optional && selectedCount === 0)} className="btn btn-primary">
                {isSubmitting ? 'Saving…' : isLast ? 'Build itinerary' : selectedCount === 0 && step.optional ? 'Skip' : 'Continue'}
                {!isSubmitting && <ArrowRight className="h-3.5 w-3.5" />}
              </button>
            </div>
          </div>
        </footer>
      )}
    </div>
  );
}
