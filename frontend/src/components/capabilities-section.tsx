import { motion } from 'motion/react';
import { Brain, Clock, MapPin, Users, Smartphone, Shield, Zap, Globe } from 'lucide-react';

const capabilities = [
  {
    icon: Brain,
    title: "AI-Powered Planning",
    description: "Our advanced AI analyzes millions of travel data points to create personalized itineraries that match your interests and budget.",
    color: "from-blue-500 to-cyan-500"
  },
  {
    icon: Clock,
    title: "Real-Time Updates",
    description: "Get instant notifications about flight changes, weather updates, and local events that might affect your travel plans.",
    color: "from-purple-500 to-pink-500"
  },
  {
    icon: MapPin,
    title: "Smart Recommendations",
    description: "Discover hidden gems and local favorites based on your preferences, with detailed insights from fellow travelers.",
    color: "from-green-500 to-emerald-500"
  },
  {
    icon: Users,
    title: "Group Coordination",
    description: "Plan trips with friends and family effortlessly. Share itineraries, vote on activities, and keep everyone in sync.",
    color: "from-orange-500 to-red-500"
  },
  {
    icon: Smartphone,
    title: "Mobile Companion",
    description: "Access your complete travel plan offline, with maps, bookings, and emergency contacts always at your fingertips.",
    color: "from-indigo-500 to-purple-500"
  },
  {
    icon: Shield,
    title: "Travel Protection",
    description: "Built-in safety features including emergency contacts, travel insurance options, and 24/7 support assistance.",
    color: "from-teal-500 to-blue-500"
  },
  {
    icon: Zap,
    title: "Instant Booking",
    description: "Book flights, hotels, and activities directly through the platform with our exclusive deals and partnerships.",
    color: "from-yellow-500 to-orange-500"
  },
  {
    icon: Globe,
    title: "Global Coverage",
    description: "Plan trips to over 10,000 destinations worldwide with local insights and culturally-aware recommendations.",
    color: "from-pink-500 to-rose-500"
  }
];

export function CapabilitiesSection() {
  return (
    <section className="py-20 bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0">
        <div className="absolute top-1/3 left-1/6 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/3 right-1/6 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-pink-500/5 rounded-full blur-3xl" />
      </div>
      
      {/* Animated grid background */}
      <div 
        className="absolute inset-0 opacity-5"
        style={{
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
        }}
      />
      
      <div className="max-w-7xl mx-auto px-6 relative">
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <motion.h2 
            initial={{ scale: 0.9 }}
            whileInView={{ scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-4xl lg:text-5xl bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent mb-4"
          >
            Powered by Intelligence
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="text-xl text-gray-300 max-w-3xl mx-auto"
          >
            Experience the future of travel planning with our comprehensive suite of AI-driven features
          </motion.p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {capabilities.map((capability, index) => {
            const Icon = capability.icon;
            return (
              <motion.div
                key={capability.title}
                initial={{ opacity: 0, y: 50 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.05 }}
                viewport={{ once: true }}
                whileHover={{ 
                  y: -12, 
                  scale: 1.02,
                  transition: { duration: 0.3 } 
                }}
                className="group bg-white/10 backdrop-blur-xl rounded-2xl p-8 shadow-2xl hover:shadow-blue-500/20 transition-all duration-300 border border-white/20 hover:border-blue-400/50"
              >
                <div className="mb-6">
                  <motion.div 
                    whileHover={{ 
                      scale: 1.15,
                      rotate: 5
                    }}
                    className={`w-16 h-16 rounded-2xl bg-gradient-to-r ${capability.color} p-4 mb-4 shadow-lg group-hover:shadow-xl transition-all duration-300`}
                  >
                    <Icon className="w-full h-full text-white" />
                  </motion.div>
                  <h3 className="text-xl text-white mb-3 group-hover:bg-gradient-to-r group-hover:from-blue-400 group-hover:to-purple-400 group-hover:bg-clip-text group-hover:text-transparent transition-all duration-300">
                    {capability.title}
                  </h3>
                  <p className="text-gray-300 leading-relaxed group-hover:text-gray-200 transition-colors">
                    {capability.description}
                  </p>
                </div>
              </motion.div>
            );
          })}
        </div>

        <motion.div
          initial={{ opacity: 0, y: 50 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          viewport={{ once: true }}
          className="text-center mt-16"
        >
          <div className="bg-gradient-to-r from-white/10 to-white/5 backdrop-blur-xl rounded-2xl p-8 shadow-2xl border border-white/20 max-w-4xl mx-auto">
            <div className="flex items-center justify-center mb-6">
              <motion.div 
                whileHover={{ scale: 1.1, rotate: 10 }}
                className="w-12 h-12 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-xl flex items-center justify-center mr-4 shadow-lg"
              >
                <Zap className="w-6 h-6 text-white" />
              </motion.div>
              <h3 className="text-2xl text-white">
                Ready to Experience the Future?
              </h3>
            </div>
            <p className="text-gray-300 mb-8 text-lg">
              Join thousands of travelers who have already discovered the magic of AI-powered trip planning.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <motion.button
                whileHover={{ 
                  scale: 1.05,
                  boxShadow: "0 25px 50px -12px rgba(59, 130, 246, 0.5)"
                }}
                whileTap={{ scale: 0.95 }}
                className="px-8 py-4 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 text-white rounded-xl shadow-xl hover:shadow-2xl transition-all duration-300"
              >
                Start Planning Now
              </motion.button>
              <motion.button
                whileHover={{ 
                  scale: 1.05,
                  backgroundColor: "rgba(255, 255, 255, 0.1)"
                }}
                whileTap={{ scale: 0.95 }}
                className="px-8 py-4 bg-transparent border-2 border-white/30 text-white rounded-xl hover:border-blue-400/70 transition-all duration-300 backdrop-blur-sm"
              >
                Watch Demo
              </motion.button>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}