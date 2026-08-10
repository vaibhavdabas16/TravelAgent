import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';

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

type MediaItem = { type: 'video' | 'image'; src: string; poster?: string; caption?: string };

const mediaPlaylist: MediaItem[] = [
  { type: 'video', src: beachVideo, poster: rollingHillsImg, caption: 'Beach vibes' },
  { type: 'video', src: oceanWavesVideo, poster: mountainsImg, caption: 'Ocean waves' },
  { type: 'video', src: tropicalCoastVideo, poster: japanImg, caption: 'Tropical coast' },
  { type: 'image', src: rollingHillsImg, caption: 'Rolling hills' },
  { type: 'image', src: mountainsImg, caption: 'Mountain escape' },
  { type: 'image', src: trekkingImg, caption: 'Trekking trails' },
  { type: 'image', src: spaImg, caption: 'Spa day' },
  { type: 'image', src: massageImg, caption: 'Relaxing massage' },
  { type: 'image', src: japanImg, caption: 'Japan' },
  { type: 'image', src: cliffJumpingImg, caption: 'Cliff jumping' }
];

export function MediaShowcaseSection() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setIndex((i) => (i + 1) % mediaPlaylist.length), 8000);
    return () => clearInterval(id);
  }, []);

  const current = mediaPlaylist[index];

  return (
    <section className="relative py-24 bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 overflow-hidden">
      <div className="max-w-7xl mx-auto px-6">
        <div className="text-center mb-10">
          <h2 className="text-4xl lg:text-5xl bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent">Scenes from the Journey</h2>
          <p className="text-slate-600 mt-3">A rotating gallery of relaxing clips and inspiring photos</p>
        </div>

        <div className="relative aspect-video rounded-2xl overflow-hidden shadow-2xl border border-white">
          <AnimatePresence mode="wait">
            {current.type === 'video' ? (
              <motion.video
                key={`video-${index}`}
                className="absolute inset-0 w-full h-full object-cover"
                src={current.src}
                poster={current.poster}
                autoPlay
                muted
                loop
                playsInline
                preload="metadata"
                initial={{ opacity: 0, scale: 1.03 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 1.02 }}
                transition={{ duration: 0.6 }}
              />
            ) : (
              <motion.img
                key={`image-${index}`}
                className="absolute inset-0 w-full h-full object-cover"
                src={current.src}
                alt={current.caption || 'Travel image'}
                loading="eager"
                initial={{ opacity: 0, scale: 1.03 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 1.02 }}
                transition={{ duration: 0.6 }}
              />
            )}
          </AnimatePresence>

          <div className="absolute inset-0 bg-gradient-to-t from-slate-900/30 via-transparent to-transparent" />

          <div className="absolute bottom-0 left-0 right-0 p-6 flex items-center justify-between">
            <div className="px-3 py-1 rounded-full bg-white/70 text-slate-800 text-sm backdrop-blur">
              {current.caption}
            </div>
            <div className="flex gap-2">
              {mediaPlaylist.map((_, i) => (
                <button
                  key={i}
                  aria-label={`Show media ${i + 1}`}
                  onClick={() => setIndex(i)}
                  className={`w-2.5 h-2.5 rounded-full ${i === index ? 'bg-white shadow' : 'bg-white/60'}`}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

export default MediaShowcaseSection;

