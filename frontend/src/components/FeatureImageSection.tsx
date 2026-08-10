import { motion } from 'motion/react';
import { Sparkles, Map, Heart, Calendar, Users } from 'lucide-react';

// Import media assets
import mountains from '../../Assets/media/mountains.jpg';
import japanImg from '../../Assets/media/Japan.jpg';
import rollingHills from '../../Assets/media/rolling_hills.jpg';
import massage from '../../Assets/media/massage.jpg';
import beachVideo from '../../Assets/media/beach.mp4';

const features = [
  {
    id: 1,
    title: 'AI-Powered Planning',
    description: 'Let our intelligent AI create personalized itineraries tailored to your preferences, budget, and travel style. Get instant recommendations for the perfect trip.',
    icon: Sparkles,
    image: mountains,
    type: 'image',
  },
  {
    id: 2,
    title: 'Discover Hidden Gems',
    description: 'Explore authentic local experiences and off-the-beaten-path destinations curated by our global community of travelers and locals.',
    icon: Map,
    image: japanImg,
    type: 'image',
  },
  {
    id: 3,
    title: 'Seamless Collaboration',
    description: 'Plan trips together with friends and family. Share itineraries, vote on activities, and keep everyone in sync with real-time updates.',
    icon: Users,
    image: rollingHills,
    type: 'image',
  },
  {
    id: 4,
    title: 'Wellness & Relaxation',
    description: 'Balance adventure with wellness. Our app suggests spa experiences, yoga retreats, and mindful activities to rejuvenate your mind and body.',
    icon: Heart,
    image: massage,
    type: 'image',
  },
  {
    id: 5,
    title: 'Smart Scheduling',
    description: 'Optimize your time with intelligent scheduling. Our AI considers travel times, opening hours, and local events to maximize your experience.',
    icon: Calendar,
    video: beachVideo,
    type: 'video',
  },
];

export function FeatureImageSection() {
  console.log('[FeatureImageSection] Rendering component');
  
  return (
    <section className="relative bg-white">
      {/* Section Header */}
      <div className="py-16 bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50">
        <div className="max-w-7xl mx-auto px-6 text-center">
          <motion.h2
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-4xl lg:text-5xl font-bold bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-4"
          >
            Everything You Need for Perfect Trips
          </motion.h2>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            viewport={{ once: true }}
            className="text-xl text-slate-600 max-w-3xl mx-auto"
          >
            Discover powerful features designed to make travel planning effortless and enjoyable
          </motion.p>
        </div>
      </div>

      {/* Feature Images Stack - Simple version without complex scroll */}
      {features.map((feature, index) => (
        <div
          key={feature.id}
          className="relative w-full overflow-hidden"
          style={{ height: '100vh', minHeight: '100vh' }}
        >
          {/* Media Background */}
          {feature.type === 'image' ? (
            <img
              src={feature.image}
              alt={feature.title}
              className="absolute inset-0 w-full h-full object-cover z-0"
              style={{ display: 'block' }}
              onLoad={() => console.log('[FeatureImageSection] Image loaded:', feature.title)}
              onError={(e) => console.error('[FeatureImageSection] Image failed:', feature.title, e)}
            />
          ) : (
            <video
              autoPlay
              loop
              muted
              playsInline
              className="absolute inset-0 w-full h-full object-cover z-0"
              style={{ display: 'block' }}
              src={feature.video}
              onLoadedData={() => console.log('[FeatureImageSection] Video loaded:', feature.title)}
              onError={(e) => console.error('[FeatureImageSection] Video failed:', feature.title, e)}
            />
          )}

          {/* Dark overlay for text readability */}
          <div className="absolute inset-0 bg-gradient-to-b from-black/30 via-black/20 to-black/40 z-10" />

          {/* Content */}
          <div className="absolute inset-0 flex items-center justify-center px-6 md:px-10 z-20">
            <div className="max-w-4xl w-full text-center">
              <motion.div
                initial={{ opacity: 0, y: 50 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
                viewport={{ once: true }}
                className="bg-black/20 backdrop-blur-lg border border-white/10 rounded-3xl p-8 md:p-12 shadow-2xl"
              >
                {/* Icon */}
                <div className="inline-flex items-center justify-center w-20 h-20 md:w-24 md:h-24 bg-white/20 backdrop-blur-md rounded-3xl mb-6 shadow-2xl">
                  <feature.icon className="w-10 h-10 md:w-12 md:h-12 text-white" />
                </div>

                {/* Title */}
                <h3 className="text-4xl md:text-6xl lg:text-7xl font-bold text-white mb-6 drop-shadow-2xl">
                  {feature.title}
                </h3>

                {/* Description */}
                <p className="text-xl md:text-2xl text-white leading-relaxed drop-shadow-lg max-w-3xl mx-auto">
                  {feature.description}
                </p>

                {/* Decorative line */}
                <div className="mt-8 h-1 w-24 bg-white/80 rounded-full mx-auto" />
              </motion.div>
            </div>
          </div>

          {/* Feature counter */}
          <div className="absolute bottom-10 right-10 text-white/60 text-sm font-semibold z-30">
            {index + 1} / {features.length}
          </div>
        </div>
      ))}

      {/* Contact Section - Separate section after all features */}
      <div className="relative bg-gradient-to-br from-slate-900 via-blue-900 to-purple-900 py-16">
        <div className="max-w-7xl mx-auto px-6 md:px-10">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Start Your Adventure Today
            </h2>
            <p className="text-xl text-white/80 max-w-2xl mx-auto">
              Have questions or need help planning your next trip? Our team is here to assist you 24/7.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            viewport={{ once: true }}
            className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl p-8 md:p-10 shadow-2xl"
          >
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-white mb-8">
              <div>
                <h4 className="text-xl font-semibold mb-3 text-white">Contact</h4>
                <p className="text-white/90 mb-2">hello@warp-travel.app</p>
                <p className="text-white/80">+1 (555) 000-1234</p>
              </div>
              <div>
                <h4 className="text-xl font-semibold mb-3 text-white">Follow Us</h4>
                <p className="text-white/90 mb-2">Instagram · Twitter</p>
                <p className="text-white/80">YouTube · LinkedIn</p>
              </div>
              <div>
                <h4 className="text-xl font-semibold mb-3 text-white">Company</h4>
                <p className="text-white/90 mb-2">Careers · Press</p>
                <p className="text-white/80">Support · About</p>
              </div>
            </div>
            
            <div className="pt-8 border-t border-white/20 flex flex-col md:flex-row items-center justify-between gap-4">
              <p className="text-white/70 text-sm">© 2025 Warp Travel. All rights reserved.</p>
              <div className="flex gap-4">
                <a href="mailto:support@warp-travel.app" className="bg-white/20 hover:bg-white/30 text-white font-semibold py-3 px-8 rounded-lg transition-colors backdrop-blur-sm">
                  Contact Us
                </a>
                <a href="#" className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-lg transition-colors">
                  Get Started
                </a>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
