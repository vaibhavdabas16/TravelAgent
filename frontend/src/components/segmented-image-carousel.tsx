import { motion, AnimatePresence } from 'motion/react';
import { useState, useEffect } from 'react';

// Import assets directly for Vite to handle bundling
import indiaLandscape from '../../Assets/India/landscape.png';
import indiaSky from '../../Assets/India/sky.png';
import indiaBuilding from '../../Assets/India/building.png';
// Landing background media (videos + images)
import beachVideo from '../../Assets/media/beach.mp4';
import oceanWavesVideo from '../../Assets/media/ocean_waves.mp4';
import tropicalCoastVideo from '../../Assets/media/tropical_coast.mp4';
import japanImg from '../../Assets/media/Japan.jpg';
import spaImg from '../../Assets/media/spa.jpg';
import massageImg from '../../Assets/media/massage.jpg';
import trekkingImg from '../../Assets/media/trekking.jpg';
import mountainsImg from '../../Assets/media/mountains.jpg';
import rollingHillsImg from '../../Assets/media/rolling_hills.jpg';
import cliffJumpingImg from '../../Assets/media/cliff_jumping.jpg';


// Travel destinations with segmented animation data
const destinations = [
  {
    id: 1,
    name: 'INDIA',
    assets: {
      landscape: indiaLandscape,
      sky: indiaSky,
      building: indiaBuilding,
    },
    textPosition: { x: '50%', y: '10%' }, // Centered at top
    colorPalette: {
      primary: '#8E44AD', // Royal purple
      secondary: '#9B59B6', // Light purple
      accent: '#E8D5E8', // Very light purple
      gradient: 'linear-gradient(145deg, #2a1d3c, #4a3b5c)',
      text: '#F5EFFF' // Lavender white
    },
    parallaxElements: [
      { type: 'reflection', count: 1, speed: 0.1 },
      { type: 'birds', count: 6, speed: 0.8 }
    ]
  },
];

interface SegmentedImageCarouselProps {
  startDelay?: number; // Delay before carousel starts (default 5000ms)
  onDestinationChange?: (destination: typeof destinations[0]) => void; // Callback for destination changes
}

export function SegmentedImageCarousel({ startDelay = 5000, onDestinationChange }: SegmentedImageCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isActive, setIsActive] = useState(false);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [showIntro, setShowIntro] = useState(true);
  const [mediaIndex, setMediaIndex] = useState(0);

  // Playlist combining videos and images
  const backgroundMedia: Array<{ type: 'video' | 'image'; src: string; poster?: string }> = [
    { type: 'video', src: beachVideo, poster: rollingHillsImg },
    { type: 'video', src: oceanWavesVideo, poster: mountainsImg },
    { type: 'video', src: tropicalCoastVideo, poster: japanImg },
    { type: 'image', src: rollingHillsImg },
    { type: 'image', src: mountainsImg },
    { type: 'image', src: trekkingImg },
    { type: 'image', src: spaImg },
    { type: 'image', src: massageImg },
    { type: 'image', src: japanImg },
    { type: 'image', src: cliffJumpingImg }
  ];

  // Start carousel after delay
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsActive(true);
      // Hide intro after first animation completes
      setTimeout(() => setShowIntro(false), 3000);
    }, startDelay);

    return () => clearTimeout(timer);
  }, [startDelay]);

  // Auto-rotate carousel
  useEffect(() => {
    if (!isActive) return;

    const interval = setInterval(() => {
      setIsTransitioning(true);
      setTimeout(() => {
        setCurrentIndex((prev) => (prev + 1) % destinations.length);
        setMediaIndex((prev) => (prev + 1) % backgroundMedia.length);
        setIsTransitioning(false);
      }, 600);
    }, 10000); // 10 seconds per slide

    return () => clearInterval(interval);
  }, [isActive]);

  // Notify parent of destination changes
  useEffect(() => {
    if (onDestinationChange && isActive) {
      onDestinationChange(destinations[currentIndex]);
    }
  }, [currentIndex, isActive, onDestinationChange]);

  if (!isActive) return (
    // Render the intro overlay centered, before the carousel is active
    <AnimatePresence>
      {showIntro && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 1, ease: "easeInOut" }}
            className="absolute inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[100]"
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 1.1, opacity: 0 }}
              transition={{ duration: 1, ease: "easeOut" }}
              className="text-center text-white"
            >
              <motion.h3
                animate={{ 
                  scale: [1, 1.05, 1],
                  textShadow: [
                    '0 0 20px rgba(255,255,255,0.5)',
                    '0 0 30px rgba(255,255,255,0.8)',
                    '0 0 20px rgba(255,255,255,0.5)'
                  ]
                }}
                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                className="text-4xl md:text-6xl lg:text-7xl font-bold mb-4 tracking-wider"
              >
                EXPLORE THE WORLD
              </motion.h3>
              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5, duration: 0.8 }}
                className="text-xl md:text-2xl text-gray-200"
              >
                Immersive travel experiences await
              </motion.p>
            </motion.div>
          </motion.div>
        )}
    </AnimatePresence>
  );

  const currentDestination = destinations[currentIndex];
  const imageSegments = [
    { id: 'landscape', src: currentDestination.assets.landscape, delay: 0.2 },
    { id: 'sky', src: currentDestination.assets.sky, delay: 0.5 },
    { id: 'building', src: currentDestination.assets.building, delay: 0.8 }
  ];

  return (
    <div className="absolute inset-0 overflow-hidden">
      <AnimatePresence mode="wait">
        <motion.div
          key={currentIndex}
          className="absolute inset-0"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 1, ease: "easeInOut" }}
        >
          {/* Background Media Layer (videos/images) */}
          <div className="absolute inset-0">
            {backgroundMedia[mediaIndex]?.type === 'video' ? (
              <video
                key={`video-${mediaIndex}`}
                className="absolute inset-0 w-full h-full object-cover"
                src={backgroundMedia[mediaIndex].src}
                poster={backgroundMedia[mediaIndex].poster}
                autoPlay
                muted
                loop
                playsInline
                preload="metadata"
              />
            ) : (
              <img
                key={`image-${mediaIndex}`}
                className="absolute inset-0 w-full h-full object-cover"
                src={backgroundMedia[mediaIndex].src}
                alt="Scenic travel background"
                loading="eager"
              />
            )}
          </div>

          {/* Dynamic Gradient Background */}
          <motion.div
            className="absolute inset-0"
            style={{ background: currentDestination.colorPalette.gradient }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.6 }}
            transition={{ duration: 2, ease: 'easeIn' }}
          />
          
          {/* Image Segment Animations */}
          {imageSegments.map(segment => (
            <motion.div
              key={segment.id}
              className="absolute inset-0 w-full h-full"
              initial={{ clipPath: 'polygon(0% 100%, 100% 100%, 100% 100%, 0% 100%)' }}
              animate={{ clipPath: 'polygon(0% 0%, 100% 0%, 100% 100%, 0% 100%)' }}
              exit={{ clipPath: 'polygon(0% 0%, 100% 0%, 100% 0%, 0% 0%)'}}
              transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1], delay: segment.delay }}
            >
              <img src={segment.src} alt={`${currentDestination.name} ${segment.id}`} className="absolute inset-0 w-full h-full object-cover"/>
            </motion.div>
          ))}
          
          {/* Destination Text */}
          <motion.div
            initial={{ opacity: 0, y: 30, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.9 }}
            transition={{ duration: 0.6, ease: "easeOut", delay: 1.2 }}
            className="absolute z-10 pointer-events-none"
            style={{
              left: currentDestination.textPosition.x,
              top: currentDestination.textPosition.y,
              transform: 'translate(-50%, -50%)'
            }}
          >
             <motion.h2
                animate={{ 
                    textShadow: [
                    `0 0 20px ${currentDestination.colorPalette.primary}`,
                    `0 0 40px ${currentDestination.colorPalette.secondary}`,
                    `0 0 20px ${currentDestination.colorPalette.primary}`
                    ]
                }}
                transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-wider select-none"
                style={{
                    fontFamily: 'system-ui, sans-serif',
                    color: currentDestination.colorPalette.text,
                    textStroke: `2px ${currentDestination.colorPalette.primary}`,
                    WebkitTextStroke: `2px ${currentDestination.colorPalette.primary}`,
                    mixBlendMode: 'screen',
                    filter: `drop-shadow(0 0 10px ${currentDestination.colorPalette.primary})`
                }}
                >
                {currentDestination.name}
            </motion.h2>
          </motion.div>

          {/* Parallax Elements */}
          {currentDestination.parallaxElements.map((element, index) => (
            <ParallaxElement
              key={`${currentIndex}-${index}`}
              type={element.type}
              count={element.count}
              speed={element.speed}
              delay={1.5 + index * 0.2}
            />
          ))}
        </motion.div>
      </AnimatePresence>

      {/* Slide Indicators */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 3, duration: 0.5 }}
        className="absolute bottom-20 left-1/2 transform -translate-x-1/2 flex space-x-3 z-10"
      >
        {destinations.map((_, index) => (
          <motion.div
            key={index}
            animate={{
              scale: index === currentIndex ? 1.2 : 1,
              opacity: index === currentIndex ? 1 : 0.5
            }}
            transition={{ duration: 0.3 }}
            className={`w-3 h-3 rounded-full border-2 border-white ${
              index === currentIndex ? 'bg-white' : 'bg-transparent'
            }`}
          />
        ))}
      </motion.div>
    </div>
  );
}

// Parallax Element Component
interface ParallaxElementProps {
  type: string;
  count: number;
  speed: number;
  delay: number;
}

function ParallaxElement({ type, count, speed, delay }: ParallaxElementProps) {
  const elements = Array.from({ length: count }, (_, i) => ({
    id: i,
    x: Math.random() * 100,
    y: Math.random() * 100,
    size: Math.random() * 20 + 10,
    duration: 10 + Math.random() * 10,
    delay: delay + i * 0.5
  }));

  const getElementStyle = (type: string) => {
    switch (type) {
      case 'clouds':
        return 'bg-white/20 rounded-full blur-sm';
      case 'mist':
        return 'bg-gray-300/10 rounded-full blur-md';
      case 'lights':
        return 'bg-yellow-300/30 rounded-full blur-sm';
      case 'sparkles':
        return 'bg-white/40 rounded-full';
      case 'sand':
        return 'bg-yellow-600/20 rounded-full blur-sm';
      case 'heat':
        return 'bg-orange-300/15 rounded-full blur-lg';
      case 'reflection':
        return 'bg-blue-200/10 rounded-full blur-md';
      case 'birds':
        return 'bg-black/30 rounded-full';
      case 'eagles':
        return 'bg-brown-600/40 rounded-full';
      case 'dust':
        return 'bg-orange-200/20 rounded-full blur-sm';
      default:
        return 'bg-white/20 rounded-full';
    }
  };

  return (
    <>
      {elements.map((element) => (
        <motion.div
          key={element.id}
          initial={{ 
            opacity: 0, 
            x: `${element.x}%`,
            y: `${element.y}%`
          }}
          animate={{ 
            opacity: [0, 0.6, 0.6, 0],
            x: [`${element.x}%`, `${element.x + speed * 20}%`],
            y: [`${element.y}%`, `${element.y - speed * 10}%`]
          }}
          transition={{
            duration: element.duration,
            delay: element.delay,
            repeat: Infinity,
            ease: "linear"
          }}
          className={`absolute pointer-events-none ${getElementStyle(type)}`}
          style={{
            width: element.size,
            height: element.size
          }}
        />
      ))}
    </>
  );
}

// Export destinations for external use
export { destinations };