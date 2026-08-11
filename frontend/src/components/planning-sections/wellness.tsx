import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Star, MapPin, Clock, Waves, Heart, Plus, Leaf, Sparkles } from 'lucide-react';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { mapPOIToWellness, WellnessLocation } from '../../utils/poi-mapper';

interface WellnessSectionProps {
  planningData: any;
  onSelectionChange: (data: any) => void;
  isTransitioning: boolean;
}

// Mock data - in real app this would come from API
const mockWellnessLocations: WellnessLocation[] = [
  {
    id: '1',
    name: 'Lodhi Gardens',
    description: 'Historic park with Mughal-era tombs and lush green landscapes',
    image: 'https://images.unsplash.com/photo-1524396309943-e03f5249f002?w=800&h=600&fit=crop',
    suggested: 95,
    price: 'Free',
    rating: 4.7,
    location: 'New Delhi',
    type: 'garden',
    duration: '1-3 hours',
    features: ['Historic Monuments', 'Jogging Tracks', 'Peaceful Walks', 'Bird Watching'],
    atmosphere: 'Serene and historic',
    bestTime: 'Early morning or evening'
  },
  // ... (keep one or two mocks as fallback)
];

export function WellnessSection({ planningData, onSelectionChange, isTransitioning }: WellnessSectionProps) {
  const getTopSuggestionCount = (tripStyle: string) => {
    switch (tripStyle) {
      case 'laid-back': return 3; // More wellness for laid-back trips
      case 'adventurous': return 2;
      default: return 2; // balanced
    }
  };

  // Filter and map real POIs to wellness
  const realWellness = planningData?.wellness?.map(mapPOIToWellness) ||
    planningData?.pois
      ?.filter((p: any) => p.category?.some((c: string) =>
        ['spa', 'park', 'gym', 'beauty_salon', 'hair_care', 'health', 'garden', 'beach'].some(k => c.toLowerCase().includes(k))
      ))
      .map(mapPOIToWellness) || [];

  // Use real wellness if available, otherwise fallback to mock
  const wellnessToDisplay = realWellness.length > 0 ? realWellness : mockWellnessLocations;

  const topSuggestionCount = getTopSuggestionCount(planningData.tripStyle);
  const sortedWellness = [...wellnessToDisplay].sort((a, b) => b.suggested - a.suggested);

  // Pre-select top AI suggestions by default
  const defaultSelections = sortedWellness.slice(0, topSuggestionCount).map(w => w.id);
  const [selectedWellness, setSelectedWellness] = useState<string[]>(defaultSelections);
  const [hoveredWellness, setHoveredWellness] = useState<string | null>(null);

  // Initialize with default selections
  useEffect(() => {
    const newDefaultSelections = sortedWellness.slice(0, topSuggestionCount).map(w => w.id);
    setSelectedWellness(newDefaultSelections);
    onSelectionChange(newDefaultSelections);
  }, [planningData?.tripStyle, planningData?.pois]);

  const handleToggleWellness = (wellnessId: string) => {
    const newSelection = selectedWellness.includes(wellnessId)
      ? selectedWellness.filter(id => id !== wellnessId)
      : [...selectedWellness, wellnessId];

    setSelectedWellness(newSelection);
    onSelectionChange(newSelection);
  };

  const getTypeColor = (type: string) => {
    const colors = {
      spa: 'bg-purple-500/20 text-purple-300',
      park: 'bg-green-500/20 text-green-300',
      garden: 'bg-emerald-500/20 text-emerald-300',
      beach: 'bg-blue-500/20 text-blue-300',
      thermal: 'bg-orange-500/20 text-orange-300',
      yoga: 'bg-pink-500/20 text-pink-300'
    };
    return colors[type as keyof typeof colors] || 'bg-gray-500/20 text-gray-300';
  };

  const getTypeIcon = (type: string) => {
    const icons = {
      spa: Sparkles,
      park: Leaf,
      garden: Leaf,
      beach: Waves,
      thermal: Waves,
      yoga: Sparkles
    };
    return icons[type as keyof typeof icons] || Leaf;
  };

  return (
    <div className="max-w-6xl mx-auto">
      {/* Section intro */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className="text-center mb-12"
      >
        <motion.div
          animate={{ scale: [1, 1.05, 1] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          className="inline-block p-4 rounded-full bg-gradient-to-r from-teal-500/20 to-cyan-500/20 backdrop-blur-sm mb-6"
        >
          <Waves className="w-8 h-8 text-teal-400" />
        </motion.div>

        <h2 className="text-3xl text-white mb-4">
          Wellness & Relaxation
        </h2>
        <p className="text-white/70 text-lg max-w-2xl mx-auto">
          Find peaceful spots to unwind and rejuvenate during your travels.
          From luxury spas to serene gardens, discover your perfect sanctuary.
        </p>
      </motion.div>

      {/* Wellness locations grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sortedWellness.map((wellness, index) => {
          const isSelected = selectedWellness.includes(wellness.id);
          const isTopSuggestion = index < topSuggestionCount;
          const isHovered = hoveredWellness === wellness.id;
          const TypeIcon = getTypeIcon(wellness.type);

          return (
            <motion.div
              key={wellness.id}
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1, ease: "easeOut" }}
              onHoverStart={() => setHoveredWellness(wellness.id)}
              onHoverEnd={() => setHoveredWellness(null)}
              className="group"
            >
              <Card className={`overflow-hidden cursor-pointer transition-all duration-300 ${isSelected
                ? 'ring-2 ring-teal-400 bg-teal-500/10'
                : 'bg-black/20 hover:bg-black/30'
                } backdrop-blur-sm border-white/10`}>
                <div className="relative">
                  {/* Image */}
                  <div className="aspect-video overflow-hidden">
                    <motion.img
                      src={wellness.image}
                      alt={wellness.name}
                      className="w-full h-full object-cover"
                      animate={{
                        scale: isHovered ? 1.05 : 1
                      }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>

                  {/* Suggested badge */}
                  {isTopSuggestion && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.3 + index * 0.1 }}
                      className="absolute top-3 left-3"
                    >
                      <Badge className="bg-gradient-to-r from-yellow-500 to-orange-500 text-white border-0">
                        <Star className="w-3 h-3 mr-1" />
                        AI Suggested
                      </Badge>
                    </motion.div>
                  )}

                  {/* Selection indicator */}
                  <AnimatePresence>
                    {isSelected && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        className="absolute top-3 right-3"
                      >
                        <div className="w-8 h-8 rounded-full bg-teal-500 flex items-center justify-center">
                          <Heart className="w-4 h-4 text-white fill-current" />
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Type badge */}
                  <div className="absolute bottom-3 right-3">
                    <div className={`flex items-center rounded-full px-2 py-1 text-xs ${getTypeColor(wellness.type)}`}>
                      <TypeIcon className="w-3 h-3 mr-1" />
                      {wellness.type}
                    </div>
                  </div>
                </div>

                <div className="p-5">
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="text-white text-lg leading-tight">{wellness.name}</h3>
                    <div className="flex items-center text-yellow-400 ml-2">
                      <Star className="w-4 h-4 fill-current" />
                      <span className="text-sm ml-1">{wellness.rating}</span>
                    </div>
                  </div>

                  <p className="text-white/70 text-sm mb-4 line-clamp-2">
                    {wellness.description}
                  </p>

                  <div className="space-y-2 mb-4">
                    <div className="flex items-center text-white/60 text-sm">
                      <MapPin className="w-4 h-4 mr-2" />
                      {wellness.location}
                    </div>
                    <div className="flex items-center text-white/60 text-sm">
                      <Clock className="w-4 h-4 mr-2" />
                      {wellness.duration}
                    </div>
                    <div className="flex items-center text-white/60 text-sm">
                      <Sparkles className="w-4 h-4 mr-2" />
                      {wellness.atmosphere}
                    </div>
                  </div>

                  {/* Features */}
                  <div className="flex flex-wrap gap-1 mb-4">
                    {wellness.features.slice(0, 3).map((feature: string) => (
                      <Badge key={feature} variant="secondary" className="text-xs bg-white/10 text-white/70">
                        {feature}
                      </Badge>
                    ))}
                    {wellness.features.length > 3 && (
                      <Badge variant="secondary" className="text-xs bg-white/10 text-white/70">
                        +{wellness.features.length - 3} more
                      </Badge>
                    )}
                  </div>

                  {/* Best time */}
                  <div className="mb-4">
                    <Badge variant="outline" className="text-xs border-white/20 text-white/60">
                      Best: {wellness.bestTime}
                    </Badge>
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-teal-400">{wellness.price}</span>
                    <Button
                      size="sm"
                      variant={isSelected ? "default" : "outline"}
                      onClick={() => handleToggleWellness(wellness.id)}
                      className={isSelected
                        ? "bg-teal-600 hover:bg-teal-700 text-white"
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

      {/* Selection summary */}
      <AnimatePresence>
        {selectedWellness.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="mt-12 text-center"
          >
            <div className="inline-flex items-center space-x-2 bg-teal-500/20 rounded-full px-6 py-3 backdrop-blur-sm">
              <Heart className="w-5 h-5 text-teal-400" />
              <span className="text-white">
                {selectedWellness.length} wellness spot{selectedWellness.length !== 1 ? 's' : ''} selected
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}