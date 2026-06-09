import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Grid2X2, 
  Notebook as NotebookIcon, 
  LogOut, 
  ArrowLeftRight,
  User
} from 'lucide-react';
import logo from '../../assets/logo.png';

type DoctorTabId = 'workspace' | 'notebook';

interface DoctorLayoutProps {
  children: React.ReactNode;
  activeTab: DoctorTabId;
  onTabChange: (tab: DoctorTabId) => void;
  doctorName: string;
  onRoleChange: () => void;
  onLogout: () => void;
}

export const DoctorLayout: React.FC<DoctorLayoutProps> = ({
  children,
  activeTab,
  onTabChange,
  doctorName,
  onRoleChange,
  onLogout,
}) => {
  const [profileOpen, setProfileOpen] = useState(false);

  const tabs: Array<{ id: DoctorTabId; icon: React.ComponentType<{ className?: string }>; label: string }> = [
    { id: 'workspace', icon: Grid2X2, label: 'Workspace' },
    { id: 'notebook', icon: NotebookIcon, label: 'Notebook' },
  ];

  return (
    <div className="flex min-h-screen w-full bg-surface">
      {/* ─── Doctor Sidebar ─── */}
      <aside className="hidden lg:flex fixed left-0 top-0 z-50 h-screen w-20 flex-col items-center border-r border-outline-variant/30 bg-white py-6">
        {/* Logo */}
        <button
          onClick={() => onTabChange('workspace')}
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
                <span className={`mt-1 text-[0.55rem] font-medium leading-tight ${
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
          <div className="relative">
            <button
              onClick={() => setProfileOpen(!profileOpen)}
              className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-container text-primary text-sm font-semibold transition-colors hover:bg-primary-fixed"
              title={doctorName}
            >
              {doctorName.charAt(0)}
            </button>

            {/* Profile Dropdown */}
            {profileOpen && (
              <div className="absolute left-[calc(100%+8px)] bottom-0 w-56 rounded-2xl bg-white p-4 shadow-[0_4px_12px_rgba(60,64,67,0.15),0_1px_3px_rgba(60,64,67,0.1)] border border-outline-variant/30 z-50">
                <div className="flex items-center gap-3 mb-3">
                  <div className="h-10 w-10 rounded-full bg-primary-container text-primary flex items-center justify-center text-sm font-semibold">
                    {doctorName.charAt(0)}
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium text-sm text-on-surface truncate">{doctorName}</p>
                    <p className="text-xs text-on-surface/50">Clinician / Provider</p>
                  </div>
                </div>

                <div className="w-full h-px bg-outline-variant/40 mb-2" />

                <button
                  onClick={onRoleChange}
                  className="w-full flex items-center gap-2 py-2 text-sm text-primary hover:text-primary/80 transition-colors font-medium rounded-lg hover:bg-primary-fixed/50 px-2"
                >
                  <ArrowLeftRight className="h-4 w-4" />
                  Patient Portal
                </button>
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
            <p className="font-semibold text-lg text-on-surface tracking-tight">nexus_ai doctor</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setProfileOpen(!profileOpen)}
              className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-container text-primary text-xs font-semibold"
            >
              {doctorName.charAt(0)}
            </button>
          </div>
        </header>

        {activeTab === 'workspace' ? (
          children
        ) : (
          <div className="px-6 py-6 md:px-8 lg:px-10 xl:px-12 max-w-7xl mx-auto pb-24 lg:pb-12">
            {children}
          </div>
        )}
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
                  layoutId="mobile-doctor-tab-indicator"
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
    </div>
  );
};
