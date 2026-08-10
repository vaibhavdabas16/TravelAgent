import { motion, useScroll, useTransform } from 'motion/react';
import { useRef } from 'react';
import cliffJumping from '../../Assets/media/cliff_jumping.jpg';
import spa from '../../Assets/media/spa.jpg';
import japan from '../../Assets/media/Japan.jpg';

const features = [
  {
    title: 'Plan your adventures',
    description: 'Our AI-powered planner helps you discover and organize activities, from thrilling cliff jumps to serene mountain treks. Customize your itinerary to match your unique travel style and create unforgettable memories.',
    image: cliffJumping,
  },
  {
    title: 'Relax and rejuvenate',
    description: 'Find the perfect moments to unwind. Whether it’s a peaceful day at the spa or a relaxing massage, our app helps you schedule downtime to make your trip both exciting and refreshing.',
    image: spa,
  },
  {
    title: 'Explore breathtaking landscapes',
    description: 'From the rolling hills of the countryside to the majestic mountains of Japan, explore the world’s most stunning landscapes. Our app provides curated suggestions for scenic spots and hidden gems.',
    image: japan,
  },
];

export function FeatureHighlightSection() {
  const targetRef = useRef(null);
  const { scrollYProgress } = useScroll({ target: targetRef });

  return (
    <section ref={targetRef} className="relative h-[300vh] bg-slate-900">
      <div className="sticky top-0 h-screen flex items-center justify-center overflow-hidden">
        {features.map((feature, i) => {
          const targetScale = 1 - ((features.length - i - 0.5) * 0.1);
          const scale = useTransform(scrollYProgress, [i / features.length, (i + 1) / features.length], [1, targetScale]);
          const opacity = useTransform(scrollYProgress, [(i + 0.5) / features.length, (i + 1) / features.length], [1, 0]);

          return (
            <motion.div
              key={i}
              style={{ 
                backgroundImage: `url(${feature.image})`,
                scale,
                opacity,
              }}
              className="absolute inset-0 w-full h-full bg-cover bg-center"
            />
          );
        })}
        <div className="absolute inset-0 bg-black/50" />
        <div className="relative z-10 max-w-4xl mx-auto px-8 text-center">
            {features.map((feature, i) => {
                const opacity = useTransform(scrollYProgress, [i / features.length, (i + 0.25) / features.length, (i + 0.75) / features.length, (i + 1) / features.length], [0, 1, 1, 0]);
                const y = useTransform(scrollYProgress, [i / features.length, (i + 0.25) / features.length], ['30px', '0px']);

                return (
                    <motion.div
                        key={i}
                        style={{ opacity, y }}
                        className="absolute inset-0 flex flex-col items-center justify-center text-white"
                    >
                        <h2 className="text-4xl md:text-6xl font-bold mb-4">{feature.title}</h2>
                        <p className="max-w-2xl text-lg md:text-xl">{feature.description}</p>
                    </motion.div>
                );
            })}
        </div>
      </div>
    </section>
  );
}