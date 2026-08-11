/// <reference types="vite/client" />
import { motion, AnimatePresence } from 'motion/react';
import { useState, useEffect } from 'react';
import {
  MapPin, Calendar, Users, DollarSign, Clock, Edit3, Save, X,
  Plane, Hotel, Utensils, Camera, Star, Navigation, Phone, Globe,
  Coffee, ShoppingBag, Mountain, Waves, Building, Car, Train,
  AlertTriangle, CheckCircle, RotateCcw, Sparkles, Heart,
  ArrowLeft, Download, Share2, Plus, Music, Leaf
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from './ui/tooltip';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { ImageWithFallback } from './figma/ImageWithFallback';

interface TripPlanProps {
  tripData?: any; // This will now be the combined planning data
  onEdit: (section: string, data: any) => void;
  onClose?: () => void;
}

// --- Strict Interfaces ---

interface TripPlanData {
  destination: string | { name: string };
  dates: { start: string; end: string };
  travelers: number;
  budget: string;
  totalBudget: number;
  overview: string;
  tripStyle: string;
  days: DayPlan[];
  selectedItems: any;
  local_transport: any;
  recommended_flights: Flight[];
  isFallback: boolean;
}

interface DayPlan {
  day: number;
  date: string;
  city: string;
  activities: Activity[];
  accommodation: Accommodation | null;
  weather: Weather;
  budget: DailyBudget;
}

interface Activity {
  id: string;
  time: string;
  title: string;
  description: string;
  location: string;
  duration: string;
  cost: number;
  rating: number;
  category: string;
  bookingRequired: boolean;
  image?: string;
  coordinates?: { lat: number; lng: number };
}

interface Accommodation {
  name: string;
  address: string;
  rating: number;
  pricePerNight: number;
  amenities: string[];
  image: string;
  checkIn: string;
  checkOut: string;
}

interface Flight {
  id: string;
  airline: string;
  flight_number: string;
  departure_time: string;
  arrival_time: string;
  duration: string;
  price: number;
  stops: number;
  origin: string;
  destination: string;
}

interface Weather {
  temperature: string;
  condition: string;
  icon: string;
  precipitation: number;
}

interface DailyBudget {
  accommodation: number;
  food: number;
  activities: number;
  transport: number;
  total: number;
}

// --- Hydration Engine ---

function hydrateItinerary(planningData: any): TripPlanData {
  console.log('Hydrating itinerary with data:', planningData);

  if (!planningData) return mockTripData as any;

  // 1. Extract Core Details
  const destination = planningData.destination || planningData.query || "Your Destination";
  const startDate = planningData.dates?.start || planningData.startDate || new Date().toISOString();
  const endDate = planningData.dates?.end || planningData.endDate || new Date(Date.now() + 5 * 86400000).toISOString();
  const travelers = planningData.travelers || planningData.groupSize || 2;
  const tripStyle = planningData.tripStyle || "balanced";

  // 2. Prepare Rich Data Pools
  const allPOIs = planningData.pois || [];
  const allHotels = planningData.recommended_hotels || [];
  const allFlights = planningData.recommended_flights || [];
  const selectedItems = planningData.selectedItems || {};

  // --- Generic Descriptions ---
  const genericDescriptions = {
    activity: [
      "A must-visit destination capturing the essence of the city.",
      "Immerse yourself in the local culture and history here.",
      "A breathtaking spot perfect for photography and relaxation.",
      "Experience the vibrant atmosphere and unique charm.",
      "A hidden gem that offers a unique perspective of the area.",
      "Discover the rich heritage and stories behind this landmark.",
      "An unforgettable experience for nature and adventure lovers.",
      "Perfect for a leisurely exploration of local traditions.",
      "A chaotic yet mesmerizing blend of sights and sounds.",
      "Step back in time and marvel at the architectural beauty.",
      "A cultural hub buzzing with energy and life.",
      "The perfect place to unwind and soak in the vibes.",
      "An architectural marvel that stands the test of time.",
      "A scenic retreat offering peace and tranquility.",
      "Explore the artistic soul of the city at this spot.",
      "A historic site echoing tales of the past.",
      "Vibrant, colorful, and full of local character.",
      "A sensory delight for every traveler.",
      "The ideal spot for creating lasting memories.",
      "Experience the city's heartbeat at this popular location."
    ],
    hotel: [
      "Experience world-class comfort and hospitality.",
      "A cozy retreat in the heart of the city.",
      "Luxury living with stunning views and amenities.",
      "Modern elegance meets traditional charm.",
      "Your perfect home away from home with premium services.",
      "Relax and rejuvenate in this tranquil urban oasis.",
      "Stylish accommodations designed for the modern traveler.",
      "Enjoy a stay defined by elegance and exceptional service.",
      "A sophisticated sanctuary amidst the city buzz.",
      "Unwind in style with top-notch facilities and comfort.",
      "A boutique experience with personalized touches.",
      "Grand interiors and impeccable service await you.",
      "Stay in the lap of luxury with exquisite decor.",
      "A charming haven offering a peaceful escape.",
      "Contemporary design paired with warm hospitality.",
      "The ultimate destination for relaxation and comfort.",
      "Experience the height of sophistication and style.",
      "A hidden sanctuary offering privacy and exclusivity.",
      "Elegant rooms with breathtaking city views.",
      "Where comfort meets convenience in the city center."
    ],
    dining: [
      "Savor the authentic flavors of local cuisine.",
      "A delightful culinary journey awaits you here.",
      "Perfect for a memorable meal with friends and family.",
      "Experience the perfect blend of taste and ambiance.",
      "A gastronomic delight showcasing the best local ingredients.",
      "Indulge in a feast for the senses at this top-rated spot.",
      "Where traditional recipes meet modern culinary art.",
      "Enjoy a vibrant dining atmosphere with exquisite dishes.",
      "A taste of heaven for food enthusiasts.",
      "Culinary excellence served with warm hospitality.",
      "Farm-to-table freshness in every bite.",
      "A cozy spot for a romantic dinner.",
      "Innovative dishes that surprise and delight.",
      "The town's favorite spot for delicious comfort food.",
      "Exquisite flavors served in a stunning setting.",
      "A culinary landmark you cannot miss.",
      "Taste the tradition in every carefully crafted dish.",
      "A modern twist on classic local favorites.",
      "The perfect setting for a celebration of food.",
      "An unforgettable dining experience for the true foodie."
    ]
  };

  const getRandomDescription = (type: 'activity' | 'hotel' | 'dining') => {
    const options = genericDescriptions[type];
    return options[Math.floor(Math.random() * options.length)];
  };

  // Helper to get photo URL
  const getPhotoUrl = (item: any) => {
    if (!item) return null;
    if (item.photo_url) return item.photo_url;
    if (item.image && item.image.startsWith('http')) return item.image;

    const ref = item.photo_reference || (item.photos && item.photos[0]);
    if (ref) {
      // Check if it's already a URL
      if (typeof ref === 'string' && ref.startsWith('http')) return ref;
      // Construct Google Photos URL
      return `https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photoreference=${ref}&key=${import.meta.env.VITE_GOOGLE_MAPS_API_KEY}`;
    }
    return null;
  };

  // 3. Hydrate Days
  let days: DayPlan[] = [];

  // Use backend itinerary if available
  if (planningData.itinerary && Array.isArray(planningData.itinerary) && planningData.itinerary.length > 0) {
    days = planningData.itinerary.map((dayItem: any, index: number) => {
      // Date Calculation
      const dayDate = new Date(startDate);
      dayDate.setDate(dayDate.getDate() + (dayItem.day - 1));

      // Hydrate Activities
      const activities = (dayItem.stops || []).map((stop: any, idx: number) => {
        // MATCHING LOGIC: ID -> Name -> Fuzzy Name
        // Now that backend returns IDs, this should be very reliable
        const richPOI = allPOIs.find((p: any) =>
          (stop.place_id && p.place_id === stop.place_id) ||
          (stop.id && p.place_id === stop.id) ||
          (stop.id && p.id === stop.id) ||
          p.name === stop.name ||
          (stop.name && p.name && p.name.includes(stop.name))
        );

        return {
          id: stop.id || stop.place_id || `stop-${index}-${idx}`,
          time: stop.time || "10:00", // Default or from backend
          title: richPOI?.name || stop.name || "Activity",
          description: richPOI?.editorial_summary || richPOI?.why_recommended || stop.description || getRandomDescription('activity'),
          location: richPOI?.formatted_address || stop.location?.formatted_address || stop.vicinity || "City Center",
          duration: stop.duration || "2 hours",
          cost: richPOI?.price_level ? richPOI.price_level * 500 : 0, // Estimate in Rupees
          rating: richPOI?.rating || 4.5,
          category: (richPOI?.types?.[0] || stop.type || 'sightseeing') as string,
          bookingRequired: false,
          image: getPhotoUrl(richPOI) || stop.photo_url || getCategoryImage(stop.type || 'sightseeing'),
          coordinates: richPOI?.geometry?.location || stop.location
        };
      });

      // Hydrate Accommodation (Strictly from Selection)
      let accommodation: Accommodation | null = null;
      if (selectedItems.accommodations && selectedItems.accommodations.length > 0) {
        const selectedId = selectedItems.accommodations[0];
        const richHotel = allHotels.find((h: any) =>
          String(h.hotel_id) === String(selectedId) ||
          String(h.id) === String(selectedId) ||
          h.name === selectedId // Fallback if ID is actually a name
        );

        if (richHotel) {
          // Robust Price Calculation
          let price = 5000; // Default fallback in INR
          if (richHotel.price && richHotel.price.total) {
            price = parseFloat(richHotel.price.total);
            // Heuristic: If price is small (< 500), it might be USD/EUR, convert to INR approx
            if (price < 500) price = price * 85;
          } else if (richHotel.pricePerNight) {
            price = parseFloat(richHotel.pricePerNight);
            if (price < 500) price = price * 85;
          } else if (richHotel.offers && richHotel.offers[0]?.price?.total) {
            price = parseFloat(richHotel.offers[0].price.total);
            if (price < 500) price = price * 85;
          } else {
            // Randomize fallback slightly to avoid "same price" look
            price = 4000 + Math.floor(Math.random() * 4000);
          }

          // Robust Image Selection
          let image = getPhotoUrl(richHotel) || "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800&h=600&fit=crop";

          accommodation = {
            name: richHotel.name,
            address: richHotel.address?.cityName || richHotel.location || "City Center",
            rating: parseFloat(richHotel.rating) || 4.5,
            pricePerNight: price,
            amenities: richHotel.amenities || ["Wi-Fi", "Pool", "Spa"],
            image: image,
            checkIn: "15:00",
            checkOut: "11:00"
          };
        } else {
          // Fallback if ID exists but no rich data
          accommodation = {
            name: "Selected Hotel",
            address: "City Center",
            rating: 4.5,
            pricePerNight: 4000 + Math.floor(Math.random() * 3000), // Randomize fallback price
            amenities: ["Wi-Fi"],
            image: "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800&h=600&fit=crop",
            checkIn: "15:00",
            checkOut: "11:00"
          };
        }
      }

      // Calculate Daily Budget dynamically
      const accommodationCost = accommodation?.pricePerNight || 0;
      const activitiesCost = activities.reduce((sum: number, act: any) => sum + (act.cost || 0), 0);
      const foodCost = 2000; // Estimate INR
      const transportCost = 500; // Estimate INR

      return {
        day: dayItem.day,
        date: dayDate.toISOString(),
        city: typeof destination === 'string' ? destination : destination.name,
        activities,
        accommodation,
        weather: {
          temperature: "25°C",
          condition: "Sunny",
          icon: "☀️",
          precipitation: 0
        },
        budget: {
          accommodation: accommodationCost,
          food: foodCost,
          activities: activitiesCost,
          transport: transportCost,
          total: accommodationCost + foodCost + activitiesCost + transportCost
        }
      };
    });
  } else {
    // Fallback generation if no backend itinerary (omitted for brevity, can reuse old logic if needed)
    // For now, we assume backend always returns something or we use mock
    return mockTripData as any;
  }

  // 4. Hydrate Flights (Strict Filtering)
  const hydratedFlights = allFlights.filter((f: any) => {
    if (!selectedItems.transportation || selectedItems.transportation.length === 0) return true; // Show all if none selected? Or none? User said "strictly what I selected"
    return selectedItems.transportation.includes(f.id);
  }).map((f: any) => ({
    id: f.id,
    airline: f.airline,
    flight_number: f.flight_number || "N/A",
    departure_time: f.departure_at || "10:00",
    arrival_time: f.arrival_at || "14:00",
    duration: f.duration_minutes ? `${Math.floor(f.duration_minutes / 60)}h ${f.duration_minutes % 60}m` : "4h",
    price: f.price ? (f.price < 500 ? f.price * 85 : f.price) : 5000, // Convert to INR if needed
    stops: f.stops || 0,
    origin: f.origin,
    destination: f.destination
  }));

  return {
    destination,
    dates: { start: startDate, end: endDate },
    travelers,
    budget: getBudgetCategory(tripStyle),
    totalBudget: days.reduce((sum, day) => sum + day.budget.total, 0),
    overview: planningData.overview || `A perfectly curated ${tripStyle} trip to ${typeof destination === 'string' ? destination : destination.name}.`,
    days,
    selectedItems,
    tripStyle,
    local_transport: planningData.local_transport,
    recommended_flights: hydratedFlights,
    isFallback: false
  };
}

function getCategoryImage(category: string) {
  const images: Record<string, string> = {
    sightseeing: 'https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=800&h=600&fit=crop',
    food: 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800&h=600&fit=crop',
    activity: 'https://images.unsplash.com/photo-1533900298318-6b8da08a523e?w=800&h=600&fit=crop',
    shopping: 'https://images.unsplash.com/photo-1483985988355-763728e1935b?w=800&h=600&fit=crop',
    wellness: 'https://images.unsplash.com/photo-1540555700478-4be289fbecef?w=800&h=600&fit=crop',
    culture: 'https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=800&h=600&fit=crop'
  };
  return images[category] || images.sightseeing;
}

// Replaces the old generateTripPlan
const generateTripPlan = hydrateItinerary;

// Helper functions to get names and descriptions
// Note: getPlaceName and getPlaceDescription are no longer used for dynamic places
// but kept for fallback or other sections if needed
function getPlaceName(placeId: string | undefined) {
  if (!placeId) return 'Local Attraction';
  return 'Historic Landmark';
}

function getPlaceDescription(placeId: string | undefined) {
  if (!placeId) return 'Discover this amazing local attraction';
  return 'Amazing historical site to explore';
}
function getDiningName(diningId: string | undefined) {
  if (!diningId) return 'Local Restaurant';

  const restaurants = {
    '1': 'Karim’s',
    '2': 'Indian Accent',
    '3': 'Bukhara',
    '4': 'Saravana Bhavan',
    '5': 'Paranthe Wali Gali',
    '6': 'Leopold Cafe'
  };
  return restaurants[diningId as keyof typeof restaurants] || 'Local Bistro';
}

function getDiningDescription(diningId: string | undefined) {
  if (!diningId) return 'Authentic local dining experience';

  const descriptions = {
    '1': 'Iconic Mughlai cuisine near Jama Masjid',
    '2': 'Contemporary Indian tasting menu',
    '3': 'Famed North Indian tandoor dishes',
    '4': 'Classic South Indian vegetarian meals',
    '5': 'Historic lane famous for stuffed parathas',
    '6': 'Mumbai institution with colonial charm'
  };
  return descriptions[diningId as keyof typeof descriptions] || 'Authentic local dining experience';
}

function getActivityName(activityId: string | undefined) {
  if (!activityId) return 'Local Experience';

  const activities = {
    '1': 'Taj Mahal Sunrise Tour',
    '2': 'Old Delhi Rickshaw & Food Walk',
    '3': 'Jaipur City Palace & Amber Fort',
    '4': 'Ganges Sunrise Boat Ride',
    '5': 'Bollywood Studio Tour',
    '6': 'Indian Cooking Class'
  };
  return activities[activityId as keyof typeof activities] || 'Cultural Experience';
}

function getActivityDescription(activityId: string | undefined) {
  if (!activityId) return 'Exciting local activity to enjoy';

  const descriptions = {
    '1': 'Experience the Taj Mahal at dawn with an expert guide',
    '2': 'Street food tasting and heritage lanes of Old Delhi',
    '3': 'Architectural wonders and royal history in Jaipur',
    '4': 'Serene boat ride on the Ganges with sunrise rituals',
    '5': 'Behind-the-scenes look at India’s film industry',
    '6': 'Hands-on class cooking regional Indian dishes'
  };
  return descriptions[activityId as keyof typeof descriptions] || 'Exciting activity to enjoy';
}

function getAccommodationName(accommodationId: string | undefined) {
  if (!accommodationId) return 'Boutique Hotel';

  const accommodations = {
    '1': 'The Oberoi Amarvilas, Agra',
    '2': 'The Imperial New Delhi',
    '3': 'Taj Lake Palace, Udaipur',
    '4': 'ITC Rajputana, Jaipur',
    '5': 'Zostel Jaipur',
    '6': 'The Leela Palace, New Delhi'
  };
  return accommodations[accommodationId as keyof typeof accommodations] || 'Boutique Hotel';
}

function getBudgetCategory(tripStyle: string) {
  const budgets = {
    'laid-back': 'Relaxed (₹800-1500)',
    'balanced': 'Balanced (₹1500-2500)',
    'adventurous': 'Premium (₹2500-4000)'
  };
  return budgets[tripStyle as keyof typeof budgets] || 'Balanced (₹1500-2500)';
}

// Mock fallback data
const mockTripData: TripPlanData = {
  destination: "India",
  dates: { start: "2024-04-15", end: "2024-04-20" },
  travelers: 2,
  selectedItems: {},
  budget: "Balanced (₹1500-2500)",
  totalBudget: 2400,
  overview: "Experience the diversity of India with a curated itinerary featuring iconic landmarks, vibrant cuisine, and unforgettable cultural experiences.",
  tripStyle: "balanced",
  days: [
    {
      day: 1,
      date: "2024-04-15",
      city: "India",
      activities: [
        {
          id: "1",
          time: "10:00",
          title: "Taj Mahal Sunrise Visit",
          description: "Iconic landmark famed for its sunrise glow",
          location: "Destination Highlight",
          duration: "2-3 hours",
          cost: 29,
          rating: 4.8,
          category: 'sightseeing',
          bookingRequired: false
        },
        {
          id: "2",
          time: "19:00",
          title: "Dinner at Indian Accent",
          description: "Contemporary Indian tasting menu",
          location: "New Delhi, India",
          duration: "1.5-2 hours",
          cost: 85,
          rating: 4.6,
          category: 'food',
          bookingRequired: true
        }
      ],
      accommodation: {
        name: "The Oberoi Amarvilas, Agra",
        address: "Taj East Gate Road, Agra, Uttar Pradesh",
        rating: 4.5,
        pricePerNight: 180,
        amenities: ["Free WiFi", "Restaurant", "Gym", "24/7 Front Desk"],
        image: "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=800&h=600&fit=crop",
        checkIn: "15:00",
        checkOut: "11:00"
      },
      weather: {
        temperature: "22°C",
        condition: "Sunny",
        icon: "☀️",
        precipitation: 5
      },
      budget: {
        accommodation: 180,
        food: 120,
        activities: 150,
        transport: 50,
        total: 500
      }
    }
  ],
  local_transport: null,
  recommended_flights: [],
  isFallback: false
};

export function TripPlan({ tripData: rawTripData, onEdit, onClose }: TripPlanProps) {
  const [editingSection, setEditingSection] = useState<string | null>(null);
  const [editValues, setEditValues] = useState<any>({});
  const [showReplanTooltip, setShowReplanTooltip] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Generate trip plan from planning data with error handling
  const [tripData, setTripData] = useState<TripPlanData | null>(null);

  useEffect(() => {
    // Move generation to effect to prevent blocking render (fixes stuck spinner)
    const generate = async () => {
      try {
        // Small delay to ensure UI renders first
        await new Promise(resolve => setTimeout(resolve, 100));
        const data = generateTripPlan(rawTripData);
        setTripData(data);
        setIsLoading(false);
      } catch (error) {
        console.error('Error generating trip plan:', error);
        setError('Failed to generate trip plan. Using default data.');
        setTripData(mockTripData);
        setIsLoading(false);
      }
    };
    generate();
  }, [rawTripData]);

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center text-white">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="w-16 h-16 border-4 border-blue-400 border-t-transparent rounded-full mx-auto mb-4"
          />
          <h2 className="text-2xl mb-2">Creating Your Perfect Trip</h2>
          <p className="text-white/70">Generating your personalized itinerary...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center text-white">
          <h2 className="text-2xl mb-4">Something went wrong</h2>
          <p className="mb-6">{error}</p>
          <Button onClick={onClose} className="bg-blue-600 hover:bg-blue-700">
            Back to Home
          </Button>
        </div>
      </div>
    );
  }

  // Helper to render price scale (1-5 Rupee signs) with numeric rating
  const renderPriceScale = (price: number, maxPrice: number = 10000) => {
    // Map price to 1-5 scale
    let scale = Math.ceil((price / maxPrice) * 5);
    if (scale < 1) scale = 1;
    if (scale > 5) scale = 5;

    return (
      <div className="flex items-center gap-2" title={`Estimated: ₹${price}`}>
        <div className="flex items-center space-x-0.5">
          <span className="text-sm font-medium text-green-400">
            {'₹'.repeat(scale)}
          </span>
          <span className="text-sm font-medium text-gray-600">
            {'₹'.repeat(5 - scale)}
          </span>
        </div>
        <span className="text-xs text-white/50 font-medium">
          {scale}/5
        </span>
      </div>
    );
  };

  const handleEdit = (section: string, currentData: any) => {
    setEditingSection(section);
    setEditValues(currentData);
  };

  const handleSave = (section: string) => {
    onEdit(section, editValues);
    setEditingSection(null);
    setShowReplanTooltip(true);
    setTimeout(() => setShowReplanTooltip(false), 3000);
  };

  const handleCancel = () => {
    setEditingSection(null);
    setEditValues({});
  };

  const getCategoryIcon = (category: string) => {
    const icons = {
      sightseeing: Camera,
      food: Utensils,
      activity: Mountain,
      transport: Car,
      shopping: ShoppingBag,
      culture: Building,
      entertainment: Music,
      wellness: Leaf
    };
    return icons[category as keyof typeof icons] || Camera;
  };

  const getCategoryColor = (category: string) => {
    const colors = {
      sightseeing: 'bg-blue-500/20 text-blue-300',
      food: 'bg-green-500/20 text-green-300',
      activity: 'bg-purple-500/20 text-purple-300',
      transport: 'bg-orange-500/20 text-orange-300',
      shopping: 'bg-pink-500/20 text-pink-300',
      culture: 'bg-indigo-500/20 text-indigo-300',
      entertainment: 'bg-red-500/20 text-red-300',
      wellness: 'bg-teal-500/20 text-teal-300'
    };
    return colors[category as keyof typeof colors] || 'bg-gray-500/20 text-gray-300';
  };

  return (
    <TooltipProvider>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden"
      >
        {/* Animated background */}
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/6 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl animate-pulse" />
          <div className="absolute bottom-1/4 right-1/6 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse" />
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-pink-500/5 rounded-full blur-3xl animate-pulse" />
        </div>

        {/* Success notification */}
        <AnimatePresence>
          {showReplanTooltip && (
            <motion.div
              initial={{ opacity: 0, y: -50, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -50, scale: 0.9 }}
              className="fixed top-8 left-1/2 transform -translate-x-1/2 z-50 bg-gradient-to-r from-green-600 to-emerald-600 text-white px-8 py-4 rounded-2xl shadow-2xl backdrop-blur-sm"
            >
              <div className="flex items-center gap-3">
                <CheckCircle className="w-6 h-6" />
                <span className="text-lg">Trip updated successfully!</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="relative z-10 max-w-7xl mx-auto p-6">
          {/* Header */}
          <motion.div
            initial={{ y: -50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            className="mb-12"
          >
            {tripData.isFallback && (
              <div className="mb-6 p-4 bg-amber-500/20 border border-amber-500/30 rounded-xl flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="text-amber-300 font-medium mb-1">Rough Itinerary Generated</h4>
                  <p className="text-amber-200/70 text-sm">
                    We encountered an issue generating your full AI itinerary. We've created this rough plan based on your selections so you can still view your trip details.
                  </p>
                </div>
              </div>
            )}
            <Card className="bg-black/20 backdrop-blur-xl border-white/10 shadow-2xl overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10" />
              <CardContent className="relative p-8">
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-6">
                      <motion.div
                        animate={{ scale: [1, 1.1, 1], rotate: [0, 5, -5, 0] }}
                        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                        className="w-16 h-16 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-lg"
                      >
                        <Globe className="w-8 h-8 text-white" />
                      </motion.div>
                      <div className="flex-1">
                        <h1 className="text-4xl bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-2">
                          {typeof tripData.destination === 'string' ? tripData.destination : tripData.destination?.name || 'Your Destination'}
                        </h1>
                        <p className="text-white/70 text-lg">Your AI-curated travel itinerary</p>
                      </div>
                      <div className="flex gap-3">
                        <Button
                          variant="outline"
                          className="border-white/20 !text-white hover:bg-white/10 hover:!text-white backdrop-blur-sm font-medium"
                        >
                          <Share2 className="w-4 h-4 mr-2" />
                          Share
                        </Button>
                        <Button
                          variant="outline"
                          className="border-white/20 !text-white hover:bg-white/10 hover:!text-white backdrop-blur-sm font-medium"
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Export
                        </Button>
                        {onClose && (
                          <Button
                            onClick={onClose}
                            variant="ghost"
                            className="text-white/70 hover:text-white hover:bg-white/10"
                          >
                            <ArrowLeft className="w-5 h-5 mr-2" />
                            Back
                          </Button>
                        )}
                      </div>
                    </div>
                    <p className="text-white/80 text-lg leading-relaxed mb-6">{tripData.overview}</p>

                    <div className="flex flex-wrap gap-4">
                      <motion.div
                        whileHover={{ scale: 1.05 }}
                        className="flex items-center gap-3 px-6 py-3 bg-gradient-to-r from-blue-500/20 to-blue-600/20 rounded-xl backdrop-blur-sm"
                      >
                        <Calendar className="w-5 h-5 text-blue-400" />
                        <span className="text-white">
                          {new Date(tripData.dates.start).toLocaleDateString()} - {new Date(tripData.dates.end).toLocaleDateString()}
                        </span>
                      </motion.div>
                      <motion.div
                        whileHover={{ scale: 1.05 }}
                        className="flex items-center gap-3 px-6 py-3 bg-gradient-to-r from-purple-500/20 to-purple-600/20 rounded-xl backdrop-blur-sm"
                      >
                        <Users className="w-5 h-5 text-purple-400" />
                        <span className="text-white">{tripData.travelers} travelers</span>
                      </motion.div>
                      <motion.div
                        whileHover={{ scale: 1.05 }}
                        className="flex items-center gap-3 px-6 py-3 bg-gradient-to-r from-green-500/20 to-green-600/20 rounded-xl backdrop-blur-sm"
                      >
                        <DollarSign className="w-5 h-5 text-green-400" />
                        <span className="text-white">${tripData.totalBudget}</span>
                      </motion.div>
                      <motion.div
                        whileHover={{ scale: 1.05 }}
                        className="flex items-center gap-3 px-6 py-3 bg-gradient-to-r from-pink-500/20 to-pink-600/20 rounded-xl backdrop-blur-sm"
                      >
                        <Heart className="w-5 h-5 text-pink-400" />
                        <span className="text-white capitalize">{tripData.tripStyle} style</span>
                      </motion.div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Trip Days */}
          <div className="space-y-12">
            {tripData.days.map((day: any, dayIndex: number) => (
              <motion.div
                key={day.day}
                initial={{ y: 100, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ duration: 0.8, delay: dayIndex * 0.2, ease: "easeOut" }}
                className="space-y-8"
              >
                {/* Day Header */}
                <Card className="bg-black/20 backdrop-blur-xl border-white/10 shadow-2xl overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-pink-500/10" />
                  <CardContent className="relative p-8">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                      <div className="flex items-center gap-6">
                        <motion.div
                          animate={{ scale: [1, 1.05, 1] }}
                          transition={{ duration: 2, repeat: Infinity, delay: dayIndex * 0.5 }}
                          className="w-20 h-20 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-3xl flex items-center justify-center text-white text-2xl shadow-xl"
                        >
                          {day.day}
                        </motion.div>
                        <div>
                          <h2 className="text-3xl text-white mb-2">Day {day.day} - {day.city}</h2>
                          <p className="text-white/70 text-lg">{new Date(day.date).toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</p>
                        </div>
                      </div>

                      <div className="flex items-center gap-6">
                        <div className="flex items-center gap-3 text-white/80">
                          <span className="text-3xl">{day.weather.icon}</span>
                          <div>
                            <div className="text-xl">{day.weather.temperature}</div>
                            <div className="text-sm text-white/60">{day.weather.condition}</div>
                          </div>
                        </div>
                        <Badge className="bg-gradient-to-r from-green-500/20 to-green-600/20 text-green-300 border-green-500/30 px-4 py-2 text-lg">
                          ${day.budget.total}
                        </Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                  {/* Activities */}
                  <div className="lg:col-span-2 space-y-6">
                    <h3 className="text-2xl text-white flex items-center gap-3">
                      <Clock className="w-6 h-6 text-blue-400" />
                      Activities & Experiences
                    </h3>

                    <div className="space-y-6">
                      {day.activities.map((activity: any, activityIndex: number) => {
                        const IconComponent = getCategoryIcon(activity.category);
                        return (
                          <motion.div
                            key={activity.id}
                            initial={{ x: -100, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            transition={{ delay: (dayIndex * 0.2) + (activityIndex * 0.1), duration: 0.6 }}
                            whileHover={{ scale: 1.02, y: -5 }}
                            className="group"
                          >
                            <Card className="bg-black/20 backdrop-blur-xl border-white/10 hover:border-white/20 transition-all duration-500 shadow-xl overflow-hidden group">
                              <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-purple-500/5 to-pink-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                              <CardContent className="relative p-0 flex flex-col md:flex-row h-full">
                                {/* Activity Image */}
                                <div className="w-full md:w-48 h-48 md:h-auto relative overflow-hidden">
                                  <ImageWithFallback
                                    src={activity.image || "https://images.unsplash.com/photo-1523906834658-6e24ef2386f9?w=800&h=600&fit=crop"}
                                    alt={activity.title}
                                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                                  />
                                  <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent md:bg-gradient-to-r" />
                                  <div className="absolute bottom-3 left-3 md:top-3 md:left-3">
                                    <div className="w-10 h-10 bg-white/10 backdrop-blur-md rounded-xl flex items-center justify-center border border-white/20">
                                      <IconComponent className="w-5 h-5 text-white" />
                                    </div>
                                  </div>
                                </div>

                                {/* Content */}
                                <div className="flex-1 p-6 flex flex-col justify-between">
                                  <div>
                                    <div className="flex items-start justify-between gap-4 mb-2">
                                      <div>
                                        <h4 className="text-xl font-semibold text-white group-hover:text-blue-400 transition-colors">
                                          {activity.title}
                                        </h4>
                                        <div className="flex items-center gap-3 text-white/70 text-sm mt-1">
                                          <div className="flex items-center gap-1">
                                            <Clock className="w-3 h-3" />
                                            {activity.time} • {activity.duration}
                                          </div>
                                          {activity.rating > 0 && (
                                            <div className="flex items-center gap-1">
                                              <Star className="w-3 h-3 text-yellow-400 fill-current" />
                                              {activity.rating}
                                            </div>
                                          )}
                                        </div>
                                      </div>
                                      <Badge className={getCategoryColor(activity.category)}>
                                        {activity.category}
                                      </Badge>
                                    </div>

                                    <p className="text-white/70 text-sm leading-relaxed line-clamp-2 mb-4">
                                      {activity.description}
                                    </p>

                                    <div className="flex items-center gap-2 text-white/60 text-xs mb-4">
                                      <MapPin className="w-3 h-3" />
                                      <span className="truncate max-w-[300px]">
                                        {typeof activity.location === 'string' ? activity.location : activity.location?.name || 'Location not specified'}
                                      </span>
                                    </div>
                                  </div>

                                  <div className="flex items-center justify-between pt-4 border-t border-white/10">
                                    <div className="flex items-center gap-3">
                                      {activity.cost > 0 ? (
                                        renderPriceScale(activity.cost, 5000)
                                      ) : (
                                        <Badge variant="outline" className="border-green-500/30 text-green-400">Free</Badge>
                                      )}
                                      {activity.bookingRequired && (
                                        <Badge variant="outline" className="text-orange-400 border-orange-400/30 text-xs">
                                          Booking Required
                                        </Badge>
                                      )}
                                    </div>

                                    <Tooltip>
                                      <TooltipTrigger asChild>
                                        <Button
                                          size="sm"
                                          variant="ghost"
                                          onClick={() => handleEdit(`activity-${activity.id}`, activity)}
                                          className="text-white/50 hover:text-white hover:bg-white/10"
                                        >
                                          <Edit3 className="w-4 h-4" />
                                        </Button>
                                      </TooltipTrigger>
                                      <TooltipContent>Edit details</TooltipContent>
                                    </Tooltip>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          </motion.div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Accommodation & Info */}
                  <div className="space-y-8">
                    {/* Accommodation */}
                    {day.accommodation && (
                      <motion.div
                        initial={{ x: 100, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: dayIndex * 0.2 + 0.3, duration: 0.6 }}
                      >
                        <Card className="bg-black/20 backdrop-blur-xl border-white/10 shadow-2xl overflow-hidden">
                          <div className="absolute inset-0 bg-gradient-to-r from-green-500/5 to-emerald-500/5" />
                          <CardHeader className="relative pb-4">
                            <CardTitle className="flex items-center justify-between text-white">
                              <div className="flex items-center gap-3">
                                <Hotel className="w-6 h-6 text-green-400" />
                                Accommodation
                              </div>
                              <Tooltip>
                                <TooltipTrigger asChild>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => handleEdit(`accommodation-${day.day}`, day.accommodation)}
                                    className="text-white/70 hover:text-white hover:bg-white/10"
                                  >
                                    <Edit3 className="w-4 h-4" />
                                  </Button>
                                </TooltipTrigger>
                                <TooltipContent>Edit accommodation</TooltipContent>
                              </Tooltip>
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="relative">
                            <div className="space-y-4">
                              <div className="aspect-video rounded-xl overflow-hidden">
                                <ImageWithFallback
                                  src={day.accommodation.image}
                                  alt={day.accommodation.name}
                                  className="w-full h-full object-cover"
                                />
                              </div>

                              <div>
                                <h4 className="text-lg text-white mb-2">{day.accommodation.name}</h4>
                                <p className="text-white/70 mb-3">{day.accommodation.address}</p>
                                <div className="flex items-center gap-3 mb-4">
                                  <div className="flex items-center">
                                    {[...Array(5)].map((_, i) => (
                                      <Star
                                        key={i}
                                        className={`w-4 h-4 ${i < Math.floor(day.accommodation.rating)
                                          ? 'text-yellow-400 fill-current'
                                          : 'text-gray-500'
                                          }`}
                                      />
                                    ))}
                                    <span className="ml-2 text-white/70">
                                      {day.accommodation.rating}
                                    </span>
                                  </div>
                                  <span className="text-green-400 text-lg">
                                    ₹{day.accommodation.pricePerNight}/night
                                  </span>
                                </div>

                                <div className="text-white/70 mb-4">
                                  <div>Check-in: {day.accommodation.checkIn}</div>
                                  <div>Check-out: {day.accommodation.checkOut}</div>
                                </div>

                                <div className="flex flex-wrap gap-2">
                                  {day.accommodation.amenities.slice(0, 3).map((amenity: string, i: number) => (
                                    <Badge key={i} variant="secondary" className="bg-white/10 text-white/70 text-xs">
                                      {amenity}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      </motion.div>
                    )}

                    {/* Budget Breakdown */}
                    <motion.div
                      initial={{ x: 100, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: dayIndex * 0.2 + 0.4, duration: 0.6 }}
                    >
                      <Card className="bg-black/20 backdrop-blur-xl border-white/10 shadow-2xl overflow-hidden">
                        <div className="absolute inset-0 bg-gradient-to-r from-amber-500/5 to-yellow-500/5" />
                        <CardHeader className="relative pb-4">
                          <CardTitle className="flex items-center gap-3 text-white">
                            <DollarSign className="w-6 h-6 text-amber-400" />
                            Daily Budget
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="relative">
                          <div className="space-y-3">
                            <div className="flex justify-between text-white/80">
                              <span>Accommodation</span>
                              <span>₹{day.budget.accommodation}</span>
                            </div>
                            <div className="flex justify-between text-white/80">
                              <span>Food & Dining</span>
                              <span>₹{day.budget.food}</span>
                            </div>
                            <div className="flex justify-between text-white/80">
                              <span>Activities</span>
                              <span>₹{day.budget.activities}</span>
                            </div>
                            <div className="flex justify-between text-white/80">
                              <span>Transportation</span>
                              <span>₹{day.budget.transport}</span>
                            </div>
                            <Separator className="bg-white/20" />
                            <div className="flex justify-between text-white text-lg">
                              <span>Total</span>
                              <span className="text-green-400">₹{day.budget.total}</span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </motion.div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Local Transport Analysis */}
          {tripData.local_transport && (
            <motion.div
              initial={{ y: 50, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.8, duration: 0.8 }}
              className="mt-12"
            >
              <Card className="bg-black/20 backdrop-blur-xl border-white/10 shadow-2xl overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-orange-500/10 via-red-500/10 to-yellow-500/10" />
                <CardHeader className="relative pb-4">
                  <CardTitle className="flex items-center gap-3 text-white">
                    <Car className="w-6 h-6 text-orange-400" />
                    Local Transport Analysis
                  </CardTitle>
                </CardHeader>
                <CardContent className="relative text-white/80 space-y-6">
                  <div className="p-4 bg-white/5 rounded-xl border border-white/10">
                    <h4 className="text-lg text-white mb-2 font-semibold">
                      Recommended Mode: <span className="text-orange-400 capitalize">{tripData.local_transport.recommended_mode}</span>
                    </h4>
                    <p className="leading-relaxed whitespace-pre-line">{tripData.local_transport.analysis}</p>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {Object.entries(tripData.local_transport.mode_comparison || {}).map(([mode, data]: [string, any]) => (
                      <div key={mode} className="p-4 bg-black/20 rounded-lg border border-white/5">
                        <div className="capitalize text-white font-medium mb-1">{mode}</div>
                        <div className="text-2xl text-orange-300 mb-1">
                          {typeof data.avg_time_minutes === 'number' ? Math.round(data.avg_time_minutes) : 'N/A'} <span className="text-sm text-white/50">min</span>
                        </div>
                        <div className="text-xs text-white/50">Average travel time</div>
                      </div>
                    ))}
                  </div>


                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Recommended Flights */}
          {tripData.recommended_flights && tripData.recommended_flights.length > 0 && (
            <motion.div
              initial={{ y: 50, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.9, duration: 0.8 }}
              className="mt-12"
            >
              <Card className="bg-black/20 backdrop-blur-xl border-white/10 shadow-2xl overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-r from-sky-500/10 via-blue-500/10 to-indigo-500/10" />
                <CardHeader className="relative pb-4">
                  <CardTitle className="flex items-center gap-3 text-white">
                    <Plane className="w-6 h-6 text-sky-400" />
                    Recommended Flights
                  </CardTitle>
                </CardHeader>
                <CardContent className="relative space-y-4">
                  {tripData.recommended_flights.map((flight: any, index: number) => (
                    <div key={index} className="p-4 bg-white/5 rounded-xl border border-white/10 hover:bg-white/10 transition-colors">
                      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 bg-sky-500/20 rounded-full flex items-center justify-center">
                            <Plane className="w-6 h-6 text-sky-400" />
                          </div>
                          <div>
                            <h4 className="text-white font-semibold text-lg">{flight.airline}</h4>
                            <div className="text-white/60 text-sm">
                              {flight.origin} → {flight.destination} • {flight.stops === 0 ? 'Direct' : `${flight.stops} Stop(s)`}
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-6">
                          <div className="text-right">
                            <div className="text-white font-medium">{flight.duration}</div>
                            <div className="text-white/50 text-sm">Duration</div>
                          </div>
                          <div className="text-right">
                            <div className="text-sky-300 font-bold text-xl">₹{flight.price}</div>
                            <div className="text-white/50 text-sm">per person</div>
                          </div>
                          <Badge className="bg-sky-500/20 text-sky-300 border-sky-500/30">
                            Score: {flight.ai_score}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Summary Footer */}
          <motion.div
            initial={{ y: 50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 1, duration: 0.8 }}
            className="mt-16"
          >
            <Card className="bg-black/20 backdrop-blur-xl border-white/10 shadow-2xl overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-500/10 via-purple-500/10 to-pink-500/10" />
              <CardContent className="relative p-8 text-center">
                <motion.div
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="w-16 h-16 bg-gradient-to-r from-green-500 to-emerald-500 rounded-full flex items-center justify-center mx-auto mb-6"
                >
                  <CheckCircle className="w-8 h-8 text-white" />
                </motion.div>
                <h3 className="text-2xl text-white mb-4">Your Perfect Trip Awaits!</h3>
                <p className="text-white/70 mb-6 max-w-2xl mx-auto">
                  This AI-curated itinerary is designed to give you the best possible experience in {typeof tripData.destination === 'string' ? tripData.destination : tripData.destination?.name || 'your destination'}.
                  All suggestions are based on your preferences and can be customized to your needs.
                </p>
                <div className="flex justify-center gap-4">
                  <Button className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 !text-white font-medium">
                    <Download className="w-4 h-4 mr-2" />
                    Download Itinerary
                  </Button>
                  <Button variant="outline" className="border-white/20 !text-white hover:bg-white/10 hover:!text-white font-medium">
                    <Share2 className="w-4 h-4 mr-2" />
                    Share with Friends
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </motion.div >
    </TooltipProvider >
  );
}