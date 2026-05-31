import { useState } from 'react';
import { AnimatePresence } from 'motion/react';
import { Layout, type TabId } from './components/Layout';
import { DashboardScreen } from './screens/DashboardScreen';
import { CareMazeScreen } from './screens/CareMazeScreen';
import { MedicationHubScreen } from './screens/MedicationHubScreen';
import { HistoryScreen } from './screens/HistoryScreen';
import { HITLScreen } from './screens/HITLScreen';
import { LoginScreen } from './screens/LoginScreen';
import { AboutScreen } from './screens/AboutScreen';

import { Profile } from './screens/Profile';
import { VoiceAssistant } from './components/VoiceAssistant';
import { useWorkspace } from './hooks/useWorkspace';
import { DoctorWorkspaceScreen } from './screens/DoctorWorkspaceScreen';

export default function App() {
  const [loggedInPatientId, setLoggedInPatientId] = useState<number | null>(() => {
    const stored = localStorage.getItem('nexus_ai_patient_id');
    return stored ? Number(stored) : null;
  });

  const [role, setRole] = useState<'patient' | 'doctor'>('patient');

  const handleLogin = (patientId: number) => {
    localStorage.setItem('nexus_ai_patient_id', String(patientId));
    setLoggedInPatientId(patientId);
  };
  
  const handleLogout = () => {
    localStorage.removeItem('nexus_ai_patient_id');
    setLoggedInPatientId(null);
  };

  if (loggedInPatientId === null) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  if (role === 'doctor') {
    return <DoctorWorkspaceScreen patientId={loggedInPatientId} onRoleChange={() => setRole('patient')} />;
  }

  return <AuthenticatedApp patientId={loggedInPatientId} onRoleChange={() => setRole('doctor')} onLogout={handleLogout} />;
}

function AuthenticatedApp({ 
  patientId: initialPatientId, 
  onRoleChange, 
  onLogout 
}: { 
  patientId: number, 
  onRoleChange: () => void, 
  onLogout: () => void 
}) {
  const [activeTab, setActiveTab] = useState<TabId>('dashboard');
  const { workspace, loading, error, refresh, patientId } = useWorkspace(initialPatientId);

  const renderScreen = () => {
    switch (activeTab) {
      case 'dashboard':
        return <DashboardScreen workspace={workspace} loading={loading} error={error} onRefresh={refresh} />;
      case 'care-maze':
        return <CareMazeScreen workspace={workspace} loading={loading} onRefresh={refresh} patientId={patientId} />;
      case 'medications':
        return <MedicationHubScreen workspace={workspace} loading={loading} onRefresh={refresh} patientId={patientId} />;

      case 'hitl':
        return <HITLScreen workspace={workspace} loading={loading} onRefresh={refresh} patientId={patientId} />;
      case 'history':
        return <HistoryScreen workspace={workspace} loading={loading} error={error} />;
      case 'profile':
        return <Profile workspace={workspace} loading={loading} error={error} onRefresh={refresh} patientId={patientId} />;
      case 'about':
        return <AboutScreen workspace={workspace} loading={loading} error={error} onRefresh={refresh} />;
      default:
        return <DashboardScreen workspace={workspace} loading={loading} error={error} onRefresh={refresh} />;
    }
  };

  return (
    <Layout
      patientId={patientId}
      activeTab={activeTab}
      onTabChange={setActiveTab}
      patientName={workspace?.patient.full_name ?? 'your care circle'}
      onRefresh={refresh}
      loading={loading}
      onRoleChange={onRoleChange}
      onLogout={onLogout}
    >
      <AnimatePresence mode="wait">
        <div key={activeTab} className="min-h-full min-w-0 w-full">
          {renderScreen()}
        </div>
      </AnimatePresence>
      <VoiceAssistant patientId={patientId} />
    </Layout>
  );
}
