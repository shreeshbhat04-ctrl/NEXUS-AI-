import React, { useRef, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Mic, Square, Loader2, X, Volume2, Upload, Send, MessageSquare } from 'lucide-react';
import { confirmAction, API_BASE_URL, sendTextMessage, type ActionOption } from '../lib/api';
import { Pill } from './ui';

interface VoiceAssistantProps {
  patientId: number;
}

interface AudioChunk {
  type: 'metadata' | 'audio' | 'error';
  chunk?: string;
  transcript?: string;
  full_message?: string;
  route_type?: string;
  primary_model?: string;
  action_id?: number;
  options?: ActionOption[];
  allow_custom_input?: boolean;
  message?: string;
}

export const VoiceAssistant: React.FC<VoiceAssistantProps> = ({ patientId }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [metadata, setMetadata] = useState<Partial<AudioChunk> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState('');
  const [customActionInput, setCustomActionInput] = useState('');
  const [isConfirmingAction, setIsConfirmingAction] = useState(false);
  const [chatInput, setChatInput] = useState('');

  const audioContextRef = useRef<AudioContext | null>(null);
  const audioWorkletNodeRef = useRef<AudioWorkletNode | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const nextStartTimeRef = useRef(0);
  const scheduledSourcesRef = useRef<AudioBufferSourceNode[]>([]);
  const isRecordingRef = useRef(false);

  const synthRef = useRef<SpeechSynthesis | null>(window.speechSynthesis);

  const speakHindi = (text: string) => {
    if (!synthRef.current) return;
    synthRef.current.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    const voices = synthRef.current.getVoices();
    const hindiVoice = voices.find(v => v.lang.includes('hi-IN') || v.lang.includes('hi_IN'));
    if (hindiVoice) utterance.voice = hindiVoice;
    utterance.lang = 'hi-IN';
    utterance.rate = 0.85;
    utterance.pitch = 1.0;
    synthRef.current.speak(utterance);
    console.log('Speaking Hindi safety warning...');
  };

  const downsampleBuffer = (buffer: Float32Array, sampleRate: number, outSampleRate: number) => {
    if (outSampleRate === sampleRate) return buffer;
    const ratio = sampleRate / outSampleRate;
    const newLength = Math.round(buffer.length / ratio);
    const result = new Float32Array(newLength);
    let offsetResult = 0;
    let offsetBuffer = 0;
    while (offsetResult < result.length) {
      const nextOffsetBuffer = Math.round((offsetResult + 1) * ratio);
      let accum = 0, count = 0;
      for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
        accum += buffer[i];
        count++;
      }
      result[offsetResult] = accum / count;
      offsetResult++;
      offsetBuffer = nextOffsetBuffer;
    }
    return result;
  };

  const convertFloat32ToInt16 = (buffer: Float32Array) => {
    let l = buffer.length;
    const buf = new Int16Array(l);
    while (l--) {
      buf[l] = Math.min(1, Math.max(-1, buffer[l])) * 0x7fff;
    }
    return buf.buffer;
  };

  const playAudio = (arrayBuffer: ArrayBuffer) => {
    const ctx = audioContextRef.current;
    if (!ctx) return;
    if (ctx.state === "suspended") ctx.resume();

    const pcmData = new Int16Array(arrayBuffer);
    const float32Data = new Float32Array(pcmData.length);
    for (let i = 0; i < pcmData.length; i++) {
      float32Data[i] = pcmData[i] / 32768.0;
    }

    const buffer = ctx.createBuffer(1, float32Data.length, 24000);
    buffer.getChannelData(0).set(float32Data);

    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(ctx.destination);

    const now = ctx.currentTime;
    nextStartTimeRef.current = Math.max(now, nextStartTimeRef.current);
    source.start(nextStartTimeRef.current);
    nextStartTimeRef.current += buffer.duration;

    scheduledSourcesRef.current.push(source);
    source.onended = () => {
      const idx = scheduledSourcesRef.current.indexOf(source);
      if (idx > -1) scheduledSourcesRef.current.splice(idx, 1);
    };
  };

  const stopAudioPlayback = () => {
    scheduledSourcesRef.current.forEach(s => {
      try { s.stop(); } catch (e) {}
    });
    scheduledSourcesRef.current = [];
    if (audioContextRef.current) {
      nextStartTimeRef.current = audioContextRef.current.currentTime;
    }
  };

  const startRecording = async () => {
    try {
      setError(null);
      setMetadata(null);
      setStatus('Connecting...');

      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsHost = API_BASE_URL.replace(/^https?:\/\//, '');
      const wsUrl = `${protocol}//${wsHost}/orchestration/voice-live-stream/${patientId}`;

      const ws = new WebSocket(wsUrl);
      ws.binaryType = "arraybuffer";
      wsRef.current = ws;

      ws.onopen = async () => {
        setStatus('Listening...');
        
        // Setup AudioContext
        if (!audioContextRef.current) {
          audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
          await audioContextRef.current.audioWorklet.addModule('/pcm-processor.js');
        }
        if (audioContextRef.current.state === 'suspended') {
          await audioContextRef.current.resume();
        }

        mediaStreamRef.current = await navigator.mediaDevices.getUserMedia({ audio: true });
        const source = audioContextRef.current.createMediaStreamSource(mediaStreamRef.current);
        audioWorkletNodeRef.current = new AudioWorkletNode(audioContextRef.current, 'pcm-processor');

        let silenceCooldownBlocks = 0;
        const THRESHOLD = 0.03; // ~1000 in Int16
        const GAIN = 2.5; // Boost volume 2.5x

        audioWorkletNodeRef.current.port.onmessage = (event) => {
          if (isRecordingRef.current && ws.readyState === WebSocket.OPEN) {
            const rawData = event.data as Float32Array;
            let maxVal = 0;
            for (let i = 0; i < rawData.length; i++) {
              const absVal = Math.abs(rawData[i]);
              if (absVal > maxVal) maxVal = absVal;
            }

            const boostedData = new Float32Array(rawData.length);
            for (let i = 0; i < rawData.length; i++) {
              boostedData[i] = rawData[i] * GAIN;
            }

            if (maxVal > THRESHOLD) {
              silenceCooldownBlocks = 12; // Send ~1s of audio after speech stops
            } else if (silenceCooldownBlocks > 0) {
              silenceCooldownBlocks--;
            }

            if (silenceCooldownBlocks > 0) {
              const downsampled = downsampleBuffer(boostedData, audioContextRef.current!.sampleRate, 16000);
              const pcm16 = convertFloat32ToInt16(downsampled);
              ws.send(pcm16);
            }
          }
        };

        source.connect(audioWorkletNodeRef.current);
        const muteGain = audioContextRef.current.createGain();
        muteGain.gain.value = 0;
        audioWorkletNodeRef.current.connect(muteGain);
        muteGain.connect(audioContextRef.current.destination);
      };

      ws.onmessage = (event) => {
        if (typeof event.data === "string") {
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'metadata' || data.type === 'gemini' || data.type === 'user') {
              setMetadata(prev => ({
                ...prev,
                type: 'metadata',
                message: data.text || data.full_message || data.message || prev?.message
              }));
              setStatus('Response incoming...');
            } else if (data.type === 'tool_call') {
              setStatus(`Tool called: ${data.name}`);
            } else if (data.type === 'turn_complete') {
              setStatus('Listening...');
            } else if (data.type === 'interrupted') {
              stopAudioPlayback();
            } else if (data.type === 'error') {
              setError(data.error);
            }
          } catch (e) {
            console.error(e);
          }
        } else if (event.data instanceof ArrayBuffer) {
          playAudio(event.data);
        }
      };

      ws.onclose = () => {
        stopRecording();
      };

      ws.onerror = () => {
        setError("WebSocket error");
        stopRecording();
      };

      setIsRecording(true);
      isRecordingRef.current = true;
    } catch (err) {
      setError('Cannot access microphone or connect to server.');
      stopRecording();
    }
  };

  const stopRecording = () => {
    setIsRecording(false);
    isRecordingRef.current = false;
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((t) => t.stop());
      mediaStreamRef.current = null;
    }
    if (audioWorkletNodeRef.current) {
      audioWorkletNodeRef.current.disconnect();
      audioWorkletNodeRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setStatus('');
    stopAudioPlayback();
  };



  const handleConfirmVoiceAction = async (selectedOption?: string, useCustom: boolean = false) => {
    if (!metadata?.action_id || isConfirmingAction) return;
    const customInput = customActionInput.trim();
    if (useCustom && !customInput) return;

    setIsConfirmingAction(true);
    try {
      if (metadata.action_id === -999) {
        const actionResult =
          selectedOption === 'email_shaun'
            ? 'Drafted an email to Dr. Shaun with risks + context. (Demo successfully routed!)'
            : selectedOption === 'asana_task'
              ? 'Created an Asana review task for Dr. Shaun. (Demo successfully escalated!)'
              : 'Started a doctor chat thread. (Demo successfully connected!)';
        setStatus('Action confirmed');
        setMetadata((prev) => ({ ...(prev || {}), full_message: actionResult, options: [] }));
        setCustomActionInput('');
        return;
      }
      const result = await confirmAction(
        metadata.action_id,
        selectedOption,
        useCustom ? customInput : undefined,
      );
      const resultMessage = (result.result?.message as string | undefined) || `Action ${result.status}.`;
      setStatus('Action confirmed');
      setMetadata((prev) => ({ ...(prev || {}), full_message: resultMessage, options: [] }));
      setCustomActionInput('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to confirm action');
    } finally {
      setIsConfirmingAction(false);
    }
  };

  const handleChatSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const query = chatInput.trim();
    if (!query) return;

    setError(null);
    setMetadata(null);
    setIsProcessing(true);
    setStatus('Thinking...');

    try {
      const result = await sendTextMessage(patientId, query);
      
      setMetadata({
        type: 'metadata',
        transcript: query,
        message: result.message,
        route_type: result.route_type,
        primary_model: result.primary_model,
        action_id: result.action_id,
        options: result.options,
        allow_custom_input: result.allow_custom_input,
      });

      setStatus('Response received');

      // Special check: If the real LLM mentions Aspirin and Fever, still trigger the Hindi safety warning
      const lowerQuery = query.toLowerCase();
      const mentionsAspirin = lowerQuery.includes('aspirin') || lowerQuery.includes('asprin') || lowerQuery.includes('एस्पिरिन');
      const mentionsFever = lowerQuery.includes('fever') || lowerQuery.includes('बुखार');
      
      if (mentionsAspirin && mentionsFever) {
        speakHindi('सावधान: एस्पिरिन (Aspirin) आपकी मिर्गी (Epilepsy) की दवाओं के साथ समस्या पैदा कर सकती है। क्या मैं आपकी मदद डॉक्टर को अपडेट करने में कर सकता हूँ?');
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Chat failed');
    } finally {
      setIsProcessing(false);
      setChatInput('');
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-[100] flex flex-col items-end gap-4">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="w-[450px] flex min-h-[500px] flex-col overflow-hidden rounded-[1.75rem] border border-white/10 bg-surface/95 shadow-[0_24px_54px_-12px_rgba(60,64,67,0.15)] backdrop-blur-2xl"
          >
            <div className="flex items-center justify-between border-b border-white/5 bg-surface-container-lowest/30 p-5">
              <h2 className="font-serif text-[1.2rem] font-bold text-primary">Nexus_ai Agent</h2>
              <button
                onClick={() => setIsOpen(false)}
                className="rounded-full bg-white/5 p-2 text-on-surface/50 transition-colors hover:bg-white/10 hover:text-on-surface"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto p-5">
              {metadata || error ? (
                <div className="space-y-4">
                  <div className="flex items-start justify-between">
                    {metadata ? (
                      <Pill tone={metadata.route_type === 'medical_text' ? 'terracotta' : 'sage'}>
                        {metadata.primary_model?.split('/')[1] || metadata.primary_model}
                      </Pill>
                    ) : (
                      <Pill tone="terracotta">Error</Pill>
                    )}
                  </div>

                  <div className="flex items-start gap-3 rounded-2xl bg-surface-container-lowest/50 p-4 text-[1rem] text-on-surface/80">
                    {!error ? <Volume2 className="mt-1 h-5 w-5 shrink-0 text-primary" /> : null}
                    <div className="flex flex-col">
                      <p className="mb-1 font-bold text-[0.8rem] uppercase tracking-wider text-primary/60">{status || (error ? 'Error' : 'Voice Assistant')}</p>
                      <p className="leading-relaxed">{error || metadata?.message || 'Processing voice...'}</p>
                    </div>
                  </div>

                  {metadata?.action_id && metadata.options && metadata.options.length > 0 && (
                    <div className="rounded-2xl border border-outline-variant/20 bg-surface-container-lowest p-4">
                      <p className="mb-3 text-[0.8rem] font-semibold uppercase tracking-wide text-on-surface/50">Confirm Action</p>
                      <div className="flex flex-wrap gap-2">
                        {metadata.options.map((option) => (
                          <button
                            key={`voice-${metadata.action_id}-${option.value}`}
                            onClick={() => handleConfirmVoiceAction(option.value)}
                            disabled={isConfirmingAction}
                            className="rounded-xl bg-primary-container px-4 py-2.5 text-left text-[0.9rem] text-on-primary-container transition-colors hover:bg-primary/20 disabled:opacity-60"
                          >
                            {option.label}
                          </button>
                        ))}
                      </div>
                      {metadata.allow_custom_input && (
                        <div className="mt-4 flex items-center gap-2">
                          <input
                            type="text"
                            value={customActionInput}
                            onChange={(e) => setCustomActionInput(e.target.value)}
                            placeholder="Type a custom instruction..."
                            className="input-shell h-11 flex-1 text-[0.95rem]"
                          />
                          <button
                            onClick={() => handleConfirmVoiceAction(undefined, true)}
                            disabled={isConfirmingAction}
                            className="rounded-xl bg-secondary-container px-4 py-2.5 text-[0.9rem] font-medium text-on-secondary-container transition-colors hover:bg-secondary/20 disabled:opacity-60"
                          >
                            {isConfirmingAction ? 'Sending...' : 'Send'}
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex h-full flex-col items-center justify-center space-y-4 text-center opacity-50">
                  <MessageSquare className="h-12 w-12 text-primary" />
                  <p className="font-serif text-lg">How can I help you today?</p>
                  <p className="text-sm">Speak, chat, or upload a document.</p>
                </div>
              )}
            </div>

            {/* Bottom Bar: Upload, Chat, Voice */}
            <div className="border-t border-white/5 bg-surface-container-lowest/30 p-4">
              <form onSubmit={handleChatSubmit} className="flex items-center gap-2 rounded-2xl bg-surface-container-lowest p-2 shadow-inner">
                <button type="button" className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-on-surface/50 transition-colors hover:bg-white/5 hover:text-primary">
                  <Upload className="h-5 w-5" />
                </button>
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="Ask Nexus_ai Agent..."
                  className="h-10 flex-1 bg-transparent px-2 text-[0.95rem] text-on-surface outline-none placeholder:text-on-surface/30"
                />
                {chatInput.trim() ? (
                  <button type="submit" className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary-container text-primary transition-colors hover:bg-primary/20">
                    <Send className="h-5 w-5" />
                  </button>
                ) : (
                  <button
                    type="button"
                    onClick={isRecording ? stopRecording : startRecording}
                    disabled={isProcessing}
                    className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-all ${isProcessing ? 'bg-surface-container-high text-on-surface/50' :
                        isRecording ? 'bg-terracotta text-white animate-pulse' : 'bg-primary-container text-primary hover:bg-primary/20'
                      }`}
                  >
                    {isProcessing ? <Loader2 className="h-5 w-5 animate-spin" /> :
                      isRecording ? <Square className="h-5 w-5 fill-current" /> : <Mic className="h-5 w-5" />}
                  </button>
                )}
              </form>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {!isOpen && (
        <motion.button
          onClick={() => setIsOpen(true)}
          whileHover="hover"
          initial="idle"
          className="relative flex h-20 w-20 items-center justify-center rounded-full bg-surface-container-lowest shadow-[0_8px_30px_rgb(0,0,0,0.12)] border border-outline-variant/20 overflow-hidden group transition-shadow hover:shadow-[0_8px_40px_rgb(66,133,244,0.25)]"
        >
          {/* Soft pulsing colorful background layer */}
          <motion.div
            variants={{
              idle: { opacity: 0, scale: 0.8 },
              hover: { opacity: 0.15, scale: 1.2 }
            }}
            transition={{ duration: 0.4 }}
            className="absolute inset-0 bg-gradient-to-tr from-[#4285F4] to-[#A142F4] rounded-full blur-sm"
          />

          {/* Spinning glowing aura */}
          <motion.div
            variants={{
              idle: { opacity: 0, rotate: 0 },
              hover: { opacity: 0.8, rotate: 360 }
            }}
            transition={{
              rotate: { duration: 4, repeat: Infinity, ease: "linear" },
              opacity: { duration: 0.3 }
            }}
            className="absolute inset-[-50%] bg-[conic-gradient(from_0deg,transparent_0_280deg,#4285F4_320deg,#A142F4_340deg,transparent_360deg)] blur-md mix-blend-screen"
          />

          {/* The Gemini Star */}
          <motion.div
            variants={{
              idle: { rotate: 0, scale: 1 },
              hover: { rotate: 180, scale: 1.15 }
            }}
            transition={{ type: "spring", stiffness: 200, damping: 15 }}
            className="relative z-10 drop-shadow-sm"
          >
            <svg viewBox="0 0 24 24" className="h-10 w-10" fill="url(#gemini-gradient)">
              <defs>
                <linearGradient id="gemini-gradient" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
                  <stop stopColor="#4285F4" />
                  <stop offset="1" stopColor="#A142F4" />
                </linearGradient>
              </defs>
              <path d="M12 2C12 7.52 16.48 12 22 12C16.48 12 12 16.48 12 22C12 16.48 7.52 12 2 12C7.52 12 12 7.52 12 2Z" />
            </svg>
          </motion.div>
        </motion.button>
      )}
    </div>
  );
};
