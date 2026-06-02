export interface Ingredient {
  id: string;
  name: string;
  category: 'Fresh' | 'Pantry' | 'Protein' | 'Dairy';
  price: number;
  status: 'Safe' | 'Watch' | 'Avoid';
  reason: string;
  image: string;
}

export const INGREDIENTS: Ingredient[] = [
  {
    id: '1',
    name: 'Wild Atlantic Salmon',
    category: 'Protein',
    price: 24.50,
    status: 'Safe',
    reason: 'High Omega-3 content supports anti-inflammatory goals.',
    image: 'https://images.unsplash.com/photo-1467003909585-2f8a72700288?auto=format&fit=crop&q=80&w=300'
  },
  {
    id: '2',
    name: 'Organic Avocados',
    category: 'Fresh',
    price: 5.99,
    status: 'Safe',
    reason: 'Healthy monounsaturated fats for cardiovascular health.',
    image: 'https://images.unsplash.com/photo-1523049673857-eb18f1d7b578?auto=format&fit=crop&q=80&w=300'
  },
  {
    id: '3',
    name: 'Whole Grain Sourdough',
    category: 'Pantry',
    price: 7.25,
    status: 'Watch',
    reason: 'Fermentation helps digestion, but monitor total carbohydrate intake.',
    image: 'https://images.unsplash.com/photo-1585478259715-876acc5be8eb?auto=format&fit=crop&q=80&w=300'
  },
  {
    id: '4',
    name: 'Processsed Cheddar',
    category: 'Dairy',
    price: 4.50,
    status: 'Avoid',
    reason: 'High sodium and saturated fats trigger inflammatory response.',
    image: 'https://images.unsplash.com/photo-1618376168193-94c34375497f?auto=format&fit=crop&q=80&w=300'
  },
  {
    id: '5',
    name: 'Baby Spinach',
    category: 'Fresh',
    price: 3.99,
    status: 'Safe',
    reason: 'Nutrient-dense and low-calorie; excellent for protocol compliance.',
    image: 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?auto=format&fit=crop&q=80&w=300'
  },
  {
    id: '6',
    name: 'Greek Yogurt (Plain)',
    category: 'Dairy',
    price: 6.50,
    status: 'Safe',
    reason: 'Probiotics support gut health for autoimmune recovery.',
    image: 'https://images.unsplash.com/photo-1488477181946-6428a0291777?auto=format&fit=crop&q=80&w=300'
  }
];
