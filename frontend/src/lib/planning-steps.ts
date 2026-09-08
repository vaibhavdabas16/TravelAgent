/**
 * The wizard's step order, shared by the router and the flow component so that
 * URL slugs and step indices can never drift apart.
 */
import { PlacesToVisitSection } from '../components/planning-sections/places-to-visit';
import { AccommodationsSection } from '../components/planning-sections/accommodations';
import { DiningSection } from '../components/planning-sections/dining';
import { TransportationSection } from '../components/planning-sections/transportation';
import { ActivitiesSection } from '../components/planning-sections/activities';
import { ShoppingSection } from '../components/planning-sections/shopping';
import { WellnessSection } from '../components/planning-sections/wellness';
import { PlanningInterface } from '../components/planning-interface';

export interface PlanningStep {
  id: string;
  name: string;
  /** Short label for the compact progress rail. */
  shortName: string;
  component: any;
}

export const planningSteps: PlanningStep[] = [
  { id: 'questionnaire', name: 'Tell Us About Your Trip', shortName: 'Trip', component: PlanningInterface },
  { id: 'places', name: 'Places to Visit', shortName: 'Places', component: PlacesToVisitSection },
  { id: 'accommodations', name: 'Accommodations', shortName: 'Stay', component: AccommodationsSection },
  { id: 'dining', name: 'Dining', shortName: 'Dining', component: DiningSection },
  { id: 'transportation', name: 'Transportation', shortName: 'Transport', component: TransportationSection },
  { id: 'activities', name: 'Activities & Adventures', shortName: 'Activities', component: ActivitiesSection },
  { id: 'shopping', name: 'Shopping & Markets', shortName: 'Shopping', component: ShoppingSection },
  { id: 'wellness', name: 'Wellness & Relaxation', shortName: 'Wellness', component: WellnessSection },
];

export function stepIndexById(stepId: string | undefined): number {
  if (!stepId) return 0;
  const index = planningSteps.findIndex((s) => s.id === stepId);
  return index === -1 ? 0 : index;
}

export function stepIdByIndex(index: number): string {
  return planningSteps[Math.min(Math.max(index, 0), planningSteps.length - 1)].id;
}
