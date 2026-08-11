import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Star, MapPin, Clock, Camera, Heart, Plus } from 'lucide-react';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card } from '../ui/card';



import { mapPOIToAttraction, Attraction } from '../../utils/poi-mapper';

interface PlacesToVisitSectionProps {
  planningData: any;
  onSelectionChange: (data: any) => void;
  isTransitioning: boolean;
}

export function PlacesToVisitSection({ planningData, onSelectionChange, isTransitioning }: PlacesToVisitSectionProps) {
  // Determine how many suggestions to highlight based on trip style
  const getTopSuggestionCount = (tripStyle: string) => {
    switch (tripStyle) {
      case 'laid-back': return 2;
      case 'adventurous': return 4;
      default: return 3; // balanced
    }
  };

  const topSuggestionCount = getTopSuggestionCount(planningData?.tripStyle || 'balanced');

  // Use real POIs if available, otherwise empty
  const attractions: Attraction[] = planningData?.pois && planningData.pois.length > 0
    ? planningData.pois.map(mapPOIToAttraction)
    : [];

  const sortedAttractions = [...attractions].sort((a, b) => b.suggested - a.suggested);

  // Pre-select top AI suggestions by default
  const defaultSelections = sortedAttractions.slice(0, topSuggestionCount).map(a => a.id);
  const [selectedAttractions, setSelectedAttractions] = useState<string[]>(defaultSelections);
  const [hoveredAttraction, setHoveredAttraction] = useState<string | null>(null);

  // Initialize with default selections
  // Initialize with default selections
  useEffect(() => {
    // Only set defaults if we haven't initialized yet
    // We check if selectedAttractions matches the default calculated from props
    // If we already have selections, we shouldn't overwrite them or trigger change

    // Actually, we just want to ensure the parent has the data once.
    // Let's use a ref to track if we've initialized.
  }, []);

  // Use a ref to track initialization
  const initialized = useState(false); // actually use useRef but I can't import it easily without changing imports
  // Let's just use a simple check

  useEffect(() => {
    if (planningData?.pois && selectedAttractions.length > 0) {
      // We have selections (defaults). Ensure parent knows about them.
      // But only if parent doesn't have them?
      // The parent updates 'planningData'.
      // If we call onSelectionChange, parent updates planningData.
      // planningData comes back.
      // This effect runs again if we depend on planningData.

      // Solution: Remove planningData from dependency array.
      // We only want to run this ONCE when the component mounts (and has POIs).

      onSelectionChange(selectedAttractions);
    }
  }, []); // Run once on mount

  const handleToggleAttraction = (attractionId: string) => {
    const newSelection = selectedAttractions.includes(attractionId)
      ? selectedAttractions.filter(id => id !== attractionId)
      : [...selectedAttractions, attractionId];

    setSelectedAttractions(newSelection);
    onSelectionChange(newSelection);
  };

  const getTypeColor = (type: string) => {
    const colors = {
      landmark: 'bg-amber-500/20 text-amber-300',
      museum: 'bg-purple-500/20 text-purple-300',
      nature: 'bg-green-500/20 text-green-300',
      cultural: 'bg-blue-500/20 text-blue-300',
      adventure: 'bg-red-500/20 text-red-300'
    };
    return colors[type as keyof typeof colors] || 'bg-gray-500/20 text-gray-300';
  };

  // Safety check
  if (!planningData) {
    return (
      <div className="max-w-6xl mx-auto text-center py-20">
        <div className="text-white text-xl">Loading planning data...</div>
      </div>
    );
  }

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
          className="inline-block p-4 rounded-full bg-gradient-to-r from-blue-500/20 to-purple-500/20 backdrop-blur-sm mb-6"
        >
          <MapPin className="w-8 h-8 text-blue-400" />
        </motion.div>

        <h2 className="text-3xl text-white mb-4">
          Discover Amazing Places
        </h2>
        <p className="text-white/70 text-lg max-w-2xl mx-auto">
          Select the attractions and landmarks that capture your imagination.
          Our AI has curated these based on your preferences.
        </p>
      </motion.div>

      {/* Attractions grid */}
      {sortedAttractions.length === 0 ? (
        <div className="text-center py-12 bg-white/5 rounded-xl backdrop-blur-sm border border-white/10">
          <MapPin className="w-12 h-12 text-white/20 mx-auto mb-4" />
          <h3 className="text-xl text-white mb-2">No places found</h3>
          <p className="text-white/60">We couldn't find any specific attractions for this destination.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedAttractions.map((attraction, index) => {
            const isSelected = selectedAttractions.includes(attraction.id);
            const isTopSuggestion = index < topSuggestionCount;
            const isHovered = hoveredAttraction === attraction.id;

            return (
              <motion.div
                key={attraction.id}
                initial={{ opacity: 0, y: 50 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1, ease: "easeOut" }}
                onHoverStart={() => setHoveredAttraction(attraction.id)}
                onHoverEnd={() => setHoveredAttraction(null)}
                className="group"
              >
                <Card className={`overflow-hidden cursor-pointer transition-all duration-300 ${isSelected
                  ? 'ring-2 ring-blue-400 bg-blue-500/10'
                  : 'bg-black/20 hover:bg-black/30'
                  } backdrop-blur-sm border-white/10`}>
                  <div className="relative">
                    {/* Image */}
                    <div className="aspect-video overflow-hidden">
                      <motion.img
                        src={attraction.image}
                        alt={attraction.name}
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
                          <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
                            <Heart className="w-4 h-4 text-white fill-current" />
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {/* Type badge */}
                    <div className="absolute bottom-3 right-3">
                      <Badge className={getTypeColor(attraction.type)}>
                        {attraction.type}
                      </Badge>
                    </div>
                  </div>

                  <div className="p-5">
                    <div className="flex justify-between items-start mb-3">
                      <h3 className="text-white text-lg leading-tight">{attraction.name}</h3>
                      <div className="flex items-center text-yellow-400 ml-2">
                        <Star className="w-4 h-4 fill-current" />
                        <span className="text-sm ml-1">{attraction.rating}</span>
                      </div>
                    </div>

                    <p className="text-white/70 text-sm mb-4 line-clamp-2">
                      {attraction.description}
                    </p>

                    <div className="space-y-2 mb-4">
                      <div className="flex items-center text-white/60 text-sm">
                        <MapPin className="w-4 h-4 mr-2" />
                        {attraction.location}
                      </div>
                      <div className="flex items-center text-white/60 text-sm">
                        <Clock className="w-4 h-4 mr-2" />
                        {attraction.duration}
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-1 mb-4">
                      {attraction.tags.map((tag) => (
                        <Badge key={tag} variant="secondary" className="text-xs bg-white/10 text-white/70">
                          {tag}
                        </Badge>
                      ))}
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-blue-400">{attraction.price}</span>
                      <Button
                        size="sm"
                        variant={isSelected ? "default" : "outline"}
                        onClick={() => handleToggleAttraction(attraction.id)}
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
      )}

      {/* Selection summary */}
      <AnimatePresence>
        {selectedAttractions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="mt-12 text-center"
          >
            <div className="inline-flex items-center space-x-2 bg-blue-500/20 rounded-full px-6 py-3 backdrop-blur-sm">
              <Heart className="w-5 h-5 text-blue-400" />
              <span className="text-white">
                {selectedAttractions.length} place{selectedAttractions.length !== 1 ? 's' : ''} selected
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}