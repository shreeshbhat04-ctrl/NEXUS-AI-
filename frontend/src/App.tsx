import { useState } from 'react';
import { AnimatePresence } from 'motion/react';
import { Layout, type TabId } from './patient/components/Layout';
import { DashboardScreen } from './patient/screens/DashboardScreen';
import { CareMazeScreen } from './patient/screens/CareMazeScreen';
import { MedicationHubScreen } from './patient/screens/MedicationHubScreen';
import { FinancialAdvocateScreen } from './patient/screens/FinancialAdvocateScreen';
import { HistoryScreen } from './patient/screens/HistoryScreen';
import { HITLScreen } from './patient/screens/HITLScreen';
import { LoginScreen } from './patient/screens/LoginScreen';
import { AboutScreen } from './patient/screens/AboutScreen';

import { Profile } from './patient/screens/Profile';
import { VoiceAssistant } from './patient/components/VoiceAssistant';
import { useWorkspace } from './patient/hooks/useWorkspace';
import { DoctorWorkspaceScreen } from './doctor/screens/DoctorWorkspaceScreen';
import { DoctorLayout } from './doctor/components/DoctorLayout';
import MedicalNotebookScreen from './doctor/screens/MedicalNotebookScreen';

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
    return <DoctorPortal patientId={loggedInPatientId} onRoleChange={() => setRole('patient')} onLogout={handleLogout} />;
  }

  return <AuthenticatedApp patientId={loggedInPatientId} onRoleChange={() => setRole('doctor')} onLogout={handleLogout} />;
}

function DoctorPortal({
  patientId,
  onRoleChange,
  onLogout,
}: {
  patientId: number;
  onRoleChange: () => void;
  onLogout: () => void;
}) {
  const [activeTab, setActiveTab] = useState<'workspace' | 'notebook'>('workspace');

  const renderScreen = () => {
    switch (activeTab) {
      case 'workspace':
        return <DoctorWorkspaceScreen patientId={patientId} onRoleChange={onRoleChange} />;
      case 'notebook':
        return <MedicalNotebookScreen />;
      default:
        return <DoctorWorkspaceScreen patientId={patientId} onRoleChange={onRoleChange} />;
    }
  };

  return (
    <DoctorLayout
      activeTab={activeTab}
      onTabChange={setActiveTab}
      doctorName="Dr. Shaun Murphy"
      onRoleChange={onRoleChange}
      onLogout={onLogout}
    >
      <AnimatePresence mode="wait">
        <div key={activeTab} className="min-h-full min-w-0 w-full">
          {renderScreen()}
        </div>
      </AnimatePresence>
    </DoctorLayout>
  );
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
      case 'financial-advocate':
        return <FinancialAdvocateScreen workspace={workspace} loading={loading} error={error} onRefresh={refresh} patientId={patientId} />;
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
