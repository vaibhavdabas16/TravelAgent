import { useEffect, useRef } from 'react';
import L from 'leaflet';
import type { TripDay, TripHotel } from '../../lib/trip-model';

interface MapPanelProps {
  day: TripDay | null;
  hotels: TripHotel[];
  activeStopId: string | null;
  onSelectStop: (id: string) => void;
  className?: string;
}

const TILE_URL = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
const ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

/**
 * Numbered stops for the selected day, the hotel, and the route between
 * them. Selecting a marker selects the itinerary item and vice versa. Stops
 * without coordinates are simply not drawn.
 */
export function MapPanel({ day, hotels, activeStopId, onSelectStop, className = '' }: MapPanelProps) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const layer = useRef<L.LayerGroup | null>(null);
  const markers = useRef<Map<string, L.Marker>>(new Map());
  const onSelectRef = useRef(onSelectStop);
  onSelectRef.current = onSelectStop;

  useEffect(() => {
    if (!container.current || map.current) return;
    const m = L.map(container.current, {
      zoomControl: false,
      attributionControl: true,
      scrollWheelZoom: false,
    });
    L.control.zoom({ position: 'bottomright' }).addTo(m);
    L.tileLayer(TILE_URL, { attribution: ATTRIBUTION, maxZoom: 19 }).addTo(m);
    m.setView([20, 0], 2);
    layer.current = L.layerGroup().addTo(m);
    map.current = m;
    return () => {
      m.remove();
      map.current = null;
      layer.current = null;
    };
  }, []);

  // Redraw when the day changes.
  useEffect(() => {
    const m = map.current;
    const g = layer.current;
    if (!m || !g) return;
    g.clearLayers();
    markers.current.clear();

    const points: L.LatLngExpression[] = [];
    const stops = day?.stops.filter((s) => s.coords) ?? [];

    for (const s of stops) {
      const icon = L.divIcon({
        className: '',
        html: `<div class="stop-marker" data-stop="${s.id}" role="button" aria-label="Stop ${s.index}: ${escapeHtml(s.name)}">${s.index}</div>`,
        iconSize: [22, 22],
        iconAnchor: [11, 11],
      });
      const mk = L.marker([s.coords!.lat, s.coords!.lng], { icon, keyboard: true, title: s.name }).addTo(g);
      mk.on('click', () => onSelectRef.current(s.id));
      markers.current.set(s.id, mk);
      points.push([s.coords!.lat, s.coords!.lng]);
    }

    if (points.length > 1) {
      const accent = getComputedStyle(document.documentElement).getPropertyValue('--color-accent').trim();
      L.polyline(points, { color: accent, weight: 2.5, opacity: 0.8, dashArray: '2 6', lineCap: 'round' }).addTo(g);
    }

    for (const h of hotels) {
      if (!h.coords) continue;
      const icon = L.divIcon({
        className: '',
        html: `<div class="stop-marker is-hotel" aria-label="Hotel: ${escapeHtml(h.name)}" title="${escapeHtml(h.name)}">H</div>`,
        iconSize: [22, 22],
        iconAnchor: [11, 11],
      });
      L.marker([h.coords.lat, h.coords.lng], { icon, title: h.name }).addTo(g);
      points.push([h.coords.lat, h.coords.lng]);
    }

    if (points.length) {
      const bounds = L.latLngBounds(points);
      m.fitBounds(bounds.pad(0.25), { maxZoom: 15, animate: false });
    }
    // Container may have been hidden (mobile sheet) when the map was created.
    setTimeout(() => m.invalidateSize(), 50);
  }, [day, hotels]);

  // Highlight the active stop.
  useEffect(() => {
    markers.current.forEach((mk, id) => {
      const el = mk.getElement()?.querySelector('.stop-marker');
      if (!el) return;
      el.classList.toggle('is-active', id === activeStopId);
      if (id === activeStopId) mk.setZIndexOffset(1000);
      else mk.setZIndexOffset(0);
    });
    if (activeStopId && map.current) {
      const mk = markers.current.get(activeStopId);
      if (mk && !map.current.getBounds().contains(mk.getLatLng())) {
        map.current.panTo(mk.getLatLng(), { animate: true });
      }
    }
  }, [activeStopId]);

  // Keep the map correct when its container resizes (tab switch, sheet open).
  useEffect(() => {
    const el = container.current;
    const m = map.current;
    if (!el || !m || typeof ResizeObserver === 'undefined') return;
    const ro = new ResizeObserver(() => m.invalidateSize());
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const hasPoints = (day?.stops.some((s) => s.coords) ?? false) || hotels.some((h) => h.coords);

  return (
    <div className={`relative overflow-hidden rounded-md border border-rule bg-paper-2 ${className}`}>
      <div ref={container} className="h-full w-full" aria-label="Map of today's stops" role="region" />
      {!hasPoints && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center p-6 text-center text-[13px] text-muted">
          No map positions came back for these stops.
        </div>
      )}
    </div>
  );
}

function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c] as string);
}
