import { motion, AnimatePresence } from 'motion/react';
import { useState, useEffect, useRef } from 'react';
import { Send, Sparkles, MapPin, Calendar, Users, DollarSign, Heart, Camera, CalendarDays, Wifi, Car, Utensils, Waves, Plus, ChevronLeft } from 'lucide-react';
import { Calendar as CalendarComponent } from './ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from './ui/popover';
import { Button } from './ui/button';
import { Checkbox } from './ui/checkbox';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { TripPlan } from './trip-plan';

interface Question {
  id: string;
  type: 'text' | 'multiple-choice' | 'multi-select' | 'datetime' | 'date-range' | 'amenities';
  question: string;
  placeholder?: string;
  options?: string[];
  icon?: any;
  allowMultiple?: boolean;
  allowCustom?: boolean;
  suggestedOptions?: string[];
}

const questionFlow: Question[] = [
  {
    id: 'destination',
    type: 'text',
    question: "Where do you want to go?",
    placeholder: "e.g., Tokyo, Paris, New York",
    icon: MapPin
  },
  {
    id: 'origin',
    type: 'text',
    question: "Where are you starting your trip from?",
    placeholder: "e.g., London, San Francisco, Mumbai",
    icon: MapPin
  },
  {
    id: 'travelers',
    type: 'multiple-choice',
    question: "How many travelers will be joining this adventure?",
    options: ['Just me (Solo)', '2 travelers (Couple)', '3-4 travelers (Small group)', '5+ travelers (Large group)'],
    icon: Users
  },
  {
    id: 'dates',
    type: 'date-range',
    question: "When are you planning to travel?",
    placeholder: "Select your travel dates",
    icon: CalendarDays
  },
  {
    id: 'budget',
    type: 'multiple-choice',
    question: "What's your approximate budget per person?",
    options: ['Budget-friendly', 'Mid-range', 'Luxury', 'No budget constraints'],
    icon: DollarSign
  },
  {
    id: 'interests',
    type: 'multi-select',
    question: "What type of experiences excite you most? (Select all that apply)",
    options: ['Cultural immersion & history', 'Adventure & outdoor activities', 'Relaxation & wellness', 'Food & nightlife', 'Photography & sightseeing', 'Wildlife & nature', 'Art & museums', 'Shopping & markets'],
    icon: Heart,
    allowMultiple: true
  },
  {
    id: 'amenities',
    type: 'amenities',
    question: "What amenities are important for your accommodation?",
    suggestedOptions: ['Free WiFi', 'Swimming Pool', 'Gym/Fitness Center', 'Spa Services', 'Restaurant', 'Room Service', 'Airport Shuttle', 'Pet Friendly', 'Business Center', 'Parking', 'Air Conditioning', 'Kitchen/Kitchenette'],
    icon: Wifi,
    allowCustom: true
  },
  {
    id: 'pace',
    type: 'multiple-choice',
    question: "How would you describe your ideal travel pace?",
    options: ['Slow & relaxed (few destinations)', 'Balanced mix of activities', 'Action-packed (see everything)', 'Flexible (go with the flow)'],
    icon: MapPin
  }
];

interface PlanningInterfaceProps {
  initialQuery?: string;
  onClose: () => void;
  onViewTripPlan?: (data?: any) => void;
  onComplete?: (data: any) => void;
  initialData?: any;
}

// Helper functions to extract structured data from answers
function extractDestinationFromAnswers(answers: Record<string, string | string[]>): string {
  // 1. Check explicit destination answer
  if (answers.destination && typeof answers.destination === 'string') {
    return answers.destination;
  }
  // 2. Fallback to initial query if it looks like a destination (simple heuristic)
  // ... existing logic ...
  const firstAnswer = Object.values(answers)[0];
  if (typeof firstAnswer === 'string' && firstAnswer.includes('destination')) {
    return firstAnswer;
  }
  return 'Paris, France'; // Default fallback
}

function extractTripStyleFromAnswers(answers: Record<string, string | string[]>): string {
  const pace = answers.pace as string;
  if (pace?.includes('relaxed')) return 'laid-back';
  if (pace?.includes('action-packed')) return 'adventurous';
  return 'balanced';
}

function extractTravelersFromAnswers(answers: Record<string, string | string[]>): number {
  const travelers = answers.travelers as string;
  if (travelers?.includes('Just me')) return 1;
  if (travelers?.includes('2 travelers')) return 2;
  if (travelers?.includes('3-4')) return 3;
  if (travelers?.includes('5+')) return 5;
  return 2; // Default
}

export function PlanningInterface({ initialQuery, onClose, onViewTripPlan, onComplete, initialData }: PlanningInterfaceProps) {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string | string[]>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [textInput, setTextInput] = useState('');
  const [isComplete, setIsComplete] = useState(false);
  const [showTripPlan, setShowTripPlan] = useState(false);
  const [dateRange, setDateRange] = useState<{ from: Date | undefined; to: Date | undefined }>({
    from: undefined,
    to: undefined,
  });
  const [isFlexibleDates, setIsFlexibleDates] = useState(false);
  const [selectedOptions, setSelectedOptions] = useState<string[]>([]);
  const [customAmenity, setCustomAmenity] = useState('');
  const [selectedAmenities, setSelectedAmenities] = useState<string[]>([]);

  const currentQuestion = questionFlow[currentQuestionIndex];
  const progress = ((currentQuestionIndex + 1) / questionFlow.length) * 100;

  const handleAnswer = async (answer: string | string[]) => {
    setAnswers(prev => ({ ...prev, [currentQuestion.id]: answer }));
    setIsLoading(true);

    // Simulate AI processing time
    await new Promise(resolve => setTimeout(resolve, 1000));

    if (currentQuestionIndex < questionFlow.length - 1) {
      setCurrentQuestionIndex(prev => prev + 1);
      // Reset form states
      setTextInput('');
      setSelectedOptions([]);
      setDateRange({ from: undefined, to: undefined });
      setIsFlexibleDates(false);
      setSelectedAmenities([]);
      setCustomAmenity('');
    } else {
      setIsComplete(true);
      // Show trip plan after a delay
      setTimeout(() => {
        setShowTripPlan(true);
      }, 3000);
    }
    setIsLoading(false);
  };

  const handlePrevious = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(prev => prev - 1);
      // Reset form states
      setTextInput('');
      setSelectedOptions([]);
      setDateRange({ from: undefined, to: undefined });
      setIsFlexibleDates(false);
      setSelectedAmenities([]);
      setCustomAmenity('');
    }
  };

  const handleTripPlanEdit = (section: string, data: any) => {
    console.log('Editing section:', section, 'with data:', data);
    // Handle trip plan edits here
  };

  const handleDateAnswer = () => {
    if (isFlexibleDates) {
      handleAnswer('Flexible dates - I\'m open to suggestions');
    } else if (dateRange.from && dateRange.to) {
      handleAnswer(`${dateRange.from.toLocaleDateString()} - ${dateRange.to.toLocaleDateString()}`);
    } else if (dateRange.from) {
      handleAnswer(dateRange.from.toLocaleDateString());
    }
  };

  const handleMultiSelectAnswer = () => {
    if (selectedOptions.length > 0) {
      handleAnswer(selectedOptions);
    }
  };

  const handleAmenitiesAnswer = () => {
    if (selectedAmenities.length > 0) {
      handleAnswer(selectedAmenities);
    }
  };

  const addCustomAmenity = () => {
    if (customAmenity.trim() && !selectedAmenities.includes(customAmenity.trim())) {
      setSelectedAmenities(prev => [...prev, customAmenity.trim()]);
      setCustomAmenity('');
    }
  };

  const toggleAmenity = (amenity: string) => {
    setSelectedAmenities(prev =>
      prev.includes(amenity)
        ? prev.filter(a => a !== amenity)
        : [...prev, amenity]
    );
  };

  const toggleMultiSelectOption = (option: string) => {
    setSelectedOptions(prev =>
      prev.includes(option)
        ? prev.filter(o => o !== option)
        : [...prev, option]
    );
  };

  const handleTextSubmit = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && textInput.trim()) {
      handleAnswer(textInput.trim());
    }
  };

  const hasCompleted = useRef(false);

  useEffect(() => {
    if (showTripPlan && !hasCompleted.current) {
      hasCompleted.current = true;
      if (onComplete) {
        const completedData = {
          query: initialQuery || initialData?.query || '',
          destination: extractDestinationFromAnswers(answers) || initialData?.destination,
          tripStyle: extractTripStyleFromAnswers(answers),
          travelers: extractTravelersFromAnswers(answers),
          budget: answers.budget,
          dates: answers.dates,
          interests: answers.interests,
          amenities: answers.amenities,
          pace: answers.pace,
          origin: answers.origin // Include origin in completed data
        };
        onComplete(completedData);
      } else if (onViewTripPlan) {
        onViewTripPlan();
      }
    }
  }, [showTripPlan, onComplete, onViewTripPlan, answers, initialQuery, initialData]);

  if (showTripPlan) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 z-50 overflow-y-auto"
    >

      {/* Floating elements */}
      <motion.div
        animate={{ y: [-20, 20, -20], rotate: [0, 180, 360] }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
        className="absolute top-20 right-20 w-32 h-32 bg-blue-200/20 rounded-full blur-xl pointer-events-none"
      />
      <motion.div
        animate={{ y: [20, -20, 20], rotate: [360, 180, 0] }}
        transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
        className="absolute bottom-32 left-16 w-24 h-24 bg-purple-200/20 rounded-full blur-xl pointer-events-none"
      />

      {/* Full height content wrapper */}
      <div className="min-h-screen">
        {/* Header with progress */}
        <motion.div
          initial={{ y: -100 }}
          animate={{ y: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="sticky top-0 z-10 bg-slate-900/95 backdrop-blur-lg border-b border-white/10 p-4 lg:p-6"
        >
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-between mb-4">
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
                className="flex items-center gap-3"
              >
                <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h1 className="text-xl bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
                    AI Travel Planner
                  </h1>
                  <p className="text-sm text-gray-300">Creating your perfect itinerary</p>
                </div>
              </motion.div>

              <motion.button
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 }}
                onClick={onClose}
                className="px-4 py-2 text-white/70 hover:text-white transition-colors"
              >
                ✕
              </motion.button>
            </div>

            {/* Your idea display */}
            {(initialQuery || initialData?.query) && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 }}
                className="bg-white/10 backdrop-blur-sm px-3 py-2 rounded-lg border border-white/20 mb-3"
              >
                <p className="text-xs lg:text-sm text-gray-300">
                  <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">Your Travel Idea:</span>
                  <span className="text-white ml-2">"{initialQuery || initialData?.query}"</span>
                </p>
              </motion.div>
            )}

            {/* Navigation buttons */}
            {currentQuestionIndex > 0 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mb-3"
              >
                <motion.button
                  onClick={handlePrevious}
                  whileHover={{ scale: 1.02, x: -2 }}
                  whileTap={{ scale: 0.98 }}
                  className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 border border-white/20 hover:border-white/40 rounded-lg text-white/90 hover:text-white transition-all duration-300 backdrop-blur-sm"
                >
                  <ChevronLeft className="w-4 h-4" />
                  <span className="text-sm">Previous</span>
                </motion.button>
              </motion.div>
            )}

            {/* Progress bar */}
            <div className="w-full bg-white/20 rounded-full h-2">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.5, ease: "easeOut" }}
                className="h-2 bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 rounded-full"
              />
            </div>
            <p className="text-sm text-gray-300 mt-2">
              Step {currentQuestionIndex + 1} of {questionFlow.length}
            </p>
          </div>
        </motion.div>

        {/* Main content */}
        <div className="relative z-10 min-h-[calc(100vh-180px)] flex items-start justify-center p-4 lg:p-6 pb-20">
          <div className="max-w-2xl mx-auto w-full mt-8">
            <AnimatePresence mode="wait">
              {!isComplete ? (
                <motion.div
                  key={currentQuestionIndex}
                  initial={{ opacity: 0, y: 50 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -50 }}
                  transition={{ duration: 0.5 }}
                  className="text-center"
                >
                  {/* Question icon */}
                  {currentQuestion.icon && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: 0.2, duration: 0.5, type: "spring" }}
                      className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-6"
                    >
                      <currentQuestion.icon className="w-8 h-8 text-white" />
                    </motion.div>
                  )}

                  {/* Question text */}
                  <motion.h2
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: 0.3 }}
                    className="text-2xl lg:text-3xl text-white mb-6 lg:mb-8 px-4"
                  >
                    {currentQuestion.question}
                  </motion.h2>

                  {/* Loading state */}
                  <AnimatePresence>
                    {isLoading && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        className="flex items-center justify-center gap-3 mb-8"
                      >
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                          className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full"
                        />
                        <span className="text-gray-300">Processing your answer...</span>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  {/* Answer options */}
                  {!isLoading && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.4 }}
                    >
                      {currentQuestion.type === 'multiple-choice' ? (
                        <div className="space-y-4 px-4 lg:px-0">
                          {currentQuestion.options?.map((option, index) => (
                            <motion.button
                              key={option}
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: 0.1 * index }}
                              whileHover={{ scale: 1.02, x: 8 }}
                              whileTap={{ scale: 0.98 }}
                              onClick={() => handleAnswer(option)}
                              disabled={isLoading}
                              className="w-full p-4 text-left bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl hover:border-blue-400/50 hover:shadow-lg hover:bg-white/15 transition-all duration-300 group disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              <span className="text-white group-hover:text-blue-300 transition-colors">
                                {option}
                              </span>
                            </motion.button>
                          ))}
                        </div>
                      ) : currentQuestion.type === 'multi-select' ? (
                        <div className="space-y-6 px-4 lg:px-0">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {currentQuestion.options?.map((option, index) => (
                              <motion.div
                                key={option}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.1 * index }}
                                className={`p-4 border rounded-xl cursor-pointer transition-all duration-300 ${selectedOptions.includes(option)
                                  ? 'border-blue-400/50 bg-white/15 shadow-lg'
                                  : 'border-white/20 bg-white/10 hover:border-blue-400/30 hover:shadow-md'
                                  } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                                onClick={() => !isLoading && toggleMultiSelectOption(option)}
                              >
                                <div className="flex items-center gap-3">
                                  <Checkbox
                                    checked={selectedOptions.includes(option)}
                                    onChange={() => toggleMultiSelectOption(option)}
                                    disabled={isLoading}
                                  />
                                  <span className={selectedOptions.includes(option) ? 'text-blue-300' : 'text-white'}>
                                    {option}
                                  </span>
                                </div>
                              </motion.div>
                            ))}
                          </div>
                          <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: selectedOptions.length > 0 ? 1 : 0.5 }}
                            className="text-center"
                          >
                            <Button
                              onClick={handleMultiSelectAnswer}
                              disabled={selectedOptions.length === 0 || isLoading}
                              className="px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl disabled:opacity-50"
                            >
                              Continue with {selectedOptions.length} selection{selectedOptions.length !== 1 ? 's' : ''}
                            </Button>
                          </motion.div>
                        </div>
                      ) : currentQuestion.type === 'date-range' ? (
                        <div className="space-y-6 px-4 lg:px-0">
                          <div className="flex flex-col items-center gap-4">
                            <motion.div
                              initial={{ opacity: 0, scale: 0.9 }}
                              animate={{ opacity: 1, scale: 1 }}
                              className="bg-white p-4 rounded-xl border border-gray-200 shadow-lg"
                            >
                              <CalendarComponent
                                mode="range"
                                selected={dateRange}
                                onSelect={(range: any) => setDateRange(range || { from: undefined, to: undefined })}
                                disabled={(date: Date) => date < new Date() || isLoading}
                                className="rounded-lg"
                                numberOfMonths={2}
                              />
                            </motion.div>

                            <div className="text-center space-y-4">
                              <motion.button
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                onClick={() => setIsFlexibleDates(!isFlexibleDates)}
                                disabled={isLoading}
                                className={`px-6 py-3 rounded-xl border-2 transition-all ${isFlexibleDates
                                  ? 'border-blue-400 bg-blue-50 text-blue-700'
                                  : 'border-gray-200 bg-white text-gray-700 hover:border-blue-300'
                                  } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                              >
                                {isFlexibleDates ? '✓ ' : ''}I'm flexible with dates
                              </motion.button>

                              <Button
                                onClick={handleDateAnswer}
                                disabled={(!dateRange.from && !isFlexibleDates) || isLoading}
                                className="px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl disabled:opacity-50"
                              >
                                {isFlexibleDates ? 'Continue with flexible dates' : 'Continue with selected dates'}
                              </Button>
                            </div>
                          </div>
                        </div>
                      ) : currentQuestion.type === 'amenities' ? (
                        <div className="space-y-6 px-4 lg:px-0">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {currentQuestion.suggestedOptions?.map((amenity, index) => (
                              <motion.div
                                key={amenity}
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.05 * index }}
                                className={`p-3 border rounded-xl cursor-pointer transition-all duration-300 ${selectedAmenities.includes(amenity)
                                  ? 'border-blue-400/50 bg-white/15 shadow-lg'
                                  : 'border-white/20 bg-white/10 hover:border-blue-400/30 hover:shadow-md'
                                  } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                                onClick={() => !isLoading && toggleAmenity(amenity)}
                              >
                                <div className="flex items-center gap-3">
                                  <Checkbox
                                    checked={selectedAmenities.includes(amenity)}
                                    onChange={() => toggleAmenity(amenity)}
                                    disabled={isLoading}
                                  />
                                  <span className={selectedAmenities.includes(amenity) ? 'text-blue-300' : 'text-white'}>
                                    {amenity}
                                  </span>
                                </div>
                              </motion.div>
                            ))}
                          </div>

                          {/* Custom amenity input */}
                          <div className="space-y-3">
                            <div className="flex gap-2">
                              <Input
                                value={customAmenity}
                                onChange={(e) => setCustomAmenity(e.target.value)}
                                placeholder="Add custom amenity..."
                                className="flex-1 bg-white/10 border-white/20 text-white placeholder:text-gray-400"
                                onKeyDown={(e) => e.key === 'Enter' && addCustomAmenity()}
                                disabled={isLoading}
                              />
                              <Button
                                onClick={addCustomAmenity}
                                disabled={!customAmenity.trim() || isLoading}
                                variant="outline"
                                size="sm"
                                className="px-4 border-white/20 text-white/70 hover:text-white hover:border-white/40"
                              >
                                <Plus className="w-4 h-4" />
                              </Button>
                            </div>

                            {/* Selected amenities */}
                            {selectedAmenities.length > 0 && (
                              <div className="flex flex-wrap gap-2">
                                {selectedAmenities.map((amenity) => (
                                  <Badge
                                    key={amenity}
                                    variant="secondary"
                                    className="cursor-pointer hover:bg-red-100 bg-blue-500/20 text-blue-300 border-blue-400/30"
                                    onClick={() => !isLoading && toggleAmenity(amenity)}
                                  >
                                    {amenity} ✕
                                  </Badge>
                                ))}
                              </div>
                            )}
                          </div>

                          <div className="text-center">
                            <Button
                              onClick={handleAmenitiesAnswer}
                              disabled={selectedAmenities.length === 0 || isLoading}
                              className="px-8 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl disabled:opacity-50"
                            >
                              Continue with {selectedAmenities.length} amenit{selectedAmenities.length !== 1 ? 'ies' : 'y'}
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <div className="relative">
                          <input
                            type="text"
                            value={textInput}
                            onChange={(e) => setTextInput(e.target.value)}
                            onKeyDown={handleTextSubmit}
                            placeholder={currentQuestion.placeholder}
                            disabled={isLoading}
                            className="w-full px-6 py-4 text-lg rounded-xl border-2 border-gray-200 focus:border-blue-400 focus:outline-none focus:ring-4 focus:ring-blue-100 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                            autoFocus
                          />
                          <motion.button
                            whileHover={{ scale: 1.1 }}
                            whileTap={{ scale: 0.9 }}
                            onClick={() => textInput.trim() && handleAnswer(textInput.trim())}
                            disabled={isLoading}
                            className="absolute right-3 top-1/2 transform -translate-y-1/2 p-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            <Send className="w-4 h-4" />
                          </motion.button>
                        </div>
                      )}
                    </motion.div>
                  )}
                </motion.div>
              ) : (
                <motion.div
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.6 }}
                  className="text-center"
                >
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
                    className="w-20 h-20 bg-gradient-to-r from-green-500 to-emerald-600 rounded-full flex items-center justify-center mx-auto mb-6"
                  >
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: 0.4 }}
                    >
                      ✓
                    </motion.div>
                  </motion.div>

                  <h2 className="text-3xl text-white mb-4">
                    Perfect! Creating Your Itinerary
                  </h2>
                  <p className="text-xl text-gray-300 mb-8">
                    Our AI is crafting a personalized travel plan just for you...
                  </p>

                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                    className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto"
                  />
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </motion.div>
  );
}