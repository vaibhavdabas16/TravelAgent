import { useRef } from 'react';
import { motion, useScroll, useTransform } from 'motion/react';

import cliffJumping from '../../Assets/media/cliff_jumping.jpg';
import trekking from '../../Assets/media/trekking.jpg';
import spa from '../../Assets/media/spa.jpg';
import tropicalVideo from '../../Assets/media/tropical_coast.mp4';

const panels = [
  {
    title: 'Plan your adventures',
    description: 'Our AI helps you discover and organize activities—from thrilling cliff jumps to scenic hikes—tailored to your style.',
    image: cliffJumping,
  },
  {
    title: 'Explore breathtaking trails',
    description: 'Find curated trekking routes, safety tips, and pacing suggestions for solo and group trips.',
    image: trekking,
  },
  {
    title: 'Relax and rejuvenate',
    description: 'Balance your itinerary with spa days and wellness breaks so you return refreshed.',
    image: spa,
  },
];

export function ExperienceScrollSection() {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const { scrollYProgress } = useScroll({ target: rootRef, offset: ["start end", "end start"] });
  console.log('[ExperienceScrollSection] mounted, panels:', panels.length);
  if (rootRef.current) {
    const rect = rootRef.current.getBoundingClientRect();
    console.log('[ExperienceScrollSection] root rect on mount', rect);
  }

  // Pin-and-reveal implementation
  const sectionHeightVh = panels.length * 150; // extra room per panel for smooth transitions

  return (
    <>
      <section ref={rootRef} className={`relative bg-slate-900 border-t border-slate-800 isolate`} style={{ height: `${sectionHeightVh}vh` }}>
        <div className="absolute top-0 left-0 right-0 h-2 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500" />
        <div className="sticky top-0 h-screen overflow-hidden">
          {panels.map((panel, i) => {
          const start = i / panels.length;
          const end = (i + 1) / panels.length;
          
          // Image fades in first, stays visible throughout panel, fades out at end
          const imageOpacity = useTransform(
            scrollYProgress,
            [start - 0.05, start + 0.05, end - 0.1, end],
            [0, 1, 1, 0]
          );
          
          // Title appears after image is visible
          const yTitle = useTransform(scrollYProgress, [start + 0.1, start + 0.25], ['30%', '0%']);
          const titleOpacity = useTransform(scrollYProgress, [start + 0.1, start + 0.25], [0, 1]);
          
          // Description appears after title
          const yDesc = useTransform(scrollYProgress, [start + 0.25, start + 0.4], ['40px', '0px']);
          const descOpacity = useTransform(scrollYProgress, [start + 0.25, start + 0.4], [0, 1]);
          console.log('[ExperienceScrollSection] panel', i, { start, end });

          return (
            <motion.div
              key={panel.title}
              className="absolute inset-0"
              style={{ opacity: imageOpacity }}
            >
              <img 
                src={panel.image} 
                alt={panel.title} 
                className="absolute inset-0 w-full h-full object-cover"
                onError={(e) => {
                  console.error('[ExperienceScrollSection] image failed to load', panel.title, panel.image, e);
                  (e.currentTarget as HTMLImageElement).style.opacity = '0.2';
                }}
                onLoad={() => console.log('[ExperienceScrollSection] image loaded', panel.title, panel.image)}
              />
              <div className="absolute inset-0 bg-black/40" />
              <div className="absolute inset-0 flex items-center justify-center px-6">
                <div className="max-w-3xl w-full text-center">
                  <motion.h3
                    style={{ y: yTitle, opacity: titleOpacity }}
                    className="text-white text-4xl md:text-6xl font-bold drop-shadow"
                  >
                    {panel.title}
                  </motion.h3>
                  <motion.p
                    style={{ y: yDesc, opacity: descOpacity }}
                    className="mt-6 text-gray-200 text-lg md:text-xl"
                  >
                    {panel.description}
                  </motion.p>
                </div>
              </div>
            </motion.div>
          );
          })}
        </div>
      </section>

      {/* Bottom video-backed contact section (separate from scroll section) */}
      <section className="relative bg-slate-900">
        <div className="relative w-full h-[80vh] overflow-hidden">
          <video
            className="absolute inset-0 w-full h-full object-cover"
            src={tropicalVideo}
            autoPlay
            muted
            loop
            playsInline
            preload="auto"
            onError={(e) => {
              console.error('[ExperienceScrollSection] video failed to load', tropicalVideo, e);
            }}
            onLoadedData={() => console.log('[ExperienceScrollSection] video loaded', tropicalVideo)}
          />
          <div className="absolute inset-0 bg-gradient-to-t from-slate-900/80 via-slate-900/50 to-transparent" />

          <div className="absolute inset-0 flex items-end">
            <div className="w-full px-6 md:px-10 pb-10">
              <div className="max-w-5xl mx-auto bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-6 md:p-8 shadow-2xl">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-white">
                  <div>
                    <h4 className="text-xl font-semibold mb-2">Contact</h4>
                    <p className="text-white/90">hello@warp-travel.app</p>
                    <p className="text-white/80">+1 (555) 000-1234</p>
                  </div>
                  <div>
                    <h4 className="text-xl font-semibold mb-2">Follow</h4>
                    <p className="text-white/90">Instagram · Twitter · YouTube</p>
                  </div>
                  <div>
                    <h4 className="text-xl font-semibold mb-2">Company</h4>
                    <p className="text-white/90">Careers · Press · Support</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

export default ExperienceScrollSection;

