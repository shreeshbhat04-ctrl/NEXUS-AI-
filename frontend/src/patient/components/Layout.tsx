import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Grid2X2, 
  Map, 
  Landmark,
  Pill, 
  History, 
  Stethoscope, 
  Info, 
  User, 
  ShoppingCart, 
  LogOut, 
  ArrowLeftRight,
  CheckCircle2, 
  Trash2, 
  Loader2, 
  ChevronRight, 
  Plus, 
  AlertCircle, 
  Sparkles, 
  ExternalLink, 
  X,
  CreditCard,
  Check
} from 'lucide-react';
import logo from '../../assets/logo.png';
import { 
  fetchCartItems, 
  deleteFromCart, 
  checkCartAvailability, 
  checkoutCartItem, 
  addToCart, 
  type CartItem 
} from '../../shared/lib/api';

type TabId = 'dashboard' | 'care-maze' | 'medications' | 'financial-advocate' | 'hitl' | 'history' | 'profile' | 'about';

interface LayoutProps {
  patientId: number;
  children: React.ReactNode;
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  patientName: string;
  onRefresh: () => void;
  loading: boolean;
  onRoleChange?: () => void;
  onLogout?: () => void;
}

export const Layout: React.FC<LayoutProps> = ({
  patientId,
  children,
  activeTab,
  onTabChange,
  patientName,
  onRefresh,
  loading,
  onRoleChange,
  onLogout,
}) => {
  const [profileOpen, setProfileOpen] = useState(false);
  
  // Cart-related states
  const [cartOpen, setCartOpen] = useState(false);
  const [cartItems, setCartItems] = useState<CartItem[]>([]);
  const [isCheckingAvailability, setIsCheckingAvailability] = useState(false);
  const [checkoutItem, setCheckoutItem] = useState<CartItem | null>(null);
  
  // GPay payment state
  const [isPaying, setIsPaying] = useState(false);
  const [paySuccess, setPaySuccess] = useState(false);
  const [gpayOrderId, setGpayOrderId] = useState<string | null>(null);
  
  // Custom manual item form state
  const [customItemName, setCustomItemName] = useState('');
  const [customItemType, setCustomItemType] = useState<'medicine' | 'ingredient'>('ingredient');
  const [isAddingCustom, setIsAddingCustom] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const tabs: Array<{ id: TabId; icon: React.ComponentType<{ className?: string }>; label: string }> = [
    { id: 'dashboard', icon: Grid2X2, label: 'Dashboard' },
    { id: 'care-maze', icon: Map, label: 'Care Maze' },
    { id: 'medications', icon: Pill, label: 'Meds' },
    { id: 'financial-advocate', icon: Landmark, label: 'Finance' },
    { id: 'hitl', icon: Stethoscope, label: 'Doctors' },
    { id: 'history', icon: History, label: 'History' },
    { id: 'profile', icon: User, label: 'Profile' },
    { id: 'about', icon: Info, label: 'About' },
  ];

  // Refresh cart function
  const refreshCart = async () => {
    try {
      const items = await fetchCartItems(patientId);
      setCartItems(items);
    } catch (err) {
      console.error('Failed to load cart:', err);
    }
  };

  // Sync with custom event
  useEffect(() => {
    refreshCart();
    
    const handleCartUpdated = () => {
      refreshCart();
    };
    
    window.addEventListener('cart-updated', handleCartUpdated);
    return () => {
      window.removeEventListener('cart-updated', handleCartUpdated);
    };
  }, [patientId]);

  // Actions
  const handleDeleteItem = async (itemId: number) => {
    try {
      await deleteFromCart(patientId, itemId);
      await refreshCart();
      window.dispatchEvent(new CustomEvent('cart-updated'));
    } catch (err) {
      console.error('Failed to delete item:', err);
    }
  };

  const handleCheckAvailability = async () => {
    try {
      setIsCheckingAvailability(true);
      setErrorMsg(null);
      await checkCartAvailability(patientId);
      await refreshCart();
      window.dispatchEvent(new CustomEvent('cart-updated'));
    } catch (err) {
      console.error('Failed to check availability:', err);
      setErrorMsg('Failed to check availability.');
    } finally {
      setIsCheckingAvailability(false);
    }
  };

  const handleAddCustomItem = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customItemName.trim()) return;
    try {
      setIsAddingCustom(true);
      setErrorMsg(null);
      const price = customItemType === 'ingredient' ? 8.50 : 15.00;
      await addToCart(patientId, customItemName.trim(), customItemType, price, undefined);
      setCustomItemName('');
      await refreshCart();
      window.dispatchEvent(new CustomEvent('cart-updated'));
    } catch (err) {
      console.error('Failed to add custom item:', err);
      setErrorMsg('Failed to save item to cart.');
    } finally {
      setIsAddingCustom(false);
    }
  };

  const handleStartCheckout = (item: CartItem) => {
    setCheckoutItem(item);
    setIsPaying(false);
    setPaySuccess(false);
    setGpayOrderId(null);
  };

  const handleExecuteGPay = async () => {
    if (!checkoutItem) return;
    try {
      setIsPaying(true);
      // Premium experience delay
      await new Promise((resolve) => setTimeout(resolve, 1800));
      
      const response = await checkoutCartItem(patientId, checkoutItem.id);
      if (response.success) {
        setPaySuccess(true);
        setGpayOrderId(response.order_id);
        await refreshCart();
        window.dispatchEvent(new CustomEvent('cart-updated'));
      } else {
        setErrorMsg(response.message || 'Checkout failed.');
        setCheckoutItem(null);
      }
    } catch (err) {
      console.error('Checkout error:', err);
      setErrorMsg('Checkout failed.');
      setCheckoutItem(null);
    } finally {
      setIsPaying(false);
    }
  };

  const activeCartCount = cartItems.filter(item => item.status !== 'purchased').length;

  return (
    <div className="flex min-h-screen w-full bg-surface">
      {/* ─── Desktop Sidebar ─── */}
      <aside className="hidden lg:flex fixed left-0 top-0 z-50 h-screen w-20 flex-col items-center border-r border-outline-variant/30 bg-white py-6">
        {/* Logo */}
        <button
          onClick={() => onTabChange('dashboard')}
          className="mb-8 flex h-12 w-12 items-center justify-center rounded-2xl overflow-hidden transition-transform hover:scale-105"
        >
          <img src={logo} alt="nexus_ai" className="h-10 w-10 object-contain" />
        </button>

        {/* Nav Items */}
        <nav className="flex flex-1 flex-col items-center gap-1">
          {tabs.map((tab) => {
            const isActive = tab.id === activeTab;
            return (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                title={tab.label}
                className={`group relative flex flex-col items-center justify-center w-14 rounded-2xl px-2 py-3 transition-all duration-200 ${
                  isActive
                    ? 'bg-primary-fixed text-primary'
                    : 'text-on-surface/50 hover:bg-surface-container-low hover:text-primary'
                }`}
              >
                <tab.icon className="h-5 w-5 shrink-0" />
                <span className={`mt-1 text-[0.6rem] font-medium leading-tight ${
                  isActive ? 'text-primary' : 'text-on-surface/45'
                }`}>
                  {tab.label}
                </span>

                {/* Tooltip */}
                <span className="pointer-events-none absolute left-[calc(100%+8px)] top-1/2 -translate-y-1/2 whitespace-nowrap rounded-lg bg-on-surface px-3 py-1.5 text-xs font-medium text-white opacity-0 shadow-lg transition-opacity group-hover:opacity-100 z-50">
                  {tab.label}
                </span>
              </button>
            );
          })}
        </nav>

        {/* Bottom Actions */}
        <div className="mt-auto flex flex-col items-center gap-2 pt-4">
          <button
            onClick={() => setCartOpen(true)}
            className={`relative flex h-10 w-10 items-center justify-center rounded-full transition-colors ${
              cartOpen 
                ? 'bg-primary text-white' 
                : 'bg-surface-container-low text-on-surface/50 hover:bg-surface-container-high hover:text-primary'
            }`}
            title="Gemini Universal Cart"
          >
            <ShoppingCart className="h-4 w-4" />
            {activeCartCount > 0 && (
              <span className="absolute -top-0.5 -right-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-secondary text-[9px] font-bold text-white animate-pulse">
                {activeCartCount}
              </span>
            )}
          </button>

          <div className="relative">
            <button
              onClick={() => setProfileOpen(!profileOpen)}
              className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-container text-primary text-sm font-semibold transition-colors hover:bg-primary-fixed"
              title={patientName}
            >
              {patientName.charAt(0)}
            </button>

            {/* Profile Dropdown */}
            {profileOpen && (
              <div className="absolute left-[calc(100%+8px)] bottom-0 w-56 rounded-2xl bg-white p-4 shadow-[0_4px_12px_rgba(60,64,67,0.15),0_1px_3px_rgba(60,64,67,0.1)] border border-outline-variant/30 z-50">
                <div className="flex items-center gap-3 mb-3">
                  <div className="h-10 w-10 rounded-full bg-primary-container text-primary flex items-center justify-center text-sm font-semibold">
                    {patientName.charAt(0)}
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium text-sm text-on-surface truncate">{patientName}</p>
                    <p className="text-xs text-on-surface/50">Patient</p>
                  </div>
                </div>

                <div className="w-full h-px bg-outline-variant/40 mb-2" />

                <button
                  onClick={() => {
                    onTabChange('profile');
                    setProfileOpen(false);
                  }}
                  className="w-full flex items-center gap-2 py-2 text-sm text-on-surface/70 hover:text-primary transition-colors rounded-lg hover:bg-surface-container-low px-2"
                >
                  <User className="h-4 w-4" />
                  Account Settings
                </button>
                {onRoleChange && (
                  <button
                    onClick={onRoleChange}
                    className="w-full flex items-center gap-2 py-2 text-sm text-primary hover:text-primary/80 transition-colors font-medium rounded-lg hover:bg-primary-fixed/50 px-2"
                  >
                    <ArrowLeftRight className="h-4 w-4" />
                    Provider Portal
                  </button>
                )}
                <button
                  onClick={onLogout}
                  className="w-full flex items-center gap-2 py-2 text-sm text-secondary hover:text-secondary/80 transition-colors rounded-lg hover:bg-secondary-container/50 px-2"
                >
                  <LogOut className="h-4 w-4" />
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* ─── Main Content ─── */}
      <main className="flex-1 min-h-screen min-w-0 w-full lg:ml-20">
        {/* Top bar — mobile only */}
        <header className="lg:hidden flex items-center justify-between px-5 py-4 border-b border-outline-variant/20 bg-white sticky top-0 z-40">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl overflow-hidden">
              <img src={logo} alt="nexus_ai" className="h-full w-full object-contain" />
            </div>
            <p className="font-semibold text-lg text-on-surface tracking-tight">nexus_ai</p>
          </div>
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setCartOpen(true)}
              className="relative flex h-9 w-9 items-center justify-center rounded-full bg-surface-container-low text-on-surface/60"
            >
              <ShoppingCart className="h-4 w-4" />
              {activeCartCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-secondary text-[8px] font-bold text-white">
                  {activeCartCount}
                </span>
              )}
            </button>
            <button
              onClick={() => setProfileOpen(!profileOpen)}
              className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-container text-primary text-xs font-semibold"
            >
              {patientName.charAt(0)}
            </button>
          </div>
        </header>

        <div className="px-6 py-6 md:px-8 lg:px-10 xl:px-12 max-w-7xl mx-auto pb-24 lg:pb-12">
          {children}
        </div>
      </main>

      {/* ─── Mobile Bottom Tab Bar ─── */}
      <nav className="fixed bottom-0 left-0 right-0 z-50 flex items-center justify-around border-t border-outline-variant/20 bg-white px-1 py-1 lg:hidden">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`relative flex flex-1 flex-col items-center justify-center gap-0.5 py-2 transition-colors ${
                isActive ? 'text-primary' : 'text-on-surface/40'
              }`}
            >
              {isActive && (
                <motion.div
                  layoutId="mobile-tab-indicator"
                  className="absolute top-0 left-1/2 -translate-x-1/2 h-[3px] w-8 rounded-full bg-primary"
                  transition={{ type: 'spring', duration: 0.4, bounce: 0.15 }}
                />
              )}
              <tab.icon className="h-5 w-5" />
              <span className="text-[0.6rem] font-medium">{tab.label}</span>
            </button>
          );
        })}
      </nav>

      {/* ─── Slide-over Universal Cart Drawer ─── */}
      <AnimatePresence>
        {cartOpen && (
          <>
            {/* Backdrop Blur overlay */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setCartOpen(false)}
              className="fixed inset-0 z-[100] bg-black/30 backdrop-blur-sm"
            />

            {/* Side Drawer Panel */}
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 25, stiffness: 220 }}
              className="fixed right-0 top-0 bottom-0 z-[101] w-full max-w-md bg-white border-l border-outline-variant/20 shadow-2xl flex flex-col h-full overflow-hidden"
            >
              {/* Header */}
              <div className="p-6 border-b border-outline-variant/20 flex items-center justify-between bg-surface-container-lowest">
                <div>
                  <h3 className="font-serif text-xl font-bold text-on-surface flex items-center gap-2">
                    <ShoppingCart className="h-5 w-5 text-primary" /> Gemini Cart
                  </h3>
                  <p className="text-xs text-on-surface/50 mt-0.5">Cross-Surface Background Monitoring</p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCheckAvailability}
                    disabled={isCheckingAvailability}
                    className="river-stone-btn bg-primary-fixed text-primary text-xs font-bold px-3 py-2 flex items-center gap-1.5 disabled:opacity-50"
                  >
                    {isCheckingAvailability ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : (
                      <Sparkles className="h-3.5 w-3.5" />
                    )}
                    Verify
                  </button>
                  <button
                    onClick={() => setCartOpen(false)}
                    className="p-1.5 rounded-full hover:bg-surface-container-high transition-colors"
                  >
                    <X className="h-5 w-5 text-on-surface/60" />
                  </button>
                </div>
              </div>

              {/* Items List */}
              <div className="flex-1 overflow-y-auto p-6 space-y-4">
                {errorMsg && (
                  <div className="p-4 rounded-xl bg-terracotta/10 text-terracotta text-sm flex items-center gap-2">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    <p className="leading-tight">{errorMsg}</p>
                  </div>
                )}

                {cartItems.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-16 text-center text-on-surface/40 space-y-4">
                    <div className="p-4 bg-surface-container-high rounded-full">
                      <ShoppingCart className="h-10 w-10 text-on-surface/30" />
                    </div>
                    <div className="space-y-1">
                      <p className="font-semibold text-on-surface/70">Your Universal Cart is empty</p>
                      <p className="text-xs max-w-xs leading-normal">
                        Save prescription alternatives, medicines, or marketplace ingredients and track them here automatically.
                      </p>
                    </div>
                  </div>
                ) : (
                  cartItems.map((item) => {
                    const isPurchased = item.status === 'purchased';
                    const isOutOfStock = item.status === 'out_of_stock';
                    const isPriceDrop = item.status === 'price_drop';
                    const isChecking = item.status === 'checking';
                    
                    let bgClass = 'bg-surface-container-low border-outline-variant/30';
                    let statusLabel = 'Tracking';
                    let statusColor = 'bg-on-surface/10 text-on-surface/75';

                    if (isPurchased) {
                      bgClass = 'bg-surface-container-lowest border-outline-variant/10 opacity-70';
                      statusLabel = 'Purchased';
                      statusColor = 'bg-primary-fixed/30 text-primary';
                    } else if (isOutOfStock) {
                      bgClass = 'bg-terracotta/5 border-terracotta/20';
                      statusLabel = 'Out of Stock';
                      statusColor = 'bg-terracotta/10 text-terracotta';
                    } else if (isPriceDrop) {
                      bgClass = 'bg-amber-500/5 border-amber-500/35 shadow-[0_4px_12px_rgba(245,158,11,0.05)]';
                      statusLabel = 'Price Drop Deal';
                      statusColor = 'bg-amber-500/10 text-amber-600 animate-pulse font-semibold';
                    } else if (isChecking) {
                      statusLabel = 'Checking...';
                      statusColor = 'bg-primary-fixed/20 text-primary';
                    }

                    return (
                      <motion.div
                        layout
                        key={item.id}
                        className={`rounded-2xl border p-4 transition-all duration-300 relative group ${bgClass}`}
                      >
                        <div className="flex justify-between items-start gap-4">
                          <div className="space-y-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <span className={`text-[0.65rem] uppercase tracking-wider px-2 py-0.5 rounded-full font-bold ${statusColor}`}>
                                {statusLabel}
                              </span>
                              <span className="text-[0.65rem] text-on-surface/40 uppercase tracking-widest">
                                {item.item_type}
                              </span>
                            </div>
                            <p className={`font-serif font-bold text-base text-on-surface truncate leading-tight ${isPurchased ? 'line-through text-on-surface/40' : ''}`}>
                              {item.item_name}
                            </p>
                            {item.source_url && (
                              <a
                                href={item.source_url}
                                target="_blank"
                                rel="noreferrer"
                                className="text-[0.7rem] text-primary flex items-center gap-1 hover:underline"
                              >
                                View product URL <ExternalLink className="h-3 w-3" />
                              </a>
                            )}
                          </div>
                          
                          <button
                            onClick={() => handleDeleteItem(item.id)}
                            className="p-1.5 rounded-lg text-on-surface/30 hover:text-terracotta hover:bg-terracotta/5 transition-all duration-200 shrink-0"
                            title="Remove"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>

                        {/* Price Details / Coupon Code */}
                        <div className="mt-3 flex items-baseline justify-between pt-2 border-t border-outline-variant/10">
                          <div>
                            {isPriceDrop && item.original_price ? (
                              <div className="flex items-center gap-2">
                                <span className="text-xs line-through text-on-surface/40">
                                  ${item.original_price.toFixed(2)}
                                </span>
                                <span className="text-sm font-bold text-primary">
                                  ${item.price?.toFixed(2)}
                                </span>
                              </div>
                            ) : item.price ? (
                              <span className="text-sm font-bold text-on-surface">
                                ${item.price.toFixed(2)}
                              </span>
                            ) : (
                              <span className="text-xs text-on-surface/40">Price pending check</span>
                            )}

                            {isPriceDrop && item.coupon_code && (
                              <p className="text-[0.7rem] text-amber-600 bg-amber-500/10 px-2 py-0.5 rounded-lg mt-1 inline-block">
                                Code: {item.coupon_code}
                              </p>
                            )}
                          </div>

                          {!isPurchased && !isOutOfStock && !isChecking && (
                            <button
                              onClick={() => handleStartCheckout(item)}
                              className="river-stone-btn bg-on-surface text-surface hover:bg-primary hover:text-white px-3 py-1.5 text-xs font-bold flex items-center gap-1.5 shadow-sm"
                            >
                              <CreditCard className="h-3.5 w-3.5" /> GPay Buy
                            </button>
                          )}

                          {isPurchased && (
                            <span className="text-[0.7rem] text-on-surface/40 italic flex items-center gap-1">
                              CQ-ORD-{item.id} <CheckCircle2 className="h-3.5 w-3.5 text-primary" />
                            </span>
                          )}
                        </div>
                      </motion.div>
                    );
                  })
                )}
              </div>

              {/* Add Web Link Manual Form */}
              <div className="p-6 border-t border-outline-variant/20 bg-surface-container-lowest">
                <p className="text-xs font-bold text-on-surface/60 uppercase tracking-widest mb-3 flex items-center gap-1.5">
                  <Plus className="h-3.5 w-3.5" /> Simulate Cross-Surface Save
                </p>
                <form onSubmit={handleAddCustomItem} className="space-y-3">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      placeholder="Med/Ingredient name (e.g. upma)"
                      className="input-shell text-xs flex-1"
                      value={customItemName}
                      onChange={(e) => setCustomItemName(e.target.value)}
                      required
                    />
                    <select
                      className="input-shell text-xs w-28 appearance-none bg-white border border-outline-variant/30"
                      value={customItemType}
                      onChange={(e) => setCustomItemType(e.target.value as any)}
                    >
                      <option value="ingredient">Ingredient</option>
                      <option value="medicine">Medicine</option>
                    </select>
                  </div>
                  <button
                    type="submit"
                    disabled={isAddingCustom || !customItemName.trim()}
                    className="river-stone-btn w-full bg-gradient-to-br from-primary to-primary-container text-surface text-xs font-bold py-3 hover:shadow-md disabled:opacity-50"
                  >
                    {isAddingCustom ? (
                      <><Loader2 className="h-3.5 w-3.5 animate-spin inline mr-1.5" /> Saving...</>
                    ) : (
                      'Save to Cart'
                    )}
                  </button>
                </form>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* ─── Premium Google Pay Checkout Modal ─── */}
      <AnimatePresence>
        {checkoutItem && (
          <div className="fixed inset-0 z-[150] flex items-end sm:items-center justify-center p-4 bg-black/40 backdrop-blur-sm">
            <motion.div
              initial={{ y: 100, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: 100, opacity: 0 }}
              className="w-full max-w-md bg-[#f8f9fa] rounded-t-3xl sm:rounded-3xl shadow-2xl overflow-hidden flex flex-col border border-outline-variant/10"
            >
              {/* Header (GPay branded styling) */}
              <div className="bg-[#1a1b1f] text-white p-6 flex justify-between items-center">
                <div className="flex items-center gap-2">
                  <span className="font-serif font-black tracking-tighter text-xl">Google Pay</span>
                  <span className="text-[0.65rem] bg-white/20 px-2 py-0.5 rounded-md font-sans">Simulated Checkout</span>
                </div>
                <button
                  onClick={() => setCheckoutItem(null)}
                  disabled={isPaying}
                  className="p-1.5 rounded-full hover:bg-white/10 transition-colors text-white/70 disabled:opacity-30"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Checkout content */}
              <div className="p-6 flex-1 space-y-6">
                {!paySuccess ? (
                  <>
                    {/* Order summary */}
                    <div className="space-y-3">
                      <p className="text-xs uppercase tracking-widest text-on-surface/40 font-bold">Checkout Summary</p>
                      <div className="bg-white rounded-2xl p-4 border border-outline-variant/20 flex justify-between items-center gap-4">
                        <div>
                          <p className="font-semibold text-on-surface leading-tight">{checkoutItem.item_name}</p>
                          <p className="text-xs text-on-surface/40 capitalize mt-1">{checkoutItem.item_type}</p>
                        </div>
                        <span className="font-bold text-primary font-serif">
                          ${checkoutItem.price?.toFixed(2) ?? '15.00'}
                        </span>
                      </div>
                    </div>

                    {/* Ship to Address */}
                    <div className="space-y-2">
                      <p className="text-xs uppercase tracking-widest text-on-surface/40 font-bold">Delivery Address</p>
                      <div className="bg-white rounded-2xl p-4 border border-outline-variant/20 text-sm leading-relaxed text-on-surface/75">
                        <p className="font-bold text-on-surface">Shreesha Bhat</p>
                        <p>123 Health Ave, Outer Ring Road</p>
                        <p>Bangalore, KA 560103, India</p>
                      </div>
                    </div>

                    {/* Payment Info */}
                    <div className="space-y-2">
                      <p className="text-xs uppercase tracking-widest text-on-surface/40 font-bold">Payment Method</p>
                      <div className="bg-white rounded-2xl p-4 border border-outline-variant/20 flex items-center justify-between text-sm text-on-surface/75">
                        <div className="flex items-center gap-3">
                          <div className="p-1 bg-surface-container-high rounded border border-outline-variant/20">
                            <CreditCard className="h-5 w-5 text-[#4285F4]" />
                          </div>
                          <div>
                            <p className="font-semibold">Visa ···· 9012</p>
                            <p className="text-xs text-on-surface/40">Connected to Google Pay</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Price calculation sheet */}
                    <div className="space-y-2 text-sm text-on-surface/60">
                      <div className="flex justify-between">
                        <span>Subtotal</span>
                        <span>${checkoutItem.price?.toFixed(2) ?? '15.00'}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Estimated Tax</span>
                        <span>$0.00</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Shipping</span>
                        <span className="text-[#0f9d58] font-medium">FREE</span>
                      </div>
                      <div className="flex justify-between text-base font-bold text-on-surface pt-2 border-t border-outline-variant/25">
                        <span>Total Charge</span>
                        <span>${checkoutItem.price?.toFixed(2) ?? '15.00'}</span>
                      </div>
                    </div>

                    {/* Action Button */}
                    <button
                      onClick={handleExecuteGPay}
                      disabled={isPaying}
                      className="w-full bg-[#1a1b1f] hover:bg-black text-white py-4 rounded-2xl font-bold transition-colors flex items-center justify-center gap-2 shadow-lg disabled:opacity-75"
                    >
                      {isPaying ? (
                        <>
                          <Loader2 className="h-5 w-5 animate-spin text-white" />
                          <span>Authorizing with Google Pay...</span>
                        </>
                      ) : (
                        <>
                          <span>Pay with Google Pay</span>
                        </>
                      )}
                    </button>
                  </>
                ) : (
                  /* Success Screen with custom check mark animation */
                  <div className="flex flex-col items-center justify-center py-10 space-y-6 text-center">
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: 'spring', damping: 10 }}
                      className="h-16 w-16 bg-[#0f9d58] rounded-full flex items-center justify-center text-white shadow-lg"
                    >
                      <Check className="h-8 w-8 stroke-[3]" />
                    </motion.div>

                    <div className="space-y-2">
                      <h4 className="font-serif text-2xl font-bold text-on-surface">Payment Successful</h4>
                      <p className="text-xs text-on-surface/50 max-w-xs leading-normal">
                        Your checkout of <span className="font-medium text-on-surface">{checkoutItem.item_name}</span> is complete. SMS & Gmail restock/deal alerts updated.
                      </p>
                    </div>

                    <div className="bg-white rounded-2xl p-4 border border-outline-variant/20 w-full text-xs text-on-surface/60 space-y-2 leading-relaxed text-left">
                      <div className="flex justify-between">
                        <span>Order Reference:</span>
                        <span className="font-mono font-bold text-on-surface">{gpayOrderId}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Paid amount:</span>
                        <span className="font-bold text-[#0f9d58]">${checkoutItem.price?.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Authorized payment:</span>
                        <span>Google Pay (Visa •••• 9012)</span>
                      </div>
                    </div>

                    <button
                      onClick={() => setCheckoutItem(null)}
                      className="w-full river-stone-btn bg-gradient-to-br from-primary to-primary-container text-white py-3 font-bold"
                    >
                      Continue
                    </button>
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export type { TabId };
