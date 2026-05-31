import React from 'react';
import { motion } from 'motion/react';
import { Plus, ChevronRight, Activity, Moon, Droplets } from 'lucide-react';

export const HomeScreen: React.FC = () => {
  const familyMembers = [
    { name: 'Me', color: 'bg-primary-container', image: 'https://picsum.photos/seed/me/100/100' },
    { name: 'Sarah', color: 'bg-secondary-container', image: 'https://picsum.photos/seed/sarah/100/100' },
    { name: 'Leo', color: 'bg-tertiary-container', image: 'https://picsum.photos/seed/leo/100/100' },
  ];

  const healthTips = [
    { title: 'Morning Hydration', desc: 'Start your day with warm lemon water to boost digestion.', icon: Droplets, color: 'text-blue-500' },
    { title: 'Mindful Rest', desc: 'A 10-minute meditation can lower cortisol levels significantly.', icon: Moon, color: 'text-indigo-500' },
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
          Good morning, <br />
          <span className="text-primary italic">nexus_ai is ready.</span>
        </h1>
        <p className="text-on-surface/60 font-sans">Your family's wellness journey today.</p>
      </section>

      {/* Family Hub Chip */}
      <section className="flex items-center gap-4 overflow-x-auto pb-4 no-scrollbar">
        <div className="flex -space-x-4">
          {familyMembers.map((member, i) => (
            <motion.div
              key={member.name}
              initial={{ x: -20, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              transition={{ delay: i * 0.1 }}
              className={`w-14 h-14 rounded-full border-4 border-surface overflow-hidden ${member.color}`}
            >
              <img src={member.image} alt={member.name} className="w-full h-full object-cover" referrerPolicy="no-referrer" />
            </motion.div>
          ))}
        </div>
        <button className="w-14 h-14 rounded-full border-2 border-dashed border-outline-variant flex items-center justify-center text-on-surface/40 hover:text-primary hover:border-primary transition-all">
          <Plus className="w-6 h-6" />
        </button>
      </section>

      {/* Nurture Cards */}
      <section className="space-y-6">
        <div className="flex justify-between items-end">
          <h2 className="text-2xl font-serif">Daily Nurture</h2>
          <button className="text-primary font-medium flex items-center gap-1 hover:gap-2 transition-all">
            View all <ChevronRight className="w-4 h-4" />
          </button>
        </div>
        
        <div className="grid gap-6">
          {healthTips.map((tip, i) => (
            <motion.div
              key={tip.title}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 + i * 0.1 }}
              className="nurture-card group cursor-pointer hover:shadow-xl transition-all"
            >
              <div className="flex gap-6 items-start">
                <div className={`w-12 h-12 rounded-2xl bg-surface-container-low flex items-center justify-center ${tip.color}`}>
                  <tip.icon className="w-6 h-6" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-serif mb-1 group-hover:text-primary transition-colors">{tip.title}</h3>
                  <p className="text-on-surface/60 text-sm leading-relaxed">{tip.desc}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Activity Summary */}
      <section className="bg-primary-fixed/20 rounded-[2.5rem] p-8 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-serif mb-1">Weekly Progress</h3>
          <p className="text-on-surface/60 text-sm">You've reached 85% of your goals.</p>
        </div>
        <div className="w-16 h-16 rounded-full border-4 border-primary/20 border-t-primary flex items-center justify-center">
          <Activity className="text-primary w-6 h-6" />
        </div>
      </section>
    </motion.div>
  );
};
