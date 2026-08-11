import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Star, MapPin, Clock, Music, Heart, Plus, Calendar, Users } from 'lucide-react';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { mapPOIToEntertainment, Entertainment } from '../../utils/poi-mapper';

interface EntertainmentSectionProps {
  planningData: any;
  onSelectionChange: (data: any) => void;
  isTransitioning: boolean;
}

export function EntertainmentSection({ planningData, onSelectionChange, isTransitioning }: EntertainmentSectionProps) {
  const getTopSuggestionCount = (tripStyle: string) => {
    switch (tripStyle) {
      case 'laid-back': return 2;
      case 'adventurous': return 4;
      default: return 3; // balanced
    }
  };

  // Filter and map real POIs to entertainment
  const realEntertainment = planningData?.pois
    ?.filter((p: any) => p.category?.some((c: string) =>
      ['night_club', 'bar', 'casino', 'movie_theater', 'art_gallery', 'museum', 'club', 'pub', 'theater', 'concert'].some(k => c.toLowerCase().includes(k))
    ))
    .map(mapPOIToEntertainment) || [];

  // Use real entertainment if available, otherwise empty
  const entertainmentToDisplay = realEntertainment.length > 0 ? realEntertainment : [];

  const topSuggestionCount = getTopSuggestionCount(planningData?.tripStyle || 'balanced');
  const sortedEntertainment = [...entertainmentToDisplay].sort((a, b) => b.suggested - a.suggested);

  const defaultSelections = sortedEntertainment.slice(0, topSuggestionCount).map(e => e.id);
  const [selectedEntertainment, setSelectedEntertainment] = useState<string[]>(defaultSelections);
  const [hoveredEntertainment, setHoveredEntertainment] = useState<string | null>(null);

  // Initialize with default selections
  useEffect(() => {
    const newDefaultSelections = sortedEntertainment.slice(0, topSuggestionCount).map(e => e.id);
    setSelectedEntertainment(newDefaultSelections);
    onSelectionChange(newDefaultSelections);
  }, [planningData?.tripStyle, planningData?.pois]);

  const handleToggleEntertainment = (entertainmentId: string) => {
    const newSelection = selectedEntertainment.includes(entertainmentId)
      ? selectedEntertainment.filter(id => id !== entertainmentId)
      : [...selectedEntertainment, entertainmentId];

    setSelectedEntertainment(newSelection);
    onSelectionChange(newSelection);
  };

  const getTypeColor = (type: string) => {
    const colors = {
      theater: 'bg-purple-500/20 text-purple-300',
      concert: 'bg-blue-500/20 text-blue-300',
      cabaret: 'bg-pink-500/20 text-pink-300',
      nightclub: 'bg-red-500/20 text-red-300',
      bar: 'bg-amber-500/20 text-amber-300',
      cultural: 'bg-green-500/20 text-green-300'
    };
    return colors[type as keyof typeof colors] || 'bg-gray-500/20 text-gray-300';
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
          className="inline-block p-4 rounded-full bg-gradient-to-r from-indigo-500/20 to-purple-500/20 backdrop-blur-sm mb-6"
        >
          <Music className="w-8 h-8 text-indigo-400" />
        </motion.div>

        <h2 className="text-3xl text-white mb-4">
          Entertainment & Nightlife
        </h2>
        <p className="text-white/70 text-lg max-w-2xl mx-auto">
          Experience the best of Parisian entertainment from world-famous cabarets to intimate jazz clubs.
          Discover the magic of Paris after dark.
        </p>
      </motion.div>

      {/* Entertainment grid */}
      {sortedEntertainment.length === 0 ? (
        <div className="text-center py-12 bg-white/5 rounded-xl backdrop-blur-sm border border-white/10">
          <Music className="w-12 h-12 text-white/20 mx-auto mb-4" />
          <h3 className="text-xl text-white mb-2">No entertainment found</h3>
          <p className="text-white/60">We couldn't find any specific entertainment options for this destination.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedEntertainment.map((entertainment, index) => {
            const isSelected = selectedEntertainment.includes(entertainment.id);
            const isTopSuggestion = index < topSuggestionCount;
            const isHovered = hoveredEntertainment === entertainment.id;

            return (
              <motion.div
                key={entertainment.id}
                initial={{ opacity: 0, y: 50 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1, ease: "easeOut" }}
                onHoverStart={() => setHoveredEntertainment(entertainment.id)}
                onHoverEnd={() => setHoveredEntertainment(null)}
                className="group"
              >
                <Card className={`overflow-hidden cursor-pointer transition-all duration-300 ${isSelected
                  ? 'ring-2 ring-indigo-400 bg-indigo-500/10'
                  : 'bg-black/20 hover:bg-black/30'
                  } backdrop-blur-sm border-white/10`}>
                  <div className="relative">
                    {/* Image */}
                    <div className="aspect-video overflow-hidden">
                      <motion.img
                        src={entertainment.image}
                        alt={entertainment.name}
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
                          <div className="w-8 h-8 rounded-full bg-indigo-500 flex items-center justify-center">
                            <Heart className="w-4 h-4 text-white fill-current" />
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {/* Type badge */}
                    <div className="absolute bottom-3 right-3">
                      <Badge className={getTypeColor(entertainment.type)}>
                        {entertainment.type}
                      </Badge>
                    </div>
                  </div>

                  <div className="p-5">
                    <div className="flex justify-between items-start mb-3">
                      <h3 className="text-white text-lg leading-tight">{entertainment.name}</h3>
                      <div className="flex items-center text-yellow-400 ml-2">
                        <Star className="w-4 h-4 fill-current" />
                        <span className="text-sm ml-1">{entertainment.rating}</span>
                      </div>
                    </div>

                    <p className="text-white/70 text-sm mb-4 line-clamp-2">
                      {entertainment.description}
                    </p>

                    <div className="space-y-2 mb-4">
                      <div className="flex items-center text-white/60 text-sm">
                        <MapPin className="w-4 h-4 mr-2" />
                        {entertainment.location}
                      </div>
                      <div className="flex items-center text-white/60 text-sm">
                        <Clock className="w-4 h-4 mr-2" />
                        {entertainment.schedule}
                      </div>
                      <div className="flex items-center text-white/60 text-sm">
                        <Users className="w-4 h-4 mr-2" />
                        {entertainment.atmosphere}
                      </div>
                    </div>

                    {/* Features */}
                    <div className="flex flex-wrap gap-1 mb-4">
                      {entertainment.features.slice(0, 3).map((feature: string) => (
                        <Badge key={feature} variant="secondary" className="text-xs bg-white/10 text-white/70">
                          {feature}
                        </Badge>
                      ))}
                      {entertainment.features.length > 3 && (
                        <Badge variant="secondary" className="text-xs bg-white/10 text-white/70">
                          +{entertainment.features.length - 3} more
                        </Badge>
                      )}
                    </div>

                    {/* Dress code if available */}
                    {entertainment.dressCode && (
                      <div className="mb-4">
                        <Badge variant="outline" className="text-xs border-white/20 text-white/60">
                          {entertainment.dressCode}
                        </Badge>
                      </div>
                    )}

                    <div className="flex justify-between items-center">
                      <span className="text-indigo-400">{entertainment.price}</span>
                      <Button
                        size="sm"
                        variant={isSelected ? "default" : "outline"}
                        onClick={() => handleToggleEntertainment(entertainment.id)}
                        className={isSelected
                          ? "bg-indigo-600 hover:bg-indigo-700 text-white"
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
        {selectedEntertainment.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="mt-12 text-center"
          >
            <div className="inline-flex items-center space-x-2 bg-indigo-500/20 rounded-full px-6 py-3 backdrop-blur-sm">
              <Heart className="w-5 h-5 text-indigo-400" />
              <span className="text-white">
                {selectedEntertainment.length} entertainment option{selectedEntertainment.length !== 1 ? 's' : ''} selected
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}