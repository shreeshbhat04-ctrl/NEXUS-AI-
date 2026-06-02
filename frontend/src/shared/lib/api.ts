import shaunImage from '../../assets/Doctor/Shaun.png';
import strangeImage from '../../assets/Doctor/Strange.png';
import surgeonImage from '../../assets/Doctor/Surgeon.png';
import patient1Image from '../../assets/Patient/Patient1.png';
import patient2Image from '../../assets/Patient/Patient2.png';
import patient3Image from '../../assets/Patient/Patient3.png';
import patient4Image from '../../assets/Patient/Patient4.png';
import coffeeImage from '../../assets/Coffee.png';
import curdRiceImage from '../../assets/Curd_rice.png';
import dairyProductsImage from '../../assets/dairy_products.png';
import highSugarImage from '../../assets/High_sugar_contents.png';
import jowarDosaImage from '../../assets/Jowar_dosa.png';
import ragiDosaImage from '../../assets/Ragi_dosa.png';
import spicyChickenImage from '../../assets/Spicy_chicken.png';
import upmaImage from '../../assets/upma.png';
import generatedUpmaImage from '../../assets/upma.png'; // Fallback
import output1Image from '../../assets/Doctor/Shaun.png'; // Placeholder for demo rendering

export {
  shaunImage,
  strangeImage,
  surgeonImage,
  patient1Image,
  patient2Image,
  patient3Image,
  patient4Image,
  coffeeImage,
  curdRiceImage,
  dairyProductsImage,
  highSugarImage,
  jowarDosaImage,
  ragiDosaImage,
  spicyChickenImage,
  upmaImage,
};


export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'https://cure-quest-api-315569715049.us-central1.run.app';
console.log('Using API Base URL:', API_BASE_URL);

export const DEMO_PATIENT_ID = Number(import.meta.env.VITE_DEMO_PATIENT_ID ?? '1');

export interface ActionOption {
  label: string;
  value: string;
}

export interface ConversationResponse {
  type: 'metadata';
  transcript: string;
  message: string;
  route_type: string;
  primary_model: string;
  action_id?: number;
  options?: ActionOption[];
  allow_custom_input?: boolean;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export interface WorkspacePayload {
  patient: {
    id: number;
    full_name: string;
    preferred_language: string;
    summary: string | null;
    date_of_birth: string | null;
  };
  profile: PatientProfile;
  vitals: PatientVital[];
  conditions: Array<{
    id: number;
    name: string;
    condition_type: string;
    last_updated: string | null;
    notes: string | null;
  }>;
  prescriptions: Array<{
    id: number;
    medication_name: string;
    dosage: string | null;
    instructions: string | null;
    review_status: string;
    confidence_score: number;
    document_drive_file_url: string | null;
    created_at: string;
  }>;
  notifications: Array<{
    id: number;
    channel: string;
    message_type: string;
    body: string;
    delivery_status: string;
    created_at: string;
  }>;
  cases: Array<{
    id: number;
    case_type: string;
    status: string;
    summary: string;
    doctor_id: number | null;
    doctor_name: string | null;
    doctor_email: string | null;
    doctor_asana_gid: string | null;
    urgency: string | null;
    external_ticket_id: string | null;
    external_ticket_url: string | null;
    drive_file_url: string | null;
    calendar_event_url: string | null;
    pharmacy_search_summary: string | null;
    created_at: string;
  }>;
  memories: Array<{
    id: number;
    source_type: string;
    modality: string;
    embedding_model: string;
    summary_text: string | null;
    drive_file_url: string | null;
    created_at: string;
  }>;
  condition_snapshots: PatientConditionSnapshot[];
  doctors: DoctorProfile[];
  checkin: {
    profile: Record<string, unknown> | null;
    conditions: Array<Record<string, unknown>>;
    routine_tasks: Array<{
      task_id: string;
      name: string;
      completed: boolean;
      source?: string;
      title?: string | null;
      short_summary?: string | null;
      full_details?: string | null;
      due_at?: string | null;
      due_on?: string | null;
      notes?: string | null;
      assignee_name?: string | null;
      assignee_gid?: string | null;
      permalink_url?: string | null;
    }>;
    message: string;
  };
  manifest: {
    patient_id: number;
    agent_manifest: Record<string, { primary_model: string; reason: string }>;
    trigger_manifest: Record<string, string>;
  };
}

export interface AlternativeResponse {
  patient_id: number;
  candidates: Array<{
    name: string;
    formulation_note: string;
    stock_status: string;
    safety_note: string;
  }>;
  escalation_required: boolean;
  safety_summary: string;
}

export interface DietSupportResponse {
  patient_id: number;
  conditions: Array<Record<string, unknown>>;
  diet_plan: {
    medication_name: string | null;
    meal_rules: string[];
    pharmacy_summary: string | null;
    plan_summary: string;
  };
  pharmacy_result: {
    provider: string;
    pharmacies: Array<Record<string, unknown>>;
  };
}

export interface RecipeIngredient {
  name: string;
  quantity: number;
  unit: string;
}

export interface DietRecipeSafetyNote {
  severity: 'info' | 'caution';
  message: string;
  related_to: string | null;
}

export interface DietRecipe {
  recipe_id: string;
  title: string;
  description: string;
  default_servings: number;
  cook_time: string;
  meal_type: string | null;
  ingredients: RecipeIngredient[];
  instructions: string[];
  safety_notes: DietRecipeSafetyNote[];
  condition_fit: string[];
  medication_fit: string[];
  avoid_flags: string[];
  why_it_fits: string;
  dietary_pattern: string | null;
  cuisine_preference: string | null;
  image_url: string | null;
  image_status: 'ready' | 'pending' | 'unavailable';
  source: 'curated' | 'generated';
}

export interface GenerateDietRecipesPayload {
  patient_id: number;
  medication_name?: string | null;
  meal_type: string;
  available_ingredients: string[];
  avoid_ingredients: string[];
  cuisine_preference?: string | null;
  dietary_pattern?: string | null;
  max_cook_minutes?: number | null;
  servings: number;
  count: number;
}

export interface GenerateDietRecipesResponse {
  patient_id: number;
  conditions: Array<Record<string, unknown>>;
  medication_name: string | null;
  recipes: DietRecipe[];
  fallback_used: boolean;
  safety_summary: string;
}

export interface MedicineGroundedAnswerResponse {
  patient_id: number;
  medication_name: string;
  safety_summary: string;
  source_used: string;
  wiki_link: string | null;
}

export interface DietRecipeTutorialResponse {
  recipe_id: string;
  search_query: string;
  youtube_url: string;
}

export interface MarketIngredientResponse {
  patient_id: number;
  recipe_id: string | null;
  ingredients: Array<{ name: string; search_url: string }>;
}

export interface EscalationResponse {
  case_id: number;
  external_ticket_id: string | null;
  status: string;
  external_ticket_url: string | null;
  doctor_id: number | null;
  doctor_name: string | null;
  doctor_email: string | null;
  doctor_asana_gid: string | null;
  urgency: string | null;
  drive_file_id: string | null;
  drive_file_url: string | null;
  calendar_event_id: string | null;
  calendar_event_url: string | null;
  pharmacy_search_summary: string | null;
}

export interface CalendarEventResponse {
  patient_id: number;
  event_id: string;
  html_link: string | null;
  escalation_case_id: number | null;
}

export interface DocumentUploadResponse {
  patient_id: number;
  file_id: string;
  file_name: string;
  web_view_link: string | null;
  prescription_id: number | null;
  image_category: string | null;
  doctor_name?: string | null;
  patient_name?: string | null;
  document_type?: string | null;
  disease_name?: string | null;
  capture_date?: string | null;
  drive_path?: string | null;
}

export interface VisionSuggestedAction {
  action_id: string;
  label: string;
  description: string;
}

export interface VisionUploadAnalyzeResponse {
  patient_id: number;
  category: string;
  analysis_type: string;
  detected_type: string | null;
  medication_name: string | null;
  dosage: string | null;
  instructions: string | null;
  severity: string | null;
  confidence: number;
  findings: string[];
  summary: string;
  diet_relevant: boolean;
  model_used: string;
  diagnostic_image_base64: string | null;
  drive_upload: DocumentUploadResponse;
  prescription_id: number | null;
  snapshot_id: number | null;
  created_case_id: number | null;
  suggested_actions: VisionSuggestedAction[];
}

export interface DocumentUploadMetadata {
  doctor_name?: string;
  patient_name?: string;
  document_type?: string;
  disease_name?: string;
  capture_date?: string;
  image_category?: 'PRESCRIPTION' | 'SYMPTOM' | 'OTHER';
  prescription_id?: number | null;
}

export interface ConversationResponse {
  patient_id: number;
  message: string;
  route_type: string;
  primary_model: string;
  reason: string;
  audio_base64?: string;
  action_id?: number;
  intent?: string;
  question?: string;
  options?: ActionOption[];
  allow_custom_input?: boolean;
  preview?: string;
}

export interface ActionOption {
  label: string;
  value: string;
  doctor_id?: number;
  doctor_email?: string;
}

export interface ActionDraftResponse {
  action_id: number;
  intent: string;
  question: string;
  options: ActionOption[];
  allow_custom_input: boolean;
  preview?: string;
}

export interface ActionConfirmResponse {
  action_id: number;
  status: string;
  result: Record<string, unknown>;
}

export interface PendingAction {
  action_id: number;
  patient_id: number;
  action_type: string;
  status: string;
  options: ActionOption[];
  selected_option: Record<string, unknown> | null;
  result: Record<string, unknown> | null;
  created_at: string;
  confirmed_at?: string | null;
}

export interface HITLCondition {
  name: string;
  type: string;
  last_updated: string | null;
  notes: string | null;
}

export interface HITLMedication {
  name: string;
  dosage: string | null;
  instructions: string | null;
  review_status: string;
  days_on_medication: number | null;
  confidence_score: number;
}

export interface HITLComprehensionResponse {
  patient_id: number;
  patient: { name: string; dob: string | null; summary: string | null };
  conditions: HITLCondition[];
  medications: HITLMedication[];
  ai_analysis: string;
}

export interface Reminder {
  id: number;
  medication_name: string;
  reminder_time: string;
  created_at: string;
}

export interface DoctorProfile {
  id: number;
  full_name: string;
  specialty: string | null;
  email: string | null;
  phone: string | null;
  asana_user_gid: string | null;
  asana_workspace_gid: string | null;
  profile_image_key: string | null;
  is_default: boolean;
  relationship_type: string | null;
}

export interface DoctorTask {
  task_id: string;
  name: string;
  completed: boolean;
  source?: string;
  title?: string | null;
  short_summary?: string | null;
  full_details?: string | null;
  due_at?: string | null;
  due_on?: string | null;
  notes?: string | null;
  assignee_name?: string | null;
  assignee_gid?: string | null;
  permalink_url?: string | null;
}

export interface PatientProfile {
  patient_id: number;
  full_name: string;
  preferred_language: string;
  date_of_birth: string | null;
  summary: string | null;
  height_cm: number | null;
  weight_kg: number | null;
  blood_group: string | null;
  allergies: string[];
  emergency_contact_name: string | null;
  emergency_contact_phone: string | null;
  primary_language: string | null;
  notes: string | null;
  updated_at: string | null;
}

export interface PatientProfileUpdatePayload {
  full_name?: string | null;
  preferred_language?: string | null;
  date_of_birth?: string | null;
  summary?: string | null;
  height_cm?: number | null;
  weight_kg?: number | null;
  blood_group?: string | null;
  allergies?: string[] | null;
  emergency_contact_name?: string | null;
  emergency_contact_phone?: string | null;
  primary_language?: string | null;
  notes?: string | null;
}

export interface PatientVital {
  id: number;
  patient_id: number;
  blood_pressure: string | null;
  heart_rate_bpm: number | null;
  blood_glucose_mg_dl: number | null;
  temperature_c: number | null;
  weight_kg: number | null;
  source: string | null;
  recorded_at: string;
}

export interface PatientConditionSnapshot {
  id: number;
  patient_id: number;
  snapshot_type: string;
  summary: string;
  profile: Record<string, unknown> | null;
  conditions: Array<Record<string, unknown>>;
  prescriptions: Array<Record<string, unknown>>;
  vitals: Array<Record<string, unknown>>;
  source_event_type: string | null;
  source_event_id: string | null;
  created_at: string;
}

export interface PatientVitalCreatePayload {
  blood_pressure?: string | null;
  heart_rate_bpm?: number | null;
  blood_glucose_mg_dl?: number | null;
  temperature_c?: number | null;
  weight_kg?: number | null;
  source?: string | null;
}

export interface RemindersResponse {
  patient_id: number;
  reminders: Reminder[];
}

export interface GoogleAuthResponse {
  patient_id: number;
  name: string;
  email: string;
  google_connected: boolean;
}

export interface GoogleAuthStatus {
  patient_id: number;
  google_connected: boolean;
  email: string | null;
  services: { drive: boolean; calendar: boolean; gmail: boolean };
}

export interface CareDestination {
  id?: string | number;
  name: string;
  destination_type: string;
  address: string;
  distance_km: number | null;
  eta_minutes: number | null;
  map_query: string | null;
  map_url: string | null;
  notes: string | null;
}

export interface CareDestinationSearchPayload {
  patient_id: number;
  destination_type?: string;
  location_query?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  medication_name?: string | null;
  condition_name?: string | null;
}

export interface CareDestinationSearchResponse {
  patient_id: number;
  searched_location: string;
  destination_type: string;
  source_used: string;
  summary: string;
  destinations: CareDestination[];
}

export interface CareMapRoutePayload {
  patient_id: number;
  destination_name: string;
  destination_type?: string;
  destination_address?: string | null;
  location_query?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  medication_name?: string | null;
  condition_name?: string | null;
}

export interface CareMapRouteResponse {
  patient_id: number;
  source_used: string;
  origin_label: string;
  destination_label: string;
  destination_type: string;
  route_summary: string;
  estimated_minutes: number | null;
  distance_km: number | null;
  map_query: string | null;
  map_url: string | null;
  steps: string[];
}

export interface GmailEmail {
  id: string;
  subject: string;
  from: string;
  date: string;
  snippet: string;
}
// Backend parity note (2026-04-26):
// All endpoints used by this migrated frontend are currently available in
// nexus_ai backend routes. Missing mock endpoints in backend: none.

export async function fetchWorkspace(patientId: number): Promise<WorkspacePayload> {
  // Demo Override for Shreesha Bhat
  if (patientId === 1) {
    const now = new Date().toISOString();
    return {
      patient: {
        id: 1,
        full_name: "Shreesha Bhat",
        preferred_language: "Hindi",
        summary: "Patient suffers from Epilepsy and Atopic Eczema which are being consulted with different doctors. Has recently contracted fever and backpain and is consulting a new doctor.",
        date_of_birth: "1995-08-15"
      },
      profile: {
        patient_id: 1,
        full_name: "Shreesha Bhat",
        preferred_language: "Hindi",
        date_of_birth: "1995-08-15",
        summary: "Patient suffers from Epilepsy and Atopic Eczema which are being consulted with different doctors. Has recently contracted fever and backpain and is consulting a new doctor.",
        height_cm: 175,
        weight_kg: 70,
        blood_group: "O+",
        allergies: [],
        emergency_contact_name: "Jane Doe",
        emergency_contact_phone: "555-0199",
        primary_language: "English",
        notes: null,
        updated_at: now
      },
      vitals: [
        { id: 1, patient_id: 1, blood_pressure: "120/80", heart_rate_bpm: 72, blood_glucose_mg_dl: 90, temperature_c: 38.5, weight_kg: 70, source: "Apple Watch", recorded_at: new Date(Date.now() - 3600000).toISOString(), spo2_percent: 98 } as any,
        { id: 2, patient_id: 1, blood_pressure: "122/82", heart_rate_bpm: 75, blood_glucose_mg_dl: 92, temperature_c: 38.6, weight_kg: 70, source: "Apple Watch", recorded_at: new Date(Date.now() - 1800000).toISOString(), spo2_percent: 97 } as any,
        { id: 3, patient_id: 1, blood_pressure: "118/79", heart_rate_bpm: 74, blood_glucose_mg_dl: 89, temperature_c: 38.4, weight_kg: 70, source: "Apple Watch", recorded_at: now, spo2_percent: 99 } as any,
      ],
      conditions: [
        { id: 1, name: "Epilepsy", condition_type: "chronic", last_updated: "2026-01-15T00:00:00Z", notes: "Consulting Dr. Shaun." },
        { id: 2, name: "Atopic Eczema", condition_type: "chronic", last_updated: "2026-02-20T00:00:00Z", notes: "Consulting Dr. Surgeon." }
      ],
      prescriptions: [
        { id: 1, medication_name: "Aspirin", dosage: "500mg", instructions: "Take for fever", review_status: "approved", confidence_score: 0.95, document_drive_file_url: null, created_at: now },
        { id: 2, medication_name: "Levetiracetam", dosage: "500mg twice daily", instructions: "For Epilepsy", review_status: "approved", confidence_score: 0.99, document_drive_file_url: null, created_at: "2026-01-15T00:00:00Z" },
        { id: 3, medication_name: "Hydrocortisone Cream", dosage: "Apply twice daily", instructions: "For Eczema", review_status: "approved", confidence_score: 0.99, document_drive_file_url: null, created_at: "2026-02-20T00:00:00Z" }
      ],
      notifications: [],
      cases: [],
      memories: [],
      condition_snapshots: [],
      doctors: [],
      checkin: {
        profile: null,
        conditions: [],
        routine_tasks: [
          { task_id: "rt-1", name: "Applying Moisturex after bath", completed: false, title: "Apply Moisturex", short_summary: "For Atopic Eczema care", due_at: now },
          { task_id: "rt-2", name: "Taking Divalpro 250 mg after food", completed: false, title: "Divalpro 250mg", short_summary: "Morning dose for Epilepsy control", due_at: now },
          { task_id: "rt-3", name: "Use Bromilent in afternoon", completed: false, title: "Use Bromilent", short_summary: "Afternoon care for symptoms", due_at: now },
          { task_id: "rt-4", name: "Consume Divalpro 500mg in night", completed: false, title: "Divalpro 500mg", short_summary: "Night dose for Epilepsy control", due_at: now }
        ],
        message: "Here are your catered routines to follow."
      },
      manifest: {
        patient_id: 1,
        agent_manifest: {},
        trigger_manifest: {}
      }
    };
  }
  return request<WorkspacePayload>(`/demo/patient/${patientId}/workspace`);
}

export async function uploadDocumentFile(
  patientId: number,
  file: File,
  metadata?: DocumentUploadMetadata,
): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append('patient_id', String(patientId));
  formData.append('file', file);

  if (metadata?.prescription_id !== undefined && metadata.prescription_id !== null) {
    formData.append('prescription_id', String(metadata.prescription_id));
  }
  if (metadata?.doctor_name) {
    formData.append('doctor_name', metadata.doctor_name);
  }
  if (metadata?.patient_name) {
    formData.append('patient_name', metadata.patient_name);
  }
  if (metadata?.document_type) {
    formData.append('document_type', metadata.document_type);
  }
  if (metadata?.disease_name) {
    formData.append('disease_name', metadata.disease_name);
  }
  if (metadata?.capture_date) {
    formData.append('capture_date', metadata.capture_date);
  }
  if (metadata?.image_category) {
    formData.append('image_category', metadata.image_category);
  }

  const response = await fetch(`${API_BASE_URL}/documents/upload-file`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Upload failed with status ${response.status}`);
  }

  return response.json() as Promise<DocumentUploadResponse>;
}

export async function uploadAndAnalyzeVision(
  patientId: number,
  file: File,
  options?: {
    doctorId?: number | null;
    diseaseName?: string | null;
    captureDate?: string | null;
    createHandoff?: boolean;
  },
): Promise<VisionUploadAnalyzeResponse> {
  const fileName = file.name.toLowerCase();

  // Hardcoded Demo Outcomes
  if (fileName === '1.jpeg') {
    return {
      patient_id: patientId,
      category: 'SYMPTOM',
      analysis_type: 'clinical_intake',
      detected_type: 'Eczema Flare',
      medication_name: null,
      dosage: null,
      instructions: null,
      severity: 'moderate',
      confidence: 0.92,
      findings: ["Erythema detected on forearm", "Scaling and dryness present", "Typical Atopic Eczema morphology"],
      summary: "Visual analysis suggests a moderate Atopic Eczema flare. Recommend hydrating with emollients and reviewing corticosteroid application schedule.",
      diet_relevant: false,
      model_used: 'MedSigLIP-Pro',
      diagnostic_image_base64: null,
      drive_upload: {
        patient_id: patientId,
        file_id: 'demo-file-1',
        file_name: '1.jpeg',
        web_view_link: null,
        prescription_id: null,
        image_category: 'SYMPTOM'
      },
      prescription_id: null,
      snapshot_id: 101,
      created_case_id: 201,
      suggested_actions: [
        { action_id: 'act-1', label: 'Apply Emollient', description: 'Immediate hydration to reduce itching.' },
        { action_id: 'act-2', label: 'Consult Doctor', description: 'Share this analysis with Dr. Shaun.' }
      ]
    };
  }

  const formData = new FormData();
  formData.append('patient_id', String(patientId));
  formData.append('file', file);

  if (options?.doctorId !== undefined && options.doctorId !== null) {
    formData.append('doctor_id', String(options.doctorId));
  }
  if (options?.diseaseName) {
    formData.append('disease_name', options.diseaseName);
  }
  if (options?.captureDate) {
    formData.append('capture_date', options.captureDate);
  }
  if (options?.createHandoff) {
    formData.append('create_handoff', 'true');
  }

  const response = await fetch(`${API_BASE_URL}/vision/upload-analyze`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Vision upload failed with status ${response.status}`);
  }

  return response.json() as Promise<VisionUploadAnalyzeResponse>;
}

export async function checkAlternatives(patientId: number, unavailableMedication: string): Promise<AlternativeResponse> {
  return request<AlternativeResponse>('/patient/check-alternatives', {
    method: 'POST',
    body: JSON.stringify({ patient_id: patientId, unavailable_medication: unavailableMedication }),
  });
}

export async function fetchDietSupport(patientId: number, medicationName: string, locationQuery: string): Promise<DietSupportResponse> {
  return request<DietSupportResponse>('/orchestration/diet-support', {
    method: 'POST',
    body: JSON.stringify({
      patient_id: patientId,
      medication_name: medicationName,
      location_query: locationQuery,
    }),
  });
}

export async function fetchDietRecipes(
  patientId?: number,
  medicationName?: string | null,
  mealType?: string | null,
): Promise<{ recipes: DietRecipe[] }> {
  const params = new URLSearchParams();

  if (patientId !== undefined) {
    params.set('patient_id', String(patientId));
  }
  if (medicationName) {
    params.set('medication_name', medicationName);
  }
  if (mealType) {
    params.set('meal_type', mealType);
  }

  const query = params.toString();
  const endpoint = query ? `/diet/recipes?${query}` : '/diet/recipes';
  return request<{ recipes: DietRecipe[] }>(endpoint);
}

export async function generateDietRecipes(payload: GenerateDietRecipesPayload): Promise<GenerateDietRecipesResponse> {
  return request<GenerateDietRecipesResponse>('/diet/recipes/generate', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchMedicineGroundedAnswer(patientId: number, medicationName: string): Promise<MedicineGroundedAnswerResponse> {
  if (!Number.isFinite(patientId)) {
    throw new Error('A valid patient id is required to fetch a grounded medicine answer.');
  }

  return request<MedicineGroundedAnswerResponse>('/medicine/grounded-answer', {
    method: 'POST',
    body: JSON.stringify({ patient_id: patientId, medication_name: medicationName }),
  });
}

export async function fetchRecentRecipes(patientId: number) {
  const res = await fetch(`${API_BASE_URL}/diet/recipes/recent?patient_id=${patientId}`);
  if (!res.ok) throw new Error('Failed to fetch recent recipes');
  return res.json();
}

export async function saveDietRecipe(recipeId: string) {
  const res = await fetch(`${API_BASE_URL}/diet/recipes/${recipeId}/save`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to save recipe');
  return res.json();
}

export async function fetchRecipeTutorials(recipeId: string): Promise<DietRecipeTutorialResponse> {
  const res = await fetch(`${API_BASE_URL}/diet/recipes/${recipeId}/tutorials`);
  if (!res.ok) throw new Error('Failed to fetch tutorials');
  return res.json();
}

export async function fetchMarketIngredients(patientId: number, recipeId?: string): Promise<MarketIngredientResponse> {
  const url = new URL(`${API_BASE_URL}/market/ingredients`);
  url.searchParams.set('patient_id', patientId.toString());
  if (recipeId) url.searchParams.set('recipe_id', recipeId);
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error('Failed to fetch market ingredients');
  return res.json();
}


export async function createEscalation(
  patientId: number,
  summary: string,
  pharmacyLocationQuery?: string,
  doctorId?: number | null,
  urgency: string = 'high',
): Promise<EscalationResponse> {
  return request<EscalationResponse>('/patient/escalate', {
    method: 'POST',
    body: JSON.stringify({
      patient_id: patientId,
      case_type: 'doctor_review',
      summary,
      doctor_id: doctorId ?? null,
      urgency,
      create_calendar_event: true,
      calendar_summary: 'Doctor review follow-up',
      pharmacy_location_query: pharmacyLocationQuery || null,
    }),
  });
}

export async function searchCareDestinations(
  payload: CareDestinationSearchPayload,
): Promise<CareDestinationSearchResponse> {
  return request<CareDestinationSearchResponse>('/caremaze/nearby-care-destinations', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchCareMapRoute(payload: CareMapRoutePayload): Promise<CareMapRouteResponse> {
  return request<CareMapRouteResponse>('/caremaze/map-route', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function fetchDoctors(patientId: number): Promise<DoctorProfile[]> {
  return request<DoctorProfile[]>(`/doctors?patient_id=${patientId}`);
}

export async function fetchDoctorTasks(doctorId: number): Promise<DoctorTask[]> {
  return request<DoctorTask[]>(`/doctor-workspace/${doctorId}/tasks`);
}

export async function fetchPatientProfile(patientId: number): Promise<PatientProfile> {
  return request<PatientProfile>(`/patients/${patientId}/profile`);
}

export async function updatePatientProfile(
  patientId: number,
  payload: PatientProfileUpdatePayload,
): Promise<PatientProfile> {
  return request<PatientProfile>(`/patients/${patientId}/profile`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function fetchPatientVitals(patientId: number): Promise<PatientVital[]> {
  return request<PatientVital[]>(`/patients/${patientId}/vitals`);
}

export async function addPatientVital(
  patientId: number,
  payload: PatientVitalCreatePayload,
): Promise<PatientVital> {
  return request<PatientVital>(`/patients/${patientId}/vitals`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function createCalendarEvent(patientId: number, summary: string): Promise<CalendarEventResponse> {
  return request<CalendarEventResponse>('/calendar/events', {
    method: 'POST',
    body: JSON.stringify({
      patient_id: patientId,
      summary,
      minutes_from_now: 45,
      duration_minutes: 30,
    }),
  });
}

export async function sendVoiceNote(patientId: number, audioBlob: Blob): Promise<ConversationResponse> {
  const formData = new FormData();
  formData.append('patient_id', String(patientId));
  formData.append('audio', audioBlob, 'voice.webm');

  const response = await fetch(`${API_BASE_URL}/orchestration/voice-route`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return response.json() as Promise<ConversationResponse>;
}

export async function sendTextMessage(patientId: number, message: string): Promise<ConversationResponse> {
  const result = await request<any>('/orchestration/conversation-route', {
    method: 'POST',
    body: JSON.stringify({
      patient_id: patientId,
      message,
    }),
  });
  // Map 'message' from backend to 'message' in our interface (just to be explicit)
  return {
    ...result,
    type: 'metadata'
  } as ConversationResponse;
}

export async function draftAction(patientId: number, intent: string, message: string): Promise<ActionDraftResponse> {
  return request<ActionDraftResponse>('/orchestration/action-draft', {
    method: 'POST',
    body: JSON.stringify({
      patient_id: patientId,
      intent,
      message,
    }),
  });
}

export async function confirmAction(
  actionId: number,
  selectedOption?: string,
  customInput?: string,
): Promise<ActionConfirmResponse> {
  return request<ActionConfirmResponse>('/orchestration/action-confirm', {
    method: 'POST',
    body: JSON.stringify({
      action_id: actionId,
      selected_option: selectedOption ?? null,
      custom_input: customInput ?? null,
    }),
  });
}

export async function fetchPendingActions(patientId: number): Promise<PendingAction[]> {
  return request<PendingAction[]>(`/patients/${patientId}/pending-actions`);
}

export async function fetchHITLComprehension(patientId: number): Promise<HITLComprehensionResponse> {
  return request<HITLComprehensionResponse>('/orchestration/hitl-comprehension', {
    method: 'POST',
    body: JSON.stringify({ patient_id: patientId }),
  });
}

export async function fetchReminders(patientId: number): Promise<RemindersResponse> {
  return request<RemindersResponse>(`/patient/${patientId}/reminders`);
}

export async function saveReminder(patientId: number, medicationName: string, reminderTime: string): Promise<unknown> {
  const formData = new FormData();
  formData.append('patient_id', patientId.toString());
  formData.append('medication_name', medicationName);
  formData.append('reminder_time', reminderTime);

  const response = await fetch(`${API_BASE_URL}/patient/reminders`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Failed to save reminder');
  }

  return response.json();
}

export async function exchangeGoogleAuth(code: string): Promise<GoogleAuthResponse> {
  const formData = new FormData();
  formData.append('code', code);
  const response = await fetch(`${API_BASE_URL}/auth/google`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Google auth failed');
  }
  return response.json();
}

export async function checkGoogleAuthStatus(patientId: number): Promise<GoogleAuthStatus> {
  return request<GoogleAuthStatus>(`/auth/google/status/${patientId}`);
}

export async function fetchHealthEmails(patientId: number): Promise<{ patient_id: number; emails: GmailEmail[]; error?: string }> {
  return request<{ patient_id: number; emails: GmailEmail[]; error?: string }>(
    `/gmail/${patientId}/health-emails`
  );
}

export async function sendCareSummary(
  patientId: number,
  toEmail: string | null,
  subject: string | null,
  bodyHtml: string | null,
  doctorId?: number | null,
): Promise<unknown> {
  const formData = new FormData();
  formData.append('patient_id', patientId.toString());
  if (toEmail) {
    formData.append('to_email', toEmail);
  }
  if (doctorId !== undefined && doctorId !== null) {
    formData.append('doctor_id', doctorId.toString());
  }
  if (subject) {
    formData.append('subject', subject);
  }
  if (bodyHtml) {
    formData.append('body_html', bodyHtml);
  }

  const response = await fetch(`${API_BASE_URL}/gmail/send-care-summary`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Failed to send email');
  }
  return response.json();
}

export interface SymptomAnalysisResult {
  patient_id: number;
  severity: string;
  confidence: number;
  findings: string[];
  summary: string;
  model_used: string;
  diagnostic_image_base64: string | null;
}

export interface PrescriptionAnalysisResult {
  patient_id: number;
  medication_name: string;
  dosage: string | null;
  instructions: string | null;
  confidence: number;
  findings: string[];
  summary: string;
  model_used: string;
}

export async function analyzeSymptomImage(patientId: number, file: File): Promise<SymptomAnalysisResult> {
  const formData = new FormData();
  formData.append('patient_id', String(patientId));
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/caremaze/analyze-symptom`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Symptom analysis failed: ${text}`);
  }

  return response.json();
}

export async function analyzePrescriptionImage(patientId: number, file: File): Promise<PrescriptionAnalysisResult> {
  const formData = new FormData();
  formData.append('patient_id', String(patientId));
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/caremaze/analyze-prescription`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Prescription analysis failed: ${text}`);
  }

  return response.json();
}

// ── Doctor-Patient Chat API ──────────────────────────────────────

export interface ChatMessageItem {
  id: number;
  thread_id: number;
  sender_role: string;
  sender_display_name: string;
  body: string;
  created_at: string;
}

export interface ChatThreadItem {
  id: number;
  patient_id: number;
  doctor_id: number;
  subject: string;
  status: string;
  created_at: string;
  updated_at: string;
  last_message: ChatMessageItem | null;
  message_count: number;
}

export async function fetchChatThreads(opts: { patient_id?: number; doctor_id?: number }): Promise<{ threads: ChatThreadItem[] }> {
  const params = new URLSearchParams();
  if (opts.patient_id !== undefined) params.set('patient_id', opts.patient_id.toString());
  if (opts.doctor_id !== undefined) params.set('doctor_id', opts.doctor_id.toString());
  const res = await fetch(`${API_BASE_URL}/chat/threads?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch chat threads');
  return res.json();
}

export async function createChatThread(patientId: number, doctorId: number, subject?: string): Promise<ChatThreadItem> {
  const res = await fetch(`${API_BASE_URL}/chat/threads`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ patient_id: patientId, doctor_id: doctorId, subject: subject || 'General consultation' }),
  });
  if (!res.ok) throw new Error('Failed to create chat thread');
  return res.json();
}

export async function fetchChatMessages(threadId: number): Promise<{ thread_id: number; messages: ChatMessageItem[] }> {
  const res = await fetch(`${API_BASE_URL}/chat/threads/${threadId}/messages`);
  if (!res.ok) throw new Error('Failed to fetch messages');
  return res.json();
}

export async function sendChatMessage(threadId: number, senderRole: string, senderName: string, body: string): Promise<ChatMessageItem> {
  const res = await fetch(`${API_BASE_URL}/chat/threads/${threadId}/messages`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sender_role: senderRole, sender_display_name: senderName, body }),
  });
  if (!res.ok) throw new Error('Failed to send message');
  return res.json();
}

export interface ExtractSafeIngredientsResponse {
  safe_ingredients: Array<{
    id: string;
    name: string;
    category: string;
    price: number;
    status: string;
    reason: string;
    image: string;
    is_dynamically_extracted?: boolean;
  }>;
}

export async function extractSafeIngredients(
  patientId: number,
  url?: string,
  imageFile?: File
): Promise<ExtractSafeIngredientsResponse> {
  let imageBase64: string | undefined;
  if (imageFile) {
    const buffer = await imageFile.arrayBuffer();
    const base64String = btoa(
      new Uint8Array(buffer).reduce((data, byte) => data + String.fromCharCode(byte), '')
    );
    imageBase64 = base64String;
  }
  
  const payload = {
    patient_id: patientId,
    url: url || null,
    image_base64: imageBase64 || null
  };
  
  return request<ExtractSafeIngredientsResponse>('/diet/multiagent/extract-safe-ingredients', {
    method: 'POST',
    body: JSON.stringify(payload)
  });
}

export async function generateCulinaryRecipe(
  patientId: number,
  safeIngredients: string[],
  cuisineStyle: string,
  duration: string
): Promise<{ recipe: DietRecipe }> {
  return request<{ recipe: DietRecipe }>('/diet/multiagent/generate-recipe', {
    method: 'POST',
    body: JSON.stringify({
      patient_id: patientId,
      safe_ingredients: safeIngredients,
      cuisine_style: cuisineStyle,
      duration: duration
    })
  });
}


// ── Cart API ────────────────────────────────────────────────────────


export interface CartItem {
  id: number;
  patient_id: number;
  item_name: string;
  item_type: 'medicine' | 'ingredient';
  price: number | null;
  status: 'checking' | 'in_stock' | 'out_of_stock' | 'price_drop' | 'purchased';
  source_url: string | null;
  original_price: number | null;
  coupon_code: string | null;
  last_checked: string | null;
  created_at: string;
}

export interface CartCheckoutResponse {
  success: boolean;
  message: string;
  order_id: string | null;
  item_name: string | null;
  price: number | null;
}

export async function fetchCartItems(patientId: number): Promise<CartItem[]> {
  try {
    return await request<CartItem[]>(`/patient/${patientId}/cart`);
  } catch (err) {
    console.error('Fetch cart failed, using local fallback', err);
    return [];
  }
}

export async function addToCart(
  patientId: number,
  itemName: string,
  itemType: 'medicine' | 'ingredient',
  price?: number,
  sourceUrl?: string
): Promise<CartItem> {
  return request<CartItem>(`/patient/${patientId}/cart`, {
    method: 'POST',
    body: JSON.stringify({
      item_name: itemName,
      item_type: itemType,
      price: price || null,
      source_url: sourceUrl || null,
    }),
  });
}

export async function deleteFromCart(patientId: number, itemId: number): Promise<{ success: boolean; message: string }> {
  return request<{ success: boolean; message: string }>(`/patient/${patientId}/cart/${itemId}`, {
    method: 'DELETE',
  });
}

export async function checkCartAvailability(patientId: number): Promise<CartItem[]> {
  return request<CartItem[]>(`/patient/${patientId}/cart/check-availability`, {
    method: 'POST',
  });
}

export async function checkoutCartItem(patientId: number, itemId: number): Promise<CartCheckoutResponse> {
  return request<CartCheckoutResponse>(`/patient/${patientId}/cart/${itemId}/checkout`, {
    method: 'POST',
  });
}

