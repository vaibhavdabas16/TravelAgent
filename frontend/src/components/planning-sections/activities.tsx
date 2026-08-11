import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Star, MapPin, Clock, Mountain, Heart, Plus, Users, Calendar } from 'lucide-react';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { mapPOIToActivity, Activity } from '../../utils/poi-mapper';

interface ActivitiesSectionProps {
  planningData: any;
  onSelectionChange: (data: any) => void;
  isTransitioning: boolean;
}

// Mock data - in real app this would come from API
const mockActivities: Activity[] = [
  {
    id: '1',
    name: 'Taj Mahal Sunrise Tour',
    description: 'Experience the Taj Mahal at dawn with an expert guide',
    image: 'https://images.unsplash.com/photo-1564507592333-c60657eea523?w=800&h=600&fit=crop',
    suggested: 95,
    price: '₹2500-3500',
    rating: 4.8,
    duration: '4 hours',
    groupSize: '2-30 people',
    difficulty: 'Easy',
    type: 'tour',
    location: 'Agra, Uttar Pradesh',
    includes: ['Hotel pickup', 'Expert guide', 'Entry tickets', 'Breakfast']
  },
  // ... (keep one or two mocks as fallback)
];

export function ActivitiesSection({ planningData, onSelectionChange, isTransitioning }: ActivitiesSectionProps) {
  const getTopSuggestionCount = (tripStyle: string) => {
    switch (tripStyle) {
      case 'laid-back': return 2;
      case 'adventurous': return 4;
      default: return 3; // balanced
    }
  };

  // Filter and map real POIs to activities
  let realActivities: Activity[] = [];
  if (planningData?.activities && planningData.activities.length > 0) {
    realActivities = planningData.activities.map(mapPOIToActivity);
  } else if (planningData?.pois) {
    realActivities = planningData.pois
      .filter((p: any) => p.category?.some((c: string) =>
        ['tour', 'museum', 'park', 'adventure', 'hiking', 'workshop', 'culture', 'landmark'].some(k => c.toLowerCase().includes(k))
      ))
      .map(mapPOIToActivity) || [];
  }

  // Use real activities if available, otherwise fallback to mock
  const activitiesToDisplay = realActivities.length > 0 ? realActivities : mockActivities;

  const topSuggestionCount = getTopSuggestionCount(planningData.tripStyle);
  const sortedActivities = [...activitiesToDisplay].sort((a, b) => b.suggested - a.suggested);

  // Pre-select top AI suggestions by default
  const defaultSelections = sortedActivities.slice(0, topSuggestionCount).map(a => a.id);
  const [selectedActivities, setSelectedActivities] = useState<string[]>(defaultSelections);
  const [hoveredActivity, setHoveredActivity] = useState<string | null>(null);

  // Initialize with default selections
  useEffect(() => {
    const newDefaultSelections = sortedActivities.slice(0, topSuggestionCount).map(a => a.id);
    setSelectedActivities(newDefaultSelections);
    onSelectionChange(newDefaultSelections);
  }, [planningData?.tripStyle, planningData?.pois]);

  const handleToggleActivity = (activityId: string) => {
    const newSelection = selectedActivities.includes(activityId)
      ? selectedActivities.filter(id => id !== activityId)
      : [...selectedActivities, activityId];

    setSelectedActivities(newSelection);
    onSelectionChange(newSelection);
  };

  const getTypeColor = (type: string) => {
    const colors = {
      outdoor: 'bg-green-500/20 text-green-300',
      cultural: 'bg-purple-500/20 text-purple-300',
      adventure: 'bg-red-500/20 text-red-300',
      tour: 'bg-blue-500/20 text-blue-300',
      workshop: 'bg-amber-500/20 text-amber-300'
    };
    return colors[type as keyof typeof colors] || 'bg-gray-500/20 text-gray-300';
  };

  const getDifficultyColor = (difficulty: string) => {
    const colors = {
      Easy: 'bg-emerald-500/20 text-emerald-300',
      Moderate: 'bg-yellow-500/20 text-yellow-300',
      Challenging: 'bg-red-500/20 text-red-300'
    };
    return colors[difficulty as keyof typeof colors] || 'bg-gray-500/20 text-gray-300';
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
          className="inline-block p-4 rounded-full bg-gradient-to-r from-green-500/20 to-emerald-500/20 backdrop-blur-sm mb-6"
        >
          <Mountain className="w-8 h-8 text-green-400" />
        </motion.div>

        <h2 className="text-3xl text-white mb-4">
          Adventure Awaits
        </h2>
        <p className="text-white/70 text-lg max-w-2xl mx-auto">
          Choose exciting activities and unique experiences to make your trip unforgettable.
          From cultural tours to thrilling adventures, create lasting memories.
        </p>
      </motion.div>

      {/* Activities grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sortedActivities.map((activity, index) => {
          const isSelected = selectedActivities.includes(activity.id);
          const isTopSuggestion = index < topSuggestionCount;
          const isHovered = hoveredActivity === activity.id;

          return (
            <motion.div
              key={activity.id}
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1, ease: "easeOut" }}
              onHoverStart={() => setHoveredActivity(activity.id)}
              onHoverEnd={() => setHoveredActivity(null)}
              className="group"
            >
              <Card className={`overflow-hidden cursor-pointer transition-all duration-300 ${isSelected
                ? 'ring-2 ring-green-400 bg-green-500/10'
                : 'bg-black/20 hover:bg-black/30'
                } backdrop-blur-sm border-white/10`}>
                <div className="relative">
                  {/* Image */}
                  <div className="aspect-video overflow-hidden">
                    <motion.img
                      src={activity.image}
                      alt={activity.name}
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
                        <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center">
                          <Heart className="w-4 h-4 text-white fill-current" />
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Difficulty badge */}
                  <div className="absolute bottom-3 right-3">
                    <Badge className={getDifficultyColor(activity.difficulty)}>
                      {activity.difficulty}
                    </Badge>
                  </div>
                </div>

                <div className="p-5">
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="text-white text-lg leading-tight">{activity.name}</h3>
                    <div className="flex items-center text-yellow-400 ml-2">
                      <Star className="w-4 h-4 fill-current" />
                      <span className="text-sm ml-1">{activity.rating}</span>
                    </div>
                  </div>

                  <p className="text-white/70 text-sm mb-4 line-clamp-2">
                    {activity.description}
                  </p>

                  <div className="space-y-2 mb-4">
                    <div className="flex items-center text-white/60 text-sm">
                      <MapPin className="w-4 h-4 mr-2" />
                      {activity.location}
                    </div>
                    <div className="flex items-center text-white/60 text-sm">
                      <Clock className="w-4 h-4 mr-2" />
                      {activity.duration}
                    </div>
                    <div className="flex items-center text-white/60 text-sm">
                      <Users className="w-4 h-4 mr-2" />
                      {activity.groupSize}
                    </div>
                  </div>

                  {/* Type and includes */}
                  <div className="mb-4">
                    <Badge className={getTypeColor(activity.type)} variant="secondary">
                      {activity.type}
                    </Badge>
                  </div>

                  <div className="flex flex-wrap gap-1 mb-4">
                    {activity.includes.slice(0, 3).map((include) => (
                      <Badge key={include} variant="secondary" className="text-xs bg-white/10 text-white/70">
                        {include}
                      </Badge>
                    ))}
                    {activity.includes.length > 3 && (
                      <Badge variant="secondary" className="text-xs bg-white/10 text-white/70">
                        +{activity.includes.length - 3} more
                      </Badge>
                    )}
                  </div>

                  <div className="flex justify-between items-center">
                    <span className="text-green-400">{activity.price}</span>
                    <Button
                      size="sm"
                      variant={isSelected ? "default" : "outline"}
                      onClick={() => handleToggleActivity(activity.id)}
                      className={isSelected
                        ? "bg-green-600 hover:bg-green-700 text-white"
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
        {selectedActivities.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="mt-12 text-center"
          >
            <div className="inline-flex items-center space-x-2 bg-green-500/20 rounded-full px-6 py-3 backdrop-blur-sm">
              <Heart className="w-5 h-5 text-green-400" />
              <span className="text-white">
                {selectedActivities.length} activit{selectedActivities.length !== 1 ? 'ies' : 'y'} selected
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}