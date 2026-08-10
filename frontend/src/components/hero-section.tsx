import { motion, useScroll, useTransform, AnimatePresence, useMotionValue, useSpring } from 'motion/react';
import { useState, useRef, useEffect } from 'react';
import { PlanningInterface } from './planning-interface';
import { SegmentedImageCarousel } from './segmented-image-carousel';
import { Plane, MapPin, Camera, Compass, Mountain, Palmtree, Building2, Car, Sparkles, Globe, Heart, Send } from 'lucide-react';

// Generate random floating icons with independent paths and better distribution
const generateFloatingIcon = (Icon: any, index: number) => {
  const seed = index * 1337; // Use index-based seed for consistent but different positioning
  const pseudoRandom = (offset: number) => ((seed + offset) * 9301 + 49297) % 233280 / 233280;

  return {
    Icon,
    id: index,
    startX: (pseudoRandom(1) - 0.5) * 1000 + (index % 3 - 1) * 300, // Spread across different zones
    startY: (pseudoRandom(2) - 0.5) * 700 + (Math.floor(index / 3) % 3 - 1) * 200,
    endX: (pseudoRandom(3) - 0.5) * 1200 + (index % 5 - 2) * 200,
    endY: (pseudoRandom(4) - 0.5) * 800 + (Math.floor(index / 5) % 3 - 1) * 250,
    duration: pseudoRandom(5) * 6 + 8, // 8-14 seconds
    delay: pseudoRandom(6) * 8 + index * 0.5, // Staggered delays
    rotationSpeed: (pseudoRandom(7) - 0.5) * 720, // -360 to 360 degrees
    scale: 0.7 + pseudoRandom(8) * 0.6, // 0.7-1.3 scale
    opacity: 0.3 + pseudoRandom(9) * 0.5, // 0.3-0.8 opacity
  };
};

const floatingIcons = [
  Plane, MapPin, Camera, Compass, Mountain,
  Palmtree, Building2, Car, Globe, Heart
].map((Icon, index) => generateFloatingIcon(Icon, index));

// Particle system for background
const backgroundParticles = Array.from({ length: 50 }, (_, i) => ({
  id: i,
  x: Math.random() * 100,
  y: Math.random() * 100,
  size: Math.random() * 4 + 1,
  delay: Math.random() * 5,
  duration: Math.random() * 3 + 2,
}));

interface HeroSectionProps {
  onStartPlanning?: (data?: any) => void;
  onViewTripPlan?: (data?: any) => void;
}

export function HeroSection({ onStartPlanning, onViewTripPlan }: HeroSectionProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [isPlanning, setIsPlanning] = useState(false);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [isExpanding, setIsExpanding] = useState(false);
  const [showCursor, setShowCursor] = useState(true);
  const [currentText, setCurrentText] = useState('');
  const [typewriterCompleted, setTypewriterCompleted] = useState(false);
  const [showCarousel, setShowCarousel] = useState(false);
  const [currentDestination, setCurrentDestination] = useState<any>(null);

  const ref = useRef<HTMLDivElement>(null);
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const springX = useSpring(mouseX, { stiffness: 100, damping: 20 });
  const springY = useSpring(mouseY, { stiffness: 100, damping: 20 });

  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"]
  });

  const y = useTransform(scrollYProgress, [0, 1], [0, -300]);
  const opacity = useTransform(scrollYProgress, [0, 0.8], [1, 0]);
  const scale = useTransform(scrollYProgress, [0, 0.8], [1, 0.9]);

  // Handle mouse movement for parallax
  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = ref.current?.getBoundingClientRect();
    if (rect) {
      const centerX = rect.left + rect.width / 2;
      const centerY = rect.top + rect.height / 2;
      mouseX.set((e.clientX - centerX) * 0.1);
      mouseY.set((e.clientY - centerY) * 0.1);
    }
  };

  // Typewriter effect for main title
  const titleText = "Your next adventure awaits";
  const subtitleText = "Powered by AI, crafted for you";

  useEffect(() => {
    setTypewriterCompleted(false);
    let cursorTimer: any;
    let typingInterval: any;

    const startTypingTimer = setTimeout(() => {
      let index = 0;
      setShowCursor(true); // Set cursor to solid initially
      typingInterval = setInterval(() => {
        if (index < titleText.length) {
          setCurrentText(titleText.slice(0, index + 1));
          index++;
        } else {
          clearInterval(typingInterval);
          setTypewriterCompleted(true);
          // Start blinking cursor *after* typing is complete
          cursorTimer = setInterval(() => {
            setShowCursor(prev => !prev);
          }, 530);
        }
      }, 80);
    }, 1000); // Delay before typing starts to sync with other animations

    return () => {
      clearTimeout(startTypingTimer);
      if (typingInterval) clearInterval(typingInterval);
      if (cursorTimer) clearInterval(cursorTimer);
    };
  }, []);


  // Set full text immediately after typewriter completes (for subsequent slides)
  useEffect(() => {
    if (typewriterCompleted) {
      setCurrentText(titleText);
    }
  }, [currentDestination, typewriterCompleted]);

  // Start carousel after initial animations complete
  useEffect(() => {
    const timer = setTimeout(() => {
      setShowCarousel(true);
    }, 5000); // 5 seconds delay

    return () => clearTimeout(timer);
  }, []);

  const handleSearch = async (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && searchQuery.trim()) {
      setIsTransitioning(true);

      // Smooth transition animation
      setTimeout(() => {
        setIsExpanding(true);
      }, 300);

      // Start planning flow with user's query
      setTimeout(() => {
        if (onStartPlanning) {
          onStartPlanning({
            query: searchQuery,
            destination: currentDestination.name
          });
        }
        setIsTransitioning(false);
        setIsExpanding(false);
      }, 1800);
    }
  };

  const handleClosePlanning = () => {
    setIsPlanning(false);
    setSearchQuery('');
    setIsExpanding(false);
    setIsTransitioning(false);
  };

  const handleDestinationChange = (destination: any) => {
    setCurrentDestination(destination);
  };

  return (
    <>
      <div
        ref={ref}
        className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900"
        onMouseMove={handleMouseMove}
      >
        {/* Segmented Image Carousel Background */}
        <AnimatePresence>
          {showCarousel && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 2, ease: "easeInOut" }}
              className="absolute inset-0 z-[5]"
            >
              <SegmentedImageCarousel startDelay={0} onDestinationChange={handleDestinationChange} />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Original background with fade out when carousel starts */}
        <motion.div
          animate={{
            opacity: showCarousel ? 0 : 1,
            scale: showCarousel ? 1.1 : 1
          }}
          transition={{ duration: 2, ease: "easeInOut" }}
          className="absolute inset-0 z-[1] bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900"
        />

        {/* Animated background grid - fades with original background */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{
            opacity: showCarousel ? 0 : 0.1
          }}
          transition={{ duration: 2 }}
          className="absolute inset-0 z-[2]"
          style={{
            backgroundImage: `
              linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
              linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
            `,
            backgroundSize: '50px 50px',
          }}
        />

        {/* Background particles - fade out when carousel starts */}
        <AnimatePresence>
          {!showCarousel && backgroundParticles.map((particle) => (
            <motion.div
              key={particle.id}
              className="absolute rounded-full bg-white"
              initial={{ opacity: 0, scale: 0 }}
              animate={{
                opacity: [0, 0.6, 0],
                scale: [0, 1, 0],
                y: [0, -100, -200]
              }}
              exit={{ opacity: 0, scale: 0 }}
              transition={{
                duration: particle.duration,
                delay: particle.delay,
                repeat: Infinity,
                ease: "easeInOut"
              }}
              style={{
                left: `${particle.x}%`,
                top: `${particle.y}%`,
                width: particle.size,
                height: particle.size,
              }}
            />
          ))}
        </AnimatePresence>

        {/* Independent floating travel icons - fade out when carousel starts */}
        <AnimatePresence>
          {!showCarousel && floatingIcons.map((item) => {
            const Icon = item.Icon;
            return (
              <motion.div
                key={item.id}
                initial={{
                  opacity: 0,
                  scale: 0,
                  x: item.startX,
                  y: item.startY,
                  rotate: 0
                }}
                animate={{
                  opacity: [0, item.opacity, item.opacity, 0],
                  scale: [0, item.scale, item.scale, 0],
                  x: [item.startX, item.endX, item.startX],
                  y: [item.startY, item.endY, item.startY],
                  rotate: [0, item.rotationSpeed, item.rotationSpeed * 2]
                }}
                exit={{ opacity: 0, scale: 0 }}
                transition={{
                  duration: item.duration,
                  delay: item.delay + 1,
                  repeat: Infinity,
                  ease: "easeInOut",
                  times: [0, 0.1, 0.9, 1] // Spend most time visible and moving
                }}
                className="absolute pointer-events-none"
                style={{
                  left: '50%',
                  top: '50%',
                  x: springX,
                  y: springY
                }}
              >
                <motion.div
                  animate={{
                    scale: [1, 1.1, 1],
                  }}
                  transition={{
                    duration: 3 + Math.random() * 2,
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: Math.random() * 2
                  }}
                  className="p-3 bg-gradient-to-br from-white/15 to-white/5 backdrop-blur-sm rounded-2xl border border-white/20 shadow-lg"
                >
                  <Icon className="w-6 h-6 text-white" />
                </motion.div>
              </motion.div>
            );
          })}
        </AnimatePresence>

        {/* Main content */}
        <motion.div
          style={{ y, opacity, scale }}
          animate={{
            opacity: isExpanding ? 0 : 1,
            scale: isExpanding ? 0.95 : 1,
            filter: isExpanding ? "blur(4px)" : "blur(0px)"
          }}
          transition={{
            duration: 0.4,
            ease: "easeOut"
          }}
          className="relative z-20 text-center max-w-4xl mx-auto px-8"
        >
          {/* Dynamic background overlay that adapts to carousel colors */}
          <AnimatePresence>
            {showCarousel && currentDestination && (
              <motion.div
                key={currentDestination.id}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 1.1 }}
                transition={{ duration: 1, delay: 0.2, ease: "easeOut" }}
                className="absolute inset-0 backdrop-blur-xl rounded-3xl border border-white/10 shadow-2xl -z-10"
                style={{
                  background: `linear-gradient(145deg, 
                    ${currentDestination.colorPalette.primary}08 0%, 
                    ${currentDestination.colorPalette.secondary}06 50%, 
                    ${currentDestination.colorPalette.accent}04 100%), 
                    radial-gradient(circle at 30% 30%, ${currentDestination.colorPalette.primary}12 0%, transparent 60%),
                    radial-gradient(circle at 70% 70%, ${currentDestination.colorPalette.secondary}08 0%, transparent 60%)`,
                  boxShadow: `inset 0 1px 0 rgba(255, 255, 255, 0.1), 
                              0 20px 40px rgba(0, 0, 0, 0.1), 
                              0 0 80px ${currentDestination.colorPalette.primary}20`
                }}
              />
            )}
          </AnimatePresence>

          {/* Static glass background for when carousel isn't showing */}
          <AnimatePresence>
            {!showCarousel && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 1.1 }}
                transition={{ duration: 1, ease: "easeOut" }}
                className="absolute inset-0 backdrop-blur-xl rounded-3xl border border-white/10 shadow-2xl -z-10"
                style={{
                  background: `linear-gradient(145deg, 
                    rgba(59, 130, 246, 0.08) 0%, 
                    rgba(139, 92, 246, 0.06) 50%, 
                    rgba(236, 72, 153, 0.04) 100%), 
                    radial-gradient(circle at 30% 30%, rgba(59, 130, 246, 0.12) 0%, transparent 60%),
                    radial-gradient(circle at 70% 70%, rgba(139, 92, 246, 0.08) 0%, transparent 60%)`,
                  boxShadow: `inset 0 1px 0 rgba(255, 255, 255, 0.1), 
                              0 20px 40px rgba(0, 0, 0, 0.1), 
                              0 0 80px rgba(59, 130, 246, 0.2)`
                }}
              />
            )}
          </AnimatePresence>


          {/* Main title with typewriter effect */}
          <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1, delay: 0.8, ease: "easeOut" }}
            className="mb-8"
          >
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-4 relative">
              <motion.span
                key={currentDestination?.id || 'default'}
                initial={{
                  backgroundSize: typewriterCompleted ? "100% 100%" : "0% 100%",
                  opacity: typewriterCompleted ? 0 : 1
                }}
                animate={{
                  backgroundSize: "100% 100%",
                  opacity: 1
                }}
                transition={{
                  duration: typewriterCompleted ? 0.6 : 2,
                  delay: typewriterCompleted ? 0.2 : 2,
                  ease: "easeInOut"
                }}
                className="bg-gradient-to-r bg-clip-text text-transparent"
                style={{
                  backgroundImage: showCarousel && currentDestination
                    ? currentDestination.colorPalette.gradient
                    : "linear-gradient(90deg, #60A5FA, #A78BFA, #F472B6)",
                  backgroundRepeat: "no-repeat",
                }}
              >
                {currentText}
              </motion.span>
              <motion.span
                animate={{ opacity: showCursor ? 1 : 0 }}
                style={{
                  color: showCarousel && currentDestination
                    ? currentDestination.colorPalette.primary
                    : "#60A5FA"
                }}
              >
                |
              </motion.span>
            </h1>
          </motion.div>

          {/* Animated subtitle */}
          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 3, ease: "easeOut" }}
            className="text-lg sm:text-xl mb-12 max-w-xl mx-auto"
            style={{
              color: showCarousel && currentDestination
                ? currentDestination.colorPalette.text
                : "#D1D5DB"
            }}
          >
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 1, delay: 3.5 }}
            >
              {subtitleText}
            </motion.span>
          </motion.p>

          {/* Enhanced search input */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 50 }}
            animate={{
              opacity: isExpanding ? 0 : 1,
              scale: isExpanding ? 0.9 : 1,
              y: isExpanding ? -20 : 0
            }}
            transition={{
              duration: isExpanding ? 0.4 : 1.2,
              delay: isExpanding ? 0 : 4,
              ease: "easeOut"
            }}
            className="relative max-w-2xl mx-auto"
          >
            {/* Enhanced glowing background effect that adapts to carousel colors */}
            <motion.div
              key={currentDestination?.id || 'default'}
              initial={{ opacity: 0 }}
              animate={{
                opacity: showCarousel ? (isTransitioning ? 0.9 : 0.7) : (isTransitioning ? 0.8 : 0.5),
              }}
              transition={{
                duration: 0.6,
                delay: 4.5,
                ease: "easeOut"
              }}
              className="absolute -inset-1 rounded-3xl blur-xl"
              style={{
                background: showCarousel && currentDestination
                  ? currentDestination.colorPalette.gradient
                  : "linear-gradient(to right, #3B82F6, #8B5CF6, #EC4899)"
              }}
            />

            <div className="relative">
              <motion.input
                key={currentDestination?.id || 'default'}
                whileFocus={{ scale: 1.02 }}
                initial={{
                  backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  borderColor: 'rgba(255, 255, 255, 0.2)'
                }}
                animate={{
                  scale: isTransitioning ? 1.08 : 1,
                  backgroundColor: showCarousel
                    ? 'rgba(0, 0, 0, 0.4)'
                    : 'rgba(255, 255, 255, 0.1)',
                  borderColor: showCarousel && currentDestination
                    ? `${currentDestination.colorPalette.primary}40`
                    : 'rgba(255, 255, 255, 0.2)'
                }}
                transition={{
                  duration: 0.6,
                  ease: "easeOut"
                }}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={handleSearch}
                placeholder="Describe your dream destination..."
                className="w-full pl-12 pr-20 py-5 text-lg backdrop-blur-xl border-2 rounded-2xl text-white placeholder-gray-300 focus:outline-none relative z-10"
                onFocus={(e) => {
                  e.target.style.borderColor = showCarousel && currentDestination
                    ? currentDestination.colorPalette.primary
                    : '#60A5FA';
                  e.target.style.boxShadow = `0 0 0 4px ${showCarousel && currentDestination
                    ? currentDestination.colorPalette.primary + '33'
                    : 'rgba(96, 165, 250, 0.2)'}`;
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = showCarousel && currentDestination
                    ? `${currentDestination.colorPalette.primary}40`
                    : 'rgba(255, 255, 255, 0.2)';
                  e.target.style.boxShadow = 'none';
                }}
                disabled={isTransitioning}
              />

              {/* Search icon */}
              <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 4.5 }}
                className="absolute left-4 top-1/2 transform -translate-y-1/2"
              >
                <motion.div
                  animate={{
                    rotate: isTransitioning ? 360 : 0,
                    scale: isTransitioning ? [1, 1.2, 1] : 1
                  }}
                  transition={{
                    rotate: { duration: 2, ease: "easeInOut" },
                    scale: { duration: 0.5, repeat: isTransitioning ? Infinity : 0 }
                  }}
                >
                  {isTransitioning ? (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      className="w-6 h-6 border-2 border-blue-400 border-t-transparent rounded-full"
                    />
                  ) : (
                    <Globe className="w-6 h-6 text-gray-300" />
                  )}
                </motion.div>
              </motion.div>

              {/* Enter hint */}
              <AnimatePresence>
                {!isTransitioning && searchQuery && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.8 }}
                    className="absolute right-4 top-1/2 transform -translate-y-1/2"
                  >
                    <motion.div
                      animate={{ x: [0, 5, 0] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                      className="flex items-center gap-2 px-3 py-1 rounded-lg border"
                      style={{
                        backgroundColor: showCarousel && currentDestination
                          ? `${currentDestination.colorPalette.primary}33`
                          : 'rgba(59, 130, 246, 0.125)',
                        borderColor: showCarousel && currentDestination
                          ? `${currentDestination.colorPalette.primary}4D`
                          : 'rgba(96, 165, 250, 0.3)'
                      }}
                    >
                      <Send
                        className="w-4 h-4"
                        style={{
                          color: showCarousel && currentDestination
                            ? currentDestination.colorPalette.text
                            : '#93C5FD'
                        }}
                      />
                      <span
                        className="text-sm"
                        style={{
                          color: showCarousel && currentDestination
                            ? currentDestination.colorPalette.text
                            : '#93C5FD'
                        }}
                      >
                        Enter
                      </span>
                    </motion.div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>

          {/* Animated hint text */}
          <AnimatePresence>
            {!isTransitioning && (
              <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.6, delay: 5, ease: "easeOut" }}
                className="mt-6 text-lg"
                style={{
                  color: showCarousel && currentDestination
                    ? `${currentDestination.colorPalette.text}CC`
                    : '#9CA3AF'
                }}
              >
                <motion.span
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  Press Enter to begin your journey
                </motion.span>
              </motion.p>
            )}
          </AnimatePresence>

          {/* Transition effects */}
          <AnimatePresence>
            {isTransitioning && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: 0.8 }}
                className="mt-12 text-center"
              >
                <motion.div
                  animate={{
                    scale: [1, 1.1, 1],
                    rotate: [0, 5, -5, 0]
                  }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="text-2xl font-medium mb-4"
                  style={{
                    color: showCarousel && currentDestination
                      ? currentDestination.colorPalette.text
                      : '#93C5FD'
                  }}
                >
                  ✨ Crafting your perfect adventure...
                </motion.div>
                <motion.p
                  animate={{ opacity: [0.7, 1, 0.7] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="text-lg"
                  style={{
                    color: showCarousel && currentDestination
                      ? `${currentDestination.colorPalette.text}AA`
                      : '#9CA3AF'
                  }}
                >
                  Our AI is analyzing millions of possibilities
                </motion.p>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>

        {/* Smooth background transition effects */}
        <AnimatePresence>
          {isTransitioning && !isExpanding && (
            <>
              {/* Subtle expanding rings */}
              {[1, 2, 3].map((ring) => (
                <motion.div
                  key={ring}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{
                    opacity: [0, 0.4, 0],
                    scale: [0.8, 2.5, 4]
                  }}
                  exit={{ opacity: 0 }}
                  transition={{
                    duration: 0.8,
                    delay: ring * 0.05,
                    ease: [0.25, 0.1, 0.25, 1]
                  }}
                  className="absolute rounded-full border"
                  style={{
                    borderColor: showCarousel && currentDestination
                      ? `${currentDestination.colorPalette.primary}33`
                      : 'rgba(96, 165, 250, 0.2)',
                    left: '50%',
                    top: '50%',
                    transform: 'translate(-50%, -50%)',
                    width: '80px',
                    height: '80px'
                  }}
                />
              ))}

              {/* Gentle particle burst */}
              {Array.from({ length: 12 }).map((_, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{
                    opacity: [0, 0.8, 0],
                    scale: [0, 1, 0],
                    x: Math.cos((i / 12) * Math.PI * 2) * 150,
                    y: Math.sin((i / 12) * Math.PI * 2) * 150
                  }}
                  exit={{ opacity: 0 }}
                  transition={{
                    duration: 0.6,
                    delay: i * 0.02,
                    ease: "easeOut"
                  }}
                  className="absolute w-1.5 h-1.5 rounded-full"
                  style={{
                    backgroundColor: showCarousel && currentDestination
                      ? `${currentDestination.colorPalette.primary}99`
                      : 'rgba(96, 165, 250, 0.6)',
                    left: '50%',
                    top: '50%'
                  }}
                />
              ))}
            </>
          )}
        </AnimatePresence>

        {/* Smooth full screen expansion overlay */}
        <AnimatePresence>
          {isExpanding && (
            <motion.div
              initial={{
                clipPath: "circle(0% at 50% 50%)"
              }}
              animate={{
                clipPath: "circle(100% at 50% 50%)"
              }}
              exit={{
                opacity: 0
              }}
              transition={{
                duration: 1.2,
                ease: [0.25, 0.1, 0.25, 1]
              }}
              className="fixed inset-0 bg-gradient-to-br from-blue-500 via-purple-600 to-pink-600 z-40 flex items-center justify-center"
            >
              {/* Smooth loading content */}
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -30 }}
                transition={{
                  delay: 0.6,
                  duration: 0.5,
                  ease: "easeOut"
                }}
                className="text-center text-white"
              >
                <motion.div
                  animate={{
                    scale: [1, 1.05, 1]
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                  className="text-4xl font-bold mb-4"
                >
                  ✨ Crafting Your Journey
                </motion.div>
                <motion.p
                  animate={{ opacity: [0.8, 1, 0.8] }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                  className="text-xl"
                >
                  Analyzing your preferences...
                </motion.p>

                {/* Smooth progress indicator */}
                <motion.div
                  className="mt-8 w-32 h-1 bg-white/20 rounded-full overflow-hidden mx-auto"
                >
                  <motion.div
                    initial={{ x: "-100%" }}
                    animate={{ x: "100%" }}
                    transition={{
                      duration: 1.2,
                      ease: "easeInOut",
                      repeat: Infinity,
                      repeatDelay: 0.3
                    }}
                    className="h-full w-1/3 bg-white rounded-full"
                  />
                </motion.div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0, y: 100 }}
          animate={{ opacity: isTransitioning ? 0 : 1, y: isTransitioning ? 100 : 0 }}
          transition={{ duration: 1, delay: 6, ease: "easeOut" }}
          className="absolute bottom-8 left-1/2 transform -translate-x-1/2 z-30"
        >
          <motion.div
            animate={{ y: [0, -15, 0] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            className="w-6 h-10 border-2 border-white/30 rounded-full flex justify-center backdrop-blur-sm"
          >
            <motion.div
              animate={{ y: [0, 16, 0] }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
              className="w-1 h-3 bg-white/50 rounded-full mt-2"
            />
          </motion.div>
        </motion.div>
      </div>

      {/* Planning Interface Overlay */}
      <AnimatePresence>
        {isPlanning && (
          <PlanningInterface
            initialQuery={searchQuery}
            onClose={handleClosePlanning}
            onViewTripPlan={onViewTripPlan}
          />
        )}
      </AnimatePresence>
    </>
  );
}