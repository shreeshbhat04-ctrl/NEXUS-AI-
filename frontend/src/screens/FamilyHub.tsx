import React from 'react';
import { motion } from 'motion/react';
import { Plus, ChevronRight, Heart, Shield, Star } from 'lucide-react';

export const FamilyHub: React.FC = () => {
  const family = [
    { name: 'Me', role: 'Primary Caregiver', image: 'https://picsum.photos/seed/me/200/200', status: 'Healthy', color: 'bg-primary-container' },
    { name: 'Sarah', role: 'Partner', image: 'https://picsum.photos/seed/sarah/200/200', status: 'Flu Recovery', color: 'bg-secondary-container' },
    { name: 'Leo', role: 'Child', image: 'https://picsum.photos/seed/leo/200/200', status: 'Healthy', color: 'bg-tertiary-container' },
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
          Your <span className="text-secondary italic">Hearth</span> Circle
        </h1>
        <p className="text-on-surface/60 font-sans">Nurturing those who matter most.</p>
      </section>

      <section className="grid gap-8">
        {family.map((member, i) => (
          <motion.div
            key={member.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="nurture-card group cursor-pointer hover:shadow-xl transition-all overflow-hidden relative"
          >
            {/* Background design element */}
            <div className={`absolute top-0 right-0 w-32 h-32 rounded-full -mr-16 -mt-16 opacity-10 ${member.color}`} />
            
            <div className="flex gap-8 items-center relative z-10">
              <div className={`w-24 h-24 rounded-[2rem] overflow-hidden ${member.color}`}>
                <img src={member.image} alt={member.name} className="w-full h-full object-cover" referrerPolicy="no-referrer" />
              </div>
              <div className="flex-1">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-2xl font-serif group-hover:text-primary transition-colors">{member.name}</h3>
                    <p className="text-on-surface/40 text-sm font-sans">{member.role}</p>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                    member.status === 'Healthy' ? 'bg-primary-fixed/30 text-primary' : 'bg-secondary-container/30 text-secondary'
                  }`}>
                    {member.status}
                  </div>
                </div>
                <div className="mt-4 flex gap-4">
                  <button className="text-primary text-sm font-medium flex items-center gap-1 hover:underline">
                    Health Records <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
        
        <button className="w-full py-8 rounded-[2rem] border-2 border-dashed border-outline-variant flex flex-col items-center justify-center text-on-surface/40 hover:text-primary hover:border-primary transition-all gap-2">
          <Plus className="w-8 h-8" />
          <span className="font-medium">Add Family Member</span>
        </button>
      </section>

      {/* Trust Badges */}
      <section className="flex justify-around items-center py-8 border-t border-outline-variant/20">
        <div className="flex flex-col items-center gap-2 opacity-40">
          <Shield className="w-6 h-6" />
          <span className="text-[10px] uppercase tracking-widest font-bold">Secure</span>
        </div>
        <div className="flex flex-col items-center gap-2 opacity-40">
          <Heart className="w-6 h-6" />
          <span className="text-[10px] uppercase tracking-widest font-bold">Nurturing</span>
        </div>
        <div className="flex flex-col items-center gap-2 opacity-40">
          <Star className="w-6 h-6" />
          <span className="text-[10px] uppercase tracking-widest font-bold">Premium</span>
        </div>
      </section>
    </motion.div>
  );
};
