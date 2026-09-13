/**
 * The wizard's step order, shared by the router and the flow so URL slugs
 * and step indices cannot drift apart. The order matters to the backend: each
 * search uses the selections made before it (hotels are searched around the
 * places you picked, flights are checked against the hotel, and so on).
 */
export interface PlanningStep {
  id: string;
  /** Heading shown on the step. */
  name: string;
  /** Short label for the progress rail. */
  shortName: string;
  /** One line under the heading. */
  intro: string;
  /** Field on PlanningData that holds this step's results. */
  dataKey?: string;
  /** Line shown while this step's data is being fetched. */
  loadingCopy?: string;
  /** Steps the user can pass through without choosing anything. */
  optional?: boolean;
}

export const planningSteps: PlanningStep[] = [
  {
    id: 'brief',
    name: 'Your trip',
    shortName: 'Trip',
    intro: '',
  },
  {
    id: 'places',
    name: 'Places worth your time',
    shortName: 'Places',
    intro: 'Ranked for your brief. Keep the ones you want in the plan — everything else is built around them.',
    dataKey: 'pois',
    loadingCopy: 'Finding places worth visiting',
  },
  {
    id: 'accommodations',
    name: 'Where to stay',
    shortName: 'Stay',
    intro: 'Live offers, ranked partly on how close they sit to the places you picked.',
    dataKey: 'recommended_hotels',
    loadingCopy: 'Finding the best stay',
  },
  {
    id: 'dining',
    name: 'Where to eat',
    shortName: 'Food',
    intro: 'Restaurants and cafés that fit the trip. Pick a few; we slot them into the right days.',
    dataKey: 'dining',
    loadingCopy: 'Looking for places to eat',
    optional: true,
  },
  {
    id: 'transportation',
    name: 'Getting there and around',
    shortName: 'Transport',
    intro: 'Flights if you told us where you are starting from, plus how best to move around once you arrive.',
    dataKey: 'recommended_flights',
    loadingCopy: 'Checking flights and local transport',
    optional: true,
  },
  {
    id: 'activities',
    name: 'Things to do',
    shortName: 'Activities',
    intro: 'Experiences and activities matched to your interests.',
    dataKey: 'activities',
    loadingCopy: 'Rounding up things to do',
    optional: true,
  },
  {
    id: 'shopping',
    name: 'Markets and shopping',
    shortName: 'Shopping',
    intro: 'Skip this if shopping is not your thing.',
    dataKey: 'shopping',
    loadingCopy: 'Looking for markets and shops',
    optional: true,
  },
  {
    id: 'wellness',
    name: 'Rest and wellness',
    shortName: 'Wellness',
    intro: 'Spas, baths and quiet corners for the slower hours.',
    dataKey: 'wellness',
    loadingCopy: 'Finding somewhere to unwind',
    optional: true,
  },
];

export function stepIndexById(stepId: string | undefined): number {
  if (!stepId) return 0;
  const index = planningSteps.findIndex((s) => s.id === stepId);
  return index === -1 ? 0 : index;
}

export function stepIdByIndex(index: number): string {
  return planningSteps[Math.min(Math.max(index, 0), planningSteps.length - 1)].id;
}
