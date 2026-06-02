import { useState, useMemo, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Search, 
  ShieldAlert, 
  ShieldCheck, 
  ShieldQuestion, 
  Filter,
  TrendingUp,
  ShoppingCart,
  Check,
  X,
  Upload,
  Link,
  Loader2
} from 'lucide-react';
import { Pill, SectionShell } from '../../shared/components/ui';
import { extractSafeIngredients, ExtractSafeIngredientsResponse, addToCart } from '../../shared/lib/api';

const STAGGER = {
  hidden: { opacity: 0, y: 20 },
  show: {
    opacity: 1,
    y: 0,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const ITEM = {
  hidden: { opacity: 0, y: 10 },
  show: { opacity: 1, y: 0 }
};

interface MarketplaceScreenProps {
  patientId: number;
  onAddIngredient?: (name: string) => void;
  onClose?: () => void;
}

export function MarketplaceScreen({ patientId, onAddIngredient, onClose }: MarketplaceScreenProps) {
  const [filter, setFilter] = useState<'All' | 'Fresh' | 'Pantry' | 'Protein' | 'Dairy'>('All');
  const [search, setSearch] = useState('');
  const [cartCount, setCartCount] = useState(0);
  
  const [inspirationUrl, setInspirationUrl] = useState('');
  const [inspirationFile, setInspirationFile] = useState<File | null>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [dynamicIngredients, setDynamicIngredients] = useState<ExtractSafeIngredientsResponse['safe_ingredients']>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const filteredIngredients = useMemo(() => {
    return dynamicIngredients.filter(item => {
      const matchesFilter = filter === 'All' || item.category === filter;
      const matchesSearch = item.name.toLowerCase().includes(search.toLowerCase());
      return matchesFilter && matchesSearch;
    });
  }, [filter, search, dynamicIngredients]);

  const handleAddToCart = async (item: any) => {
    if (item.status === 'Avoid') return;
    try {
      await addToCart(patientId, item.name, 'ingredient', item.price, item.search_url || '');
      setCartCount(prev => prev + 1);
      // Notify layout that cart changed
      window.dispatchEvent(new CustomEvent('cart-updated'));
    } catch (err) {
      console.error('Failed to add to cart:', err);
    }
    if (onAddIngredient) {
      onAddIngredient(item.name.toLowerCase());
    }
  };

  const handleExtract = async () => {
    if (!inspirationUrl && !inspirationFile) return;
    setIsExtracting(true);
    try {
      const result = await extractSafeIngredients(patientId, inspirationUrl || undefined, inspirationFile || undefined);
      setDynamicIngredients(result.safe_ingredients);
    } catch (error) {
      console.error(error);
    } finally {
      setIsExtracting(false);
    }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -18 }} className="space-y-8 pb-12">
      <div className="flex items-start justify-between">
        <SectionShell
          eyebrow="Marketplace Studio"
          title={
            <>
              Dynamic Ingredient <span className="text-primary italic font-serif">Extraction</span>
            </>
          }
          description="Paste a recipe URL or upload an image to extract ingredients, filtered safely against your medical profile."
        />
        {onClose && (
          <button 
            onClick={onClose}
            className="rounded-full bg-surface-container-high p-2 text-on-surface hover:bg-surface-container-highest transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        
        {/* Extraction Input Studio */}
        <div className="md:col-span-12 glass-panel p-6 flex flex-col lg:flex-row gap-6 items-center">
          <div className="flex-1 w-full space-y-4">
            <label className="space-y-2 block">
              <span className="text-sm font-medium text-on-surface/60 flex items-center gap-2">
                <Link className="h-4 w-4" /> Inspiration URL
              </span>
              <input 
                type="text"
                placeholder="https://instacart.com/... or recipe blog URL"
                className="input-shell w-full"
                value={inspirationUrl}
                onChange={(e) => setInspirationUrl(e.target.value)}
              />
            </label>
          </div>
          <div className="text-on-surface/40 font-serif italic text-xl">OR</div>
          <div className="flex-1 w-full space-y-4">
            <label className="space-y-2 block">
              <span className="text-sm font-medium text-on-surface/60 flex items-center gap-2">
                <Upload className="h-4 w-4" /> Inspiration Image
              </span>
              <div className="flex items-center gap-3">
                <button 
                  onClick={() => fileInputRef.current?.click()}
                  className="river-stone-btn bg-surface-container-high text-on-surface/80 px-4 py-3 text-sm"
                >
                  {inspirationFile ? inspirationFile.name : 'Select Image...'}
                </button>
                <input 
                  type="file" 
                  ref={fileInputRef} 
                  className="hidden" 
                  accept="image/*"
                  onChange={(e) => setInspirationFile(e.target.files?.[0] || null)}
                />
              </div>
            </label>
          </div>
          <div className="shrink-0 w-full lg:w-auto">
             <button
                onClick={handleExtract}
                disabled={isExtracting || (!inspirationUrl && !inspirationFile)}
                className="river-stone-btn w-full lg:w-auto bg-gradient-to-br from-primary to-primary-container px-6 py-4 text-surface disabled:opacity-50"
             >
                {isExtracting ? <><Loader2 className="w-5 h-5 animate-spin inline mr-2"/> Extracting...</> : 'Extract & Filter'}
             </button>
          </div>
        </div>

        {/* Categories Sidebar */}
        <div className="md:col-span-3 lg:col-span-2 space-y-4">
          <div className="glass-panel p-3">
             <p className="eyebrow text-on-surface/40 px-3 py-2">Categories</p>
             <nav className="space-y-1">
              {(['All', 'Fresh', 'Protein', 'Pantry', 'Dairy'] as const).map((cat) => (
                <button
                  key={cat}
                  onClick={() => setFilter(cat)}
                  className={`w-full text-left px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                    filter === cat 
                      ? 'bg-primary-fixed/30 text-primary' 
                      : 'text-on-surface/60 hover:bg-surface-container-lowest hover:text-primary'
                  }`}
                >
                  {cat === 'All' ? 'All Safe' : cat}
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Main Grid */}
        <div className="md:col-span-9 lg:col-span-10 space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 px-2">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-on-surface/30" />
              <input 
                type="text"
                placeholder="Search extracted ingredients..."
                className="w-full bg-surface-container-lowest/50 border border-outline-variant/30 rounded-2xl pl-11 pr-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
          </div>

          {dynamicIngredients.length === 0 && !isExtracting ? (
             <div className="p-12 text-center text-on-surface/50 border border-dashed border-outline-variant/40 rounded-3xl">
                Upload an image or paste a URL above to extract ingredients.
             </div>
          ) : (
            <motion.div 
              variants={STAGGER}
              initial="hidden"
              animate="show"
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
            >
              <AnimatePresence mode="popLayout">
                {filteredIngredients.map((item) => (
                  <motion.div 
                    layout
                    key={item.id}
                    variants={ITEM}
                    initial="hidden"
                    animate="show"
                    exit={{ opacity: 0, scale: 0.9 }}
                    className="glass-panel group flex flex-col h-full relative"
                  >
                    {/* Safety Watermark */}
                    <div className="absolute top-4 right-4 z-10">
                      {item.status === 'Safe' && (
                        <div className="p-1.5 bg-primary-fixed/40 rounded-lg text-primary glass-edge">
                          <ShieldCheck className="w-4 h-4" />
                        </div>
                      )}
                      {item.status === 'Watch' && (
                        <div className="p-1.5 bg-tertiary-container/30 rounded-lg text-tertiary glass-edge">
                          <ShieldQuestion className="w-4 h-4" />
                        </div>
                      )}
                      {item.status === 'Avoid' && (
                        <div className="p-1.5 bg-terracotta/10 rounded-lg text-terracotta glass-edge">
                          <ShieldAlert className="w-4 h-4" />
                        </div>
                      )}
                    </div>

                    <div className="aspect-[4/3] rounded-xl mb-5 overflow-hidden bg-surface-container-low/50">
                      <img 
                        src={item.image} 
                        alt={item.name}
                        className={`w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ${item.status === 'Avoid' ? 'grayscale opacity-60' : ''}`}
                      />
                    </div>
                    
                    <div className="flex flex-col flex-1">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-serif font-bold text-[1.1rem] text-on-surface leading-tight">{item.name}</h4>
                        <span className="font-serif text-[0.95rem] font-bold text-primary">${item.price.toFixed(2)}</span>
                      </div>
                      <p className="eyebrow text-on-surface/30 mb-4">{item.category}</p>
                      
                      <div className={`mt-auto p-4 rounded-xl text-[0.85rem] leading-6 glass-edge ${
                        item.status === 'Safe' ? 'bg-primary-fixed/10 text-primary/80' :
                        item.status === 'Watch' ? 'bg-tertiary-container/10 text-tertiary/80' :
                        'bg-terracotta/5 text-terracotta/80'
                      }`}>
                        <p className="font-bold flex items-center gap-2 mb-1">
                           {item.status === 'Safe' ? 'Recommended' : item.status === 'Watch' ? 'Monitor Intake' : 'Non-Compliant'}
                        </p>
                        <p className="opacity-80 font-sans">{item.reason}</p>
                      </div>

                      <button 
                        onClick={() => handleAddToCart(item)}
                        className={`w-full mt-5 py-3 rounded-xl text-[0.85rem] font-bold tracking-widest uppercase transition-all ${
                          item.status === 'Avoid' 
                          ? 'bg-surface-container-high/40 text-on-surface/20 cursor-not-allowed glass-edge' 
                          : 'bg-on-surface text-surface hover:bg-primary hover:text-white shadow-sm'
                        }`}
                      >
                        {item.status === 'Avoid' ? 'Restricted' : 'Add to Pantry'}
                      </button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </motion.div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
