import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { User, CheckCircle2, MessageSquare, ClipboardList } from 'lucide-react';
import logo from '../../assets/logo.png';
import { SoftCard, Pill } from '../../shared/components/ui';
import {
  fetchDoctors,
  fetchDoctorTasks,
  surgeonImage,
  patient1Image,
  patient2Image,
  patient3Image,
  patient4Image,
  type DoctorProfile,
  type DoctorTask,
  fetchChatThreads,
  fetchChatMessages,
  sendChatMessage,
  createChatThread,
  type ChatThreadItem,
  type ChatMessageItem,
} from '../../shared/lib/api';


export function DoctorWorkspaceScreen({ patientId, onRoleChange }: { patientId: number; onRoleChange: () => void }) {
  const [profileOpen, setProfileOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'tasks' | 'chat' | 'records'>('tasks');
  const [doctors, setDoctors] = useState<DoctorProfile[]>([]);
  const [selectedDoctorId, setSelectedDoctorId] = useState<number | null>(null);
  const [tasks, setTasks] = useState<DoctorTask[]>([]);
  const [tasksLoading, setTasksLoading] = useState(false);
  const [tasksError, setTasksError] = useState<string | null>(null);

  const [activePatientChatId, setActivePatientChatId] = useState(1);
  const [chatThreads, setChatThreads] = useState<ChatThreadItem[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<number | null>(null);
  const [chatMessages, setChatMessages] = useState<ChatMessageItem[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const chatPatients = [
    { id: 1, name: 'Shreesha', condition: 'Eczema, Early stage diabetes', initial: 'S', lastMessage: 'Can you help?', image: patient2Image },
    { id: 2, name: 'Alex M.', condition: 'Hypertension', initial: 'A', lastMessage: 'Thanks, Dr!', image: patient1Image },
    { id: 3, name: 'Sarah K.', condition: 'Asthma review', initial: 'S', lastMessage: 'Refill requested', image: patient3Image },
    { id: 4, name: 'David R.', condition: 'Post-op recovery', initial: 'D', lastMessage: 'Feeling better today.', image: patient4Image }
  ];

  const activePatient = chatPatients.find(p => p.id === activePatientChatId) || chatPatients[0];
  const selectedDoctor = doctors.find((doctor) => doctor.id === selectedDoctorId) ?? doctors[0] ?? null;

  useEffect(() => {
    let active = true;

    const loadDoctors = async () => {
      try {
        const result = await fetchDoctors(patientId);
        if (!active) return;
        setDoctors(result);
        const defaultDoctor = result.find((doctor) => doctor.is_default) ?? result[0] ?? null;
        setSelectedDoctorId(defaultDoctor?.id ?? null);
      } catch (error) {
        if (!active) return;
        setTasksError(error instanceof Error ? error.message : 'Unable to load doctors.');
      }
    };

    void loadDoctors();

    return () => {
      active = false;
    };
  }, [patientId]);

  useEffect(() => {
    if (!selectedDoctorId) return;
    let active = true;

    const loadTasks = async () => {
      try {
        setTasksLoading(true);
        setTasksError(null);
        const result = await fetchDoctorTasks(selectedDoctorId);
        if (!active) return;
        setTasks(result);
      } catch (error) {
        if (!active) return;
        setTasksError(error instanceof Error ? error.message : 'Unable to load Asana tasks.');
      } finally {
        if (active) setTasksLoading(false);
      }
    };

    void loadTasks();

    return () => {
      active = false;
    };
  }, [selectedDoctorId]);

  // Load chat threads for this doctor
  useEffect(() => {
    if (!selectedDoctorId) return;
    let active = true;

    setActiveThreadId(null);
    setChatMessages([]);

    const loadThreads = async () => {
      try {
        setChatLoading(true);
        const result = await fetchChatThreads({ doctor_id: selectedDoctorId });
        if (!active) return;
        setChatThreads(result.threads);
        if (result.threads.length > 0) {
          setActiveThreadId(result.threads[0].id);
        } else {
          setActiveThreadId(null);
        }
      } catch (err) {
        console.error(err);
      } finally {
        if (active) setChatLoading(false);
      }
    };
    void loadThreads();
    return () => { active = false; };
  }, [selectedDoctorId]);

  // Load messages while the chat tab is visible.
  useEffect(() => {
    if (activeTab !== 'chat' || !activeThreadId) return;

    let active = true;
    let inFlight = false;

    const loadMessages = async () => {
      if (inFlight) return;

      inFlight = true;
      try {
        const result = await fetchChatMessages(activeThreadId);
        if (!active) return;
        setChatMessages(result.messages);
      } catch (err) {
        console.error(err);
      } finally {
        inFlight = false;
      }
    };

    void loadMessages();
    const interval = setInterval(loadMessages, 15000);

    return () => {
      active = false;
      clearInterval(interval);
    };
  }, [activeTab, activeThreadId]);

  const handleSendMessage = async () => {
    if (!chatInput.trim() || !activeThreadId || !selectedDoctor || isSending) return;
    const optimisticMessage = chatInput.trim();
    setIsSending(true);
    setChatInput('');
    try {
      const msg = await sendChatMessage(
        activeThreadId,
        'doctor',
        selectedDoctor.full_name,
        optimisticMessage
      );
      setChatMessages(prev => [...prev, msg]);
    } catch (err) {
      console.error(err);
      setChatInput(optimisticMessage); // revert on error
    } finally {
      setIsSending(false);
    }
  };

  const handleNewThread = async () => {
    if (!selectedDoctorId) return;
    try {
      const thread = await createChatThread(patientId, selectedDoctorId, 'New consultation');
      setChatThreads(prev => [thread, ...prev]);
      setActiveThreadId(thread.id);
      setChatMessages([]);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex h-screen w-full bg-surface text-on-surface overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 border-r border-outline-variant/30 bg-surface-container-lowest flex flex-col">
        <div className="p-6 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-surface-container shadow-sm overflow-hidden">
            <img src={logo} alt="nexus_ai" className="h-6 w-6 object-contain" />
          </div>
          <div>
            <h1 className="font-serif font-semibold text-primary leading-tight">Provider<br/>Workspace</h1>
          </div>
        </div>

        <nav className="flex-1 px-4 space-y-2 mt-4">
          <button 
            onClick={() => setActiveTab('tasks')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${activeTab === 'tasks' ? 'bg-primary-container text-on-primary-container font-medium' : 'hover:bg-surface-container-low text-on-surface/70'}`}
          >
            <ClipboardList className="h-5 w-5" />
            Asana Tasks
            {tasks.length > 0 && <span className="ml-auto bg-terracotta text-white text-xs px-2 py-0.5 rounded-full">{tasks.length}</span>}
          </button>
          <button 
            onClick={() => setActiveTab('chat')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${activeTab === 'chat' ? 'bg-primary-container text-on-primary-container font-medium' : 'hover:bg-surface-container-low text-on-surface/70'}`}
          >
            <MessageSquare className="h-5 w-5" />
            Patient Chat
          </button>
          <button 
            onClick={() => setActiveTab('records')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-colors ${activeTab === 'records' ? 'bg-primary-container text-on-primary-container font-medium' : 'hover:bg-surface-container-low text-on-surface/70'}`}
          >
            <User className="h-5 w-5" />
            Biodata & Rx
          </button>
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-20 border-b border-outline-variant/30 px-8 flex items-center justify-between shrink-0">
          <h2 className="font-serif text-2xl">
            {activeTab === 'tasks' ? 'Task Queue' : activeTab === 'chat' ? 'Patient Communications' : 'Patient Records'}
          </h2>
          
          <div className="relative">
            <button
              onClick={() => setProfileOpen(!profileOpen)}
              className="flex h-12 w-12 items-center justify-center rounded-full bg-surface-container-low text-on-surface/70 transition-colors hover:bg-surface-container-high"
            >
              <User className="h-5 w-5" />
            </button>
            
            {profileOpen && (
              <div className="absolute right-0 top-[3.5rem] w-64 rounded-2xl bg-surface-container-low p-4 shadow-xl border border-outline-variant/30 z-50">
                <div className="flex flex-col items-center">
                  <div className="h-16 w-16 rounded-full border-2 border-primary/20 overflow-hidden mb-3 shadow-sm">
                    <img src={surgeonImage} alt="Dr. Strange" className="h-full w-full object-cover" />
                  </div>
                  <h3 className="font-serif font-medium text-lg text-on-surface">{selectedDoctor?.full_name ?? 'Doctor'}</h3>
                  <p className="text-sm text-on-surface/60 mb-4">{selectedDoctor?.specialty ?? 'Provider Account'}</p>
                  <div className="w-full h-px bg-outline-variant/30 mb-2"></div>
                  <button 
                    onClick={onRoleChange}
                    className="w-full py-2 text-sm text-left text-primary hover:text-primary/80 transition-colors font-medium"
                  >
                    Switch to Patient View
                  </button>
                </div>
              </div>
            )}
          </div>
        </header>

        <main className="flex-1 overflow-auto p-8">
          <AnimatePresence mode="wait">
            {activeTab === 'tasks' && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="max-w-4xl space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <p className="text-sm text-on-surface/55">Asana assignee</p>
                    <h3 className="font-serif text-xl">{selectedDoctor?.full_name ?? 'No doctor mapped'}</h3>
                  </div>
                  {doctors.length > 1 ? (
                    <select
                      value={selectedDoctorId ?? ''}
                      onChange={(event) => setSelectedDoctorId(Number(event.target.value))}
                      className="input-shell max-w-xs appearance-none"
                    >
                      {doctors.map((doctor) => (
                        <option key={doctor.id} value={doctor.id}>
                          {doctor.full_name}
                        </option>
                      ))}
                    </select>
                  ) : null}
                </div>

                {tasksError ? (
                  <SoftCard className="border-secondary/30 bg-secondary-container/20 text-secondary">
                    {tasksError}
                  </SoftCard>
                ) : null}

                {tasksLoading ? (
                  <SoftCard className="text-center py-12">
                    <h3 className="font-serif text-xl">Loading Asana tasks...</h3>
                    <p className="text-on-surface/60 mt-2">Fetching tasks assigned to {selectedDoctor?.full_name ?? 'this doctor'}.</p>
                  </SoftCard>
                ) : tasks.length === 0 ? (
                  <SoftCard className="text-center py-12">
                    <CheckCircle2 className="h-12 w-12 text-sage mx-auto mb-4" />
                    <h3 className="font-serif text-xl">All caught up!</h3>
                    <p className="text-on-surface/60 mt-2">No pending Asana tasks in your queue.</p>
                  </SoftCard>
                ) : (
                  tasks.map(task => (
                    <SoftCard key={task.task_id} className="flex items-center justify-between hover:border-primary/30 transition-colors">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1">
                          <Pill tone={task.completed ? 'sage' : 'sand'}>{task.completed ? 'Done' : 'Open'}</Pill>
                          {task.due_on && <span className="text-xs text-on-surface/45 uppercase tracking-wider">Due {task.due_on}</span>}
                        </div>
                        <h4 className="text-lg font-medium">{task.name}</h4>
                        <p className="text-sm text-on-surface/60 mt-1">{task.notes || 'Pending review and clearance.'}</p>
                      </div>
                      {task.permalink_url ? (
                        <a
                          href={task.permalink_url}
                          target="_blank"
                          rel="noreferrer"
                          className="river-stone-btn bg-surface-container-low px-5 py-2.5 text-sm text-primary hover:bg-primary-container transition-colors shrink-0"
                        >
                          Open in Asana
                        </a>
                      ) : (
                        <span className="rounded-full bg-surface-container-low px-5 py-2.5 text-sm text-on-surface/40 shrink-0">
                          No Asana link
                        </span>
                      )}
                    </SoftCard>
                  ))
                )}
              </motion.div>
            )}

            {activeTab === 'chat' && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="h-full flex gap-6 max-w-5xl">
                {/* Thread List Sidebar */}
                <SoftCard className="w-72 flex flex-col bg-surface-container-lowest border border-outline-variant/30 h-[calc(100vh-12rem)] overflow-hidden shrink-0">
                  <div className="border-b border-outline-variant/30 pb-4 mb-2 shrink-0 flex items-center justify-between">
                    <h3 className="font-serif text-lg">Chat Threads</h3>
                    <button onClick={handleNewThread} className="text-xs text-primary hover:text-primary/80 font-medium">+ New</button>
                  </div>
                  <div className="flex-1 overflow-y-auto -mx-2 px-2 space-y-1">
                    {chatLoading ? (
                      <p className="text-sm text-on-surface/50 text-center py-4">Loading...</p>
                    ) : chatThreads.length === 0 ? (
                      <p className="text-sm text-on-surface/50 text-center py-4">No chat threads yet.</p>
                    ) : (
                      chatThreads.map(thread => (
                        <button
                          key={thread.id}
                          onClick={() => setActiveThreadId(thread.id)}
                          className={`w-full text-left p-3 rounded-xl transition-colors ${activeThreadId === thread.id ? 'bg-primary-container text-on-primary-container' : 'hover:bg-surface-container-low'}`}
                        >
                          <div className="min-w-0">
                            <h4 className="font-medium text-sm truncate">{thread.subject}</h4>
                            <p className="text-xs opacity-70 truncate">
                              {thread.last_message ? thread.last_message.body : 'No messages yet'}
                            </p>
                            <p className="text-xs opacity-40 mt-0.5">
                              {thread.message_count} message{thread.message_count !== 1 ? 's' : ''}
                            </p>
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                </SoftCard>

                {/* Active Chat Area */}
                <SoftCard className="flex-1 flex flex-col bg-surface-container-lowest border border-outline-variant/30 h-[calc(100vh-12rem)]">
                  {activeThreadId ? (
                    <>
                      <div className="border-b border-outline-variant/30 pb-4 mb-4 shrink-0">
                        <h3 className="font-serif text-lg">
                          {chatThreads.find(t => t.id === activeThreadId)?.subject || 'Conversation'}
                        </h3>
                        <p className="text-sm text-on-surface/60">
                          Patient #{chatThreads.find(t => t.id === activeThreadId)?.patient_id} &middot; Thread #{activeThreadId}
                        </p>
                      </div>

                      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
                        {chatMessages.length === 0 ? (
                          <div className="flex items-center justify-center h-full text-on-surface/50 text-sm">
                            No messages in this thread yet. Start the conversation!
                          </div>
                        ) : (
                          chatMessages.map(msg => (
                            <div key={msg.id} className={`flex gap-4 ${msg.sender_role === 'doctor' ? 'flex-row-reverse' : ''}`}>
                              <div className={`h-10 w-10 rounded-full shrink-0 flex items-center justify-center text-sm font-medium shadow-sm ${msg.sender_role === 'doctor' ? 'bg-primary-container text-on-primary-container' : 'bg-surface-container-low text-on-surface/70'}`}>
                                {msg.sender_display_name.charAt(0).toUpperCase()}
                              </div>
                              <div className={`max-w-[70%] p-4 rounded-2xl ${msg.sender_role === 'doctor' ? 'bg-primary-fixed/30 rounded-tr-none' : 'bg-surface-container-low rounded-tl-none'}`}>
                                <p className="text-xs font-medium opacity-60 mb-1">{msg.sender_display_name}</p>
                                <p className="text-sm leading-relaxed">{msg.body}</p>
                                <p className="text-xs opacity-40 mt-1">{new Date(msg.created_at).toLocaleTimeString()}</p>
                              </div>
                            </div>
                          ))
                        )}
                      </div>

                      <div className="mt-4 pt-4 border-t border-outline-variant/30 flex gap-3 shrink-0">
                        <input
                          type="text"
                          value={chatInput}
                          onChange={(e) => setChatInput(e.target.value)}
                          onKeyDown={(e) => { if (e.key === 'Enter' && !isSending) handleSendMessage(); }}
                          placeholder="Type a message..."
                          className="input-shell flex-1 bg-surface"
                          disabled={isSending}
                        />
                        <button 
                          onClick={handleSendMessage} 
                          disabled={isSending}
                          className="river-stone-btn bg-primary text-surface px-6 font-medium disabled:opacity-50"
                        >
                          {isSending ? 'Sending...' : 'Send'}
                        </button>
                      </div>
                    </>
                  ) : (
                    <div className="flex items-center justify-center h-full text-on-surface/50 text-sm">
                      Select a thread or create a new one to start chatting.
                    </div>
                  )}
                </SoftCard>
              </motion.div>
            )}

            {activeTab === 'records' && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="h-full flex gap-6 max-w-5xl">
                {/* Patient List Sidebar */}
                <SoftCard className="w-72 flex flex-col bg-surface-container-lowest border border-outline-variant/30 h-[calc(100vh-12rem)] overflow-hidden shrink-0">
                  <div className="border-b border-outline-variant/30 pb-4 mb-2 shrink-0">
                    <h3 className="font-serif text-lg">Patient Directory</h3>
                  </div>
                  <div className="flex-1 overflow-y-auto -mx-2 px-2 space-y-1">
                    {chatPatients.map(p => (
                      <button 
                        key={p.id}
                        onClick={() => setActivePatientChatId(p.id)}
                        className={`w-full text-left p-3 rounded-xl transition-colors ${activePatientChatId === p.id ? 'bg-primary-container text-on-primary-container' : 'hover:bg-surface-container-low'}`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`h-10 w-10 rounded-full shrink-0 flex items-center justify-center overflow-hidden border border-outline-variant/10 shadow-sm ${activePatientChatId === p.id ? 'bg-surface' : 'bg-primary-container'}`}>
                            <img src={p.image} alt={p.name} className="h-full w-full object-cover" />
                          </div>
                          <div className="min-w-0">
                            <h4 className="font-medium text-sm truncate">{p.name}</h4>
                            <p className="text-xs opacity-70 truncate">{p.condition}</p>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </SoftCard>

                {/* Biodata Area */}
                <SoftCard className="flex-1 flex flex-col bg-surface-container-lowest border border-outline-variant/30 h-[calc(100vh-12rem)] overflow-y-auto p-8">
                  <div className="flex items-center gap-6 mb-8">
                    <div className="h-20 w-20 rounded-full border-4 border-primary/10 overflow-hidden shadow-lg">
                      <img src={activePatient.image} alt={activePatient.name} className="h-full w-full object-cover" />
                    </div>
                    <div>
                      <h2 className="font-serif text-3xl mb-1">{activePatient.name}</h2>
                      <p className="text-on-surface/60">ID: PT-{1000 + activePatient.id} • DoB: 05/12/1985 (38y)</p>
                    </div>
                  </div>

                  <div className="space-y-8">
                    <section>
                      <h3 className="font-serif text-lg mb-3 flex items-center gap-2">
                        <CheckCircle2 className="h-5 w-5 text-primary" /> Active Conditions
                      </h3>
                      <div className="bg-surface-container-low rounded-2xl p-4">
                        <p className="font-medium">{activePatient.condition}</p>
                        <p className="text-sm text-on-surface/60 mt-2">Diagnosed 2023. Currently under active management and monitoring.</p>
                      </div>
                    </section>

                    <section>
                      <h3 className="font-serif text-lg mb-3 flex items-center gap-2">
                        <ClipboardList className="h-5 w-5 text-terracotta" /> Current Prescriptions
                      </h3>
                      <div className="space-y-3">
                        {activePatient.id === 1 ? (
                          <>
                            <div className="bg-surface-container-low rounded-2xl p-4 flex justify-between items-center">
                              <div>
                                <h4 className="font-medium">Metformin 500mg</h4>
                                <p className="text-sm text-on-surface/60">Take 1 tablet twice daily with meals</p>
                              </div>
                              <Pill tone="sand">Active</Pill>
                            </div>
                            <div className="bg-surface-container-low rounded-2xl p-4 flex justify-between items-center">
                              <div>
                                <h4 className="font-medium">Hydrocortisone Cream 1%</h4>
                                <p className="text-sm text-on-surface/60">Apply to affected areas twice daily</p>
                              </div>
                              <Pill tone="sand">Active</Pill>
                            </div>
                          </>
                        ) : (
                          <div className="bg-surface-container-low rounded-2xl p-4 text-center text-on-surface/60 text-sm">
                            No active prescriptions found in system.
                          </div>
                        )}
                      </div>
                    </section>

                    <section>
                      <h3 className="font-serif text-lg mb-3">Recent Vitals</h3>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="bg-surface-container-low rounded-2xl p-4 text-center">
                          <p className="text-sm text-on-surface/60 mb-1">Blood Pressure</p>
                          <p className="text-lg font-medium">120/80</p>
                        </div>
                        <div className="bg-surface-container-low rounded-2xl p-4 text-center">
                          <p className="text-sm text-on-surface/60 mb-1">Heart Rate</p>
                          <p className="text-lg font-medium">72 bpm</p>
                        </div>
                        <div className="bg-surface-container-low rounded-2xl p-4 text-center">
                          <p className="text-sm text-on-surface/60 mb-1">Weight</p>
                          <p className="text-lg font-medium">70 kg</p>
                        </div>
                      </div>
                    </section>
                  </div>
                </SoftCard>
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
