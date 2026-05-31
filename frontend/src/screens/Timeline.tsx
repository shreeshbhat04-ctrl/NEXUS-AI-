import React from 'react';
import { motion } from 'motion/react';
import { Calendar, ChevronRight, Activity, Droplets, Moon, Sun } from 'lucide-react';

export const Timeline: React.FC = () => {
  const events = [
    { date: 'Today', title: 'Morning Hydration', time: '08:00 AM', icon: Droplets, color: 'bg-blue-100 text-blue-600', desc: 'Drank 500ml of warm lemon water.' },
    { date: 'Today', title: 'Vitamin Intake', time: '09:30 AM', icon: Sun, color: 'bg-yellow-100 text-yellow-600', desc: 'Took daily multivitamin and Vitamin D.' },
    { date: 'Yesterday', title: 'Sleep Quality', time: '11:00 PM', icon: Moon, color: 'bg-indigo-100 text-indigo-600', desc: 'Deep sleep for 3 hours. Total 7.5 hours.' },
    { date: '2 Days Ago', title: 'Cardio Session', time: '05:00 PM', icon: Activity, color: 'bg-red-100 text-red-600', desc: '30-minute brisk walk in the park.' },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="space-y-12"
    >
      <section>
        <h1 className="text-4xl font-serif mb-2 font-medium leading-tight">
          Your <span className="text-tertiary italic">Journey</span>
        </h1>
        <p className="text-on-surface/60 font-sans">The blossoms of your health journey.</p>
      </section>

      {/* Timeline Blossoms */}
      <section className="relative pl-12 space-y-16">
        {/* The "No-Line" Rule: We use tonal shifts and blossoms instead of a clinical line */}
        <div className="absolute left-[22px] top-4 bottom-4 w-1 bg-surface-container-high rounded-full opacity-30" />
        
        {events.map((event, i) => (
          <motion.div
            key={event.title + i}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.15 }}
            className="relative group"
          >
            {/* Blossom */}
            <div className={`absolute -left-12 top-0 w-12 h-12 rounded-full border-4 border-surface shadow-sm flex items-center justify-center transition-all duration-500 group-hover:scale-110 ${event.color}`}>
              <event.icon className="w-5 h-5" />
            </div>
            
            <div className="nurture-card group-hover:shadow-xl transition-all">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h3 className="text-xl font-serif group-hover:text-primary transition-colors">{event.title}</h3>
                  <p className="text-on-surface/40 text-xs font-sans uppercase tracking-widest">{event.date} • {event.time}</p>
                </div>
                <button className="w-8 h-8 rounded-full bg-surface-container-low flex items-center justify-center text-on-surface/40 hover:text-primary transition-colors">
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
              <p className="text-on-surface/60 text-sm leading-relaxed">{event.desc}</p>
            </div>
          </motion.div>
        ))}
      </section>

      <button className="w-full py-6 rounded-[3rem] bg-primary text-surface font-medium flex items-center justify-center gap-2 hover:bg-primary-container transition-all shadow-lg shadow-primary/20">
        <Calendar className="w-5 h-5" />
        <span>Schedule New Check-in</span>
      </button>
    </motion.div>
  );
};
