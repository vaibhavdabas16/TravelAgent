import { motion } from 'motion/react';
import { ImageWithFallback } from './figma/ImageWithFallback';
import { Calendar, MapPin, Users, Star } from 'lucide-react';

const recentTrips = [
  {
    id: 1,
    title: "Tokyo Nights",
    location: "Tokyo, Japan",
    image: "https://images.unsplash.com/photo-1668563966338-38394330adf0?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx0b2t5byUyMHNreWxpbmUlMjBuaWdodHxlbnwxfHx8fDE3NTc0MTg2ODB8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
    duration: "7 days",
    travelers: 2,
    rating: 4.9,
    price: "$2,850"
  },
  {
    id: 2,
    title: "Taj Mahal Sunrise",
    location: "Agra, India",
    image: "https://images.unsplash.com/photo-1512453979798-5ea266f8880c?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&q=80&w=1080",
    duration: "5 days",
    travelers: 2,
    rating: 4.8,
    price: "$2,200"
  },
  {
    id: 3,
    title: "Bali Temples",
    location: "Bali, Indonesia",
    image: "https://images.unsplash.com/photo-1613278435217-de4e5a91a4ee?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxiYWxpJTIwdGVtcGxlJTIwc3Vuc2V0fGVufDF8fHx8MTc1NzM4MTc4MXww&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
    duration: "10 days",
    travelers: 4,
    rating: 4.7,
    price: "$1,950"
  },
  {
    id: 4,
    title: "NYC Adventures",
    location: "New York, USA",
    image: "https://images.unsplash.com/photo-1698066574628-3d1a68c2f204?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxuZXclMjB5b3JrJTIwY2l0eSUyMG1hbmhhdHRhbnxlbnwxfHx8fDE3NTc0MTU0ODZ8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
    duration: "4 days",
    travelers: 1,
    rating: 4.6,
    price: "$1,650"
  },
  {
    id: 5,
    title: "Santorini Dreams",
    location: "Santorini, Greece",
    image: "https://images.unsplash.com/photo-1743427495409-bf19fdaa4c16?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxzYW50b3JpbmklMjBncmVlY2UlMjBibHVlJTIwZG9tZXxlbnwxfHx8fDE3NTc0MTg2ODl8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
    duration: "6 days",
    travelers: 2,
    rating: 4.9,
    price: "$2,400"
  },
  {
    id: 6,
    title: "Iceland Aurora",
    location: "Reykjavik, Iceland",
    image: "https://images.unsplash.com/photo-1488415032361-b7e238421f1b?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxpY2VsYW5kJTIwbm9ydGhlcm4lMjBsaWdodHN8ZW58MXx8fHwxNzU3Mzg2MjY3fDA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral",
    duration: "8 days",
    travelers: 3,
    rating: 4.8,
    price: "$3,200"
  }
];

export function TripsCarousel() {
  return (
    <section className="py-20 bg-gradient-to-br from-slate-50 via-blue-50 to-purple-50 relative overflow-hidden">
      {/* Background decorative elements */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-blue-200/20 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-200/20 rounded-full blur-3xl" />
      </div>
      
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
            className="text-4xl lg:text-5xl bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 bg-clip-text text-transparent mb-4"
          >
            Recent Adventures
          </motion.h2>
          <motion.p 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="text-xl text-slate-600 max-w-2xl mx-auto"
          >
            Discover amazing journeys planned by our AI for travelers just like you
          </motion.p>
        </motion.div>

        <div className="relative">
          <div className="flex gap-6 overflow-x-auto pb-6 scrollbar-hide">
            {recentTrips.map((trip, index) => (
              <motion.div
                key={trip.id}
                initial={{ opacity: 0, y: 50 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                viewport={{ once: true }}
                whileHover={{ 
                  y: -12, 
                  scale: 1.02,
                  transition: { duration: 0.3 } 
                }}
                className="group min-w-[320px] bg-white/70 backdrop-blur-sm rounded-2xl shadow-xl overflow-hidden cursor-pointer border border-white/40 hover:shadow-2xl hover:border-blue-200/50"
              >
                <div className="relative h-48 overflow-hidden">
                  <ImageWithFallback
                    src={trip.image}
                    alt={trip.title}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                  />
                  <motion.div 
                    whileHover={{ scale: 1.05 }}
                    className="absolute top-4 right-4 bg-gradient-to-r from-yellow-400 to-orange-400 px-3 py-1 rounded-full shadow-lg"
                  >
                    <div className="flex items-center gap-1">
                      <Star className="w-4 h-4 text-white fill-current" />
                      <span className="text-sm text-white">{trip.rating}</span>
                    </div>
                  </motion.div>
                  <motion.div 
                    whileHover={{ scale: 1.05 }}
                    className="absolute bottom-4 left-4 bg-gradient-to-r from-green-400 to-emerald-400 px-3 py-1 rounded-full shadow-lg"
                  >
                    <span className="text-sm text-white">{trip.price}</span>
                  </motion.div>
                </div>

                <div className="p-6">
                  <h3 className="text-xl mb-2 bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent group-hover:from-blue-600 group-hover:to-purple-600 transition-all duration-300">
                    {trip.title}
                  </h3>
                  
                  <div className="flex items-center gap-2 mb-4 text-slate-600">
                    <MapPin className="w-4 h-4 text-blue-500" />
                    <span className="text-sm">{trip.location}</span>
                  </div>

                  <div className="flex items-center justify-between text-sm text-slate-500">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-4 h-4 text-purple-500" />
                      <span>{trip.duration}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Users className="w-4 h-4 text-pink-500" />
                      <span>{trip.travelers} travelers</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
          
          {/* Enhanced gradient fade edges */}
          <div className="absolute top-0 left-0 bottom-6 w-12 bg-gradient-to-r from-slate-50 via-blue-50/50 to-transparent pointer-events-none" />
          <div className="absolute top-0 right-0 bottom-6 w-12 bg-gradient-to-l from-purple-50 via-blue-50/50 to-transparent pointer-events-none" />
        </div>
      </div>
    </section>
  );
}