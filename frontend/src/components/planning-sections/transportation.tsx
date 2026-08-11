import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Star, MapPin, Clock, Car, Train, Plane, Heart, Plus } from 'lucide-react';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card } from '../ui/card';

interface TransportOption {
  id: string;
  name: string;
  description: string;
  image: string;
  suggested: number;
  price: string;
  duration: string;
  type: 'flight' | 'train' | 'car' | 'bus' | 'metro';
  route: string;
  features: string[];
}

interface TransportationSectionProps {
  planningData: any;
  onSelectionChange: (data: any) => void;
  isTransitioning: boolean;
}

const mockTransportOptions: TransportOption[] = [
  {
    id: '1',
    name: 'Air India Direct Flight',
    description: 'Direct flight with excellent service and comfortable seating',
    image: 'https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=800&h=600&fit=crop',
    suggested: 95,
    price: '₹15000-35000',
    duration: '2-3 hours',
    type: 'flight',
    route: 'Delhi → Mumbai',
    features: ['Direct Flight', 'Meals Included', 'Entertainment']
  },
  {
    id: '2',
    name: 'Shatabdi Express Train',
    description: 'Premium high-speed train with comfortable seating',
    image: 'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=800&h=600&fit=crop',
    suggested: 88,
    price: '₹1500-3000',
    duration: '5-6 hours',
    type: 'train',
    route: 'Delhi → Agra',
    features: ['AC Coaches', 'Meals Included', 'Comfortable Seats']
  },
  {
    id: '3',
    name: 'Delhi Metro Pass',
    description: 'Unlimited access to Delhi Metro network',
    image: 'https://images.unsplash.com/photo-1592490337798-3811b23ed628?w=800&h=600&fit=crop',
    suggested: 92,
    price: '₹200-600',
    duration: 'Varies',
    type: 'metro',
    route: 'All Delhi NCR',
    features: ['Unlimited Travel', 'AC Coaches', '1-7 Day Options']
  }
];

// Helper to map backend flight data
const mapFlightToTransport = (flight: any): TransportOption => {
  // Check if it's the simplified Flight object from backend
  if (flight.airline) {
    const stopsText = flight.stops === 0 ? 'Direct Flight' : `${flight.stops} Stop(s)`;
    return {
      id: flight.offer_id || `flight-${Math.random()}`,
      name: `${flight.airline} Flight`,
      description: `Flight from ${flight.origin} to ${flight.destination}`,
      image: 'https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=800&h=600&fit=crop',
      suggested: flight.ai_score || 90,
      price: `₹${Math.round(flight.price * 83)}`, // Convert USD to INR approx
      duration: `${Math.floor(flight.duration_minutes / 60)}h ${flight.duration_minutes % 60}m`,
      type: 'flight',
      route: `${flight.origin} → ${flight.destination}`,
      features: [stopsText, flight.cabin_class || 'Economy', `CO2: ${flight.co2_emissions_kg || '?'}kg`]
    };
  }

  // Fallback for raw Amadeus data (legacy)
  const itinerary = flight.itineraries?.[0];
  const segment = itinerary?.segments?.[0];
  const carrier = flight.validatingAirlineCodes?.[0] || 'Airline';

  return {
    id: flight.id,
    name: `${carrier} Flight`,
    description: `Flight from ${segment?.departure?.iataCode} to ${segment?.arrival?.iataCode}`,
    image: 'https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=800&h=600&fit=crop',
    suggested: 95,
    price: flight.price?.total ? `₹${Math.round(parseFloat(flight.price.total) * 83)}` : 'Check Price',
    duration: itinerary?.duration?.replace('PT', '').replace('H', 'h ').replace('M', 'm').toLowerCase() || 'Unknown',
    type: 'flight',
    route: `${segment?.departure?.iataCode} → ${segment?.arrival?.iataCode}`,
    features: ['Direct Flight', 'Standard Seat']
  };
};

// Helper to map local transport strings/objects
const mapLocalTransportToOption = (item: any, type: 'train' | 'car' | 'bus' | 'metro', index: number): TransportOption => {
  const text = typeof item === 'string' ? item : (item.description || item.name || 'Transport Option');
  const price = typeof item === 'object' && item.price ? item.price : 'Varies';

  return {
    id: `local-${type}-${index}`,
    name: typeof item === 'object' && item.name ? item.name : `${type.charAt(0).toUpperCase() + type.slice(1)} Option`,
    description: text,
    image: type === 'metro' || type === 'train'
      ? 'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=800&h=600&fit=crop'
      : 'https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?w=800&h=600&fit=crop',
    suggested: 85,
    price: price,
    duration: 'Varies',
    type: type,
    route: 'City Travel',
    features: ['Local Travel']
  };
};

export function TransportationSection({ planningData, onSelectionChange, isTransitioning }: TransportationSectionProps) {
  // 1. Map Flights
  const flightOptions = planningData?.recommended_flights?.map(mapFlightToTransport) || [];

  // 2. Map Local Transport
  const localOptions: TransportOption[] = [];
  if (planningData?.local_transport) {
    const lt = planningData.local_transport;

    // Check for mode_comparison from new TransportAgent
    if (lt.mode_comparison) {
      const modes = lt.mode_comparison;

      // Walking
      if (modes.walking) {
        localOptions.push({
          id: 'local-walking',
          name: 'Walking',
          description: 'Explore the city on foot',
          image: 'https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?w=800&h=600&fit=crop',
          suggested: lt.recommended_mode === 'walking' ? 95 : 80,
          price: 'Free',
          duration: `${Math.round(modes.walking.avg_time_minutes)} min avg`,
          type: 'car', // Use car icon/type for generic ground
          route: 'City Center',
          features: ['Eco-friendly', 'Free', 'Scenic']
        });
      }

      // Transit
      if (modes.transit) {
        localOptions.push({
          id: 'local-transit',
          name: 'Public Transit',
          description: 'Bus, Metro, or Tram',
          image: 'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=800&h=600&fit=crop',
          suggested: lt.recommended_mode === 'transit' ? 95 : 85,
          price: '₹20-100',
          duration: `${Math.round(modes.transit.avg_time_minutes)} min avg`,
          type: 'metro',
          route: 'City Wide',
          features: ['Cost-effective', 'Reliable']
        });
      }

      // Driving
      if (modes.driving) {
        localOptions.push({
          id: 'local-driving',
          name: 'Rideshare / Taxi',
          description: 'Uber, Ola, or Taxi',
          image: 'https://images.unsplash.com/photo-1449965408869-eaa3f722e40d?w=800&h=600&fit=crop',
          suggested: lt.recommended_mode === 'driving' ? 95 : 70,
          price: '₹200-500',
          duration: `${Math.round(modes.driving.avg_time_minutes)} min avg`,
          type: 'car',
          route: 'Door to Door',
          features: ['Convenient', 'Fast', 'Private']
        });
      }
    } else {
      // Legacy fallback
      if (lt.transit_options) {
        lt.transit_options.forEach((opt: any, i: number) => localOptions.push(mapLocalTransportToOption(opt, 'metro', i)));
      }
      if (lt.taxi_services) {
        lt.taxi_services.forEach((opt: any, i: number) => localOptions.push(mapLocalTransportToOption(opt, 'car', i)));
      }
      if (lt.car_rentals) {
        lt.car_rentals.forEach((opt: any, i: number) => localOptions.push(mapLocalTransportToOption(opt, 'car', i + 10)));
      }
    }
  }

  const realTransportOptions = [...flightOptions, ...localOptions];
  const transportOptionsToDisplay = realTransportOptions.length > 0 ? realTransportOptions : mockTransportOptions;

  // Start with no selections to let user choose
  const [selectedTransport, setSelectedTransport] = useState<string[]>([]);

  // Initialize with default selections (empty)
  useEffect(() => {
    setSelectedTransport([]);
    onSelectionChange([]);
  }, [planningData?.recommended_flights, planningData?.local_transport]);

  const handleToggleTransport = (transportId: string) => {
    const newSelection = selectedTransport.includes(transportId)
      ? selectedTransport.filter(id => id !== transportId)
      : [...selectedTransport, transportId];

    setSelectedTransport(newSelection);
    onSelectionChange(newSelection);
  };

  const getTypeIcon = (type: string) => {
    const icons = {
      flight: Plane,
      train: Train,
      car: Car,
      bus: Car,
      metro: Train
    };
    return icons[type as keyof typeof icons] || Car;
  };

  return (
    <div className="max-w-6xl mx-auto">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="text-center mb-12"
      >
        <motion.div
          animate={{ scale: [1, 1.05, 1] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          className="inline-block p-4 rounded-full bg-gradient-to-r from-blue-500/20 to-cyan-500/20 backdrop-blur-sm mb-6"
        >
          <Car className="w-8 h-8 text-blue-400" />
        </motion.div>

        <h2 className="text-3xl text-white mb-4">Get Around in Style</h2>
        <p className="text-white/70 text-lg max-w-2xl mx-auto">
          Choose your preferred transportation methods for a seamless travel experience.
        </p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {transportOptionsToDisplay.map((transport, index) => {
          const isSelected = selectedTransport.includes(transport.id);
          const IconComponent = getTypeIcon(transport.type);

          return (
            <motion.div
              key={transport.id}
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1, ease: "easeOut" }}
            >
              <Card className={`overflow-hidden cursor-pointer transition-all duration-300 ${isSelected
                ? 'ring-2 ring-blue-400 bg-blue-500/10'
                : 'bg-black/20 hover:bg-black/30'
                } backdrop-blur-sm border-white/10`}>
                <div className="relative">
                  <div className="aspect-video overflow-hidden">
                    <img
                      src={transport.image}
                      alt={transport.name}
                      className="w-full h-full object-cover"
                    />
                  </div>

                  <div className="absolute top-3 left-3">
                    <Badge className="bg-gradient-to-r from-yellow-500 to-orange-500 text-white border-0">
                      <Star className="w-3 h-3 mr-1" />
                      AI Suggested
                    </Badge>
                  </div>

                  <AnimatePresence>
                    {isSelected && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        className="absolute top-3 right-3"
                      >
                        <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
                          <Heart className="w-4 h-4 text-white fill-current" />
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  <div className="absolute bottom-3 right-3">
                    <div className="flex items-center bg-black/50 rounded-full px-2 py-1">
                      <IconComponent className="w-4 h-4 text-white mr-1" />
                      <span className="text-white text-sm capitalize">{transport.type}</span>
                    </div>
                  </div>
                </div>

                <div className="p-5">
                  <h3 className="text-white text-lg mb-3">{transport.name}</h3>
                  <p className="text-white/70 text-sm mb-4">{transport.description}</p>

                  <div className="space-y-2 mb-4">
                    <div className="flex items-center text-white/60 text-sm">
                      <MapPin className="w-4 h-4 mr-2" />
                      {transport.route}
                    </div>
                    <div className="flex items-center text-white/60 text-sm">
                      <Clock className="w-4 h-4 mr-2" />
                      {transport.duration}
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-1 mb-4">
                    {transport.features.map((feature) => (
                      <Badge key={feature} variant="secondary" className="text-xs bg-white/10 text-white/70">
                        {feature}
                      </Badge>
                    ))}
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-blue-400">{transport.price}</span>
                    <Button
                      size="sm"
                      variant={isSelected ? "default" : "outline"}
                      onClick={() => handleToggleTransport(transport.id)}
                      className={isSelected
                        ? "bg-blue-600 hover:bg-blue-700 text-white"
                        : "border-white/20 text-white hover:bg-white/10"
                      }
                    >
                      {isSelected ? (
                        <>
                          <Heart className="w-4 h-4 mr-1 fill-current" />
                          Added
                        </>
                      ) : (
                        <>
                          <Plus className="w-4 h-4 mr-1" />
                          Add
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </Card>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}