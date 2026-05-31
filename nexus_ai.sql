--
-- PostgreSQL database dump
--

\restrict lOyUPDJC5GznVCScDKTzsUXY6yy5Q3gyhxxTnq1Q5ciEbVQlZR6rU9dIMtLX4KO

-- Dumped from database version 18.0
-- Dumped by pg_dump version 18.0

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: chat_messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chat_messages (
    id integer NOT NULL,
    thread_id integer NOT NULL,
    sender_role character varying(40) NOT NULL,
    sender_display_name character varying(255) NOT NULL,
    body text NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.chat_messages OWNER TO postgres;

--
-- Name: chat_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.chat_messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.chat_messages_id_seq OWNER TO postgres;

--
-- Name: chat_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.chat_messages_id_seq OWNED BY public.chat_messages.id;


--
-- Name: chat_threads; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chat_threads (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    doctor_id integer NOT NULL,
    subject character varying(500) NOT NULL,
    status character varying(40) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.chat_threads OWNER TO postgres;

--
-- Name: chat_threads_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.chat_threads_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.chat_threads_id_seq OWNER TO postgres;

--
-- Name: chat_threads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.chat_threads_id_seq OWNED BY public.chat_threads.id;


--
-- Name: chronic_conditions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chronic_conditions (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    name character varying(255) NOT NULL,
    condition_type character varying(32) NOT NULL,
    last_updated date,
    notes text
);


ALTER TABLE public.chronic_conditions OWNER TO postgres;

--
-- Name: chronic_conditions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.chronic_conditions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.chronic_conditions_id_seq OWNER TO postgres;

--
-- Name: chronic_conditions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.chronic_conditions_id_seq OWNED BY public.chronic_conditions.id;


--
-- Name: doctors; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.doctors (
    id integer NOT NULL,
    full_name character varying(255) NOT NULL,
    specialty character varying(255),
    email character varying(255),
    phone character varying(50),
    asana_user_gid character varying(255),
    asana_workspace_gid character varying(255),
    profile_image_key character varying(100),
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.doctors OWNER TO postgres;

--
-- Name: doctors_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.doctors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.doctors_id_seq OWNER TO postgres;

--
-- Name: doctors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.doctors_id_seq OWNED BY public.doctors.id;


--
-- Name: escalation_cases; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.escalation_cases (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    case_type character varying(50) NOT NULL,
    status character varying(50) NOT NULL,
    summary text NOT NULL,
    doctor_id integer,
    doctor_name character varying(255),
    doctor_email character varying(255),
    doctor_asana_gid character varying(255),
    urgency character varying(50),
    external_ticket_id character varying(255),
    external_ticket_url text,
    drive_file_id character varying(255),
    drive_file_url text,
    calendar_event_id character varying(255),
    calendar_event_url text,
    pharmacy_search_summary text,
    drive_path text,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.escalation_cases OWNER TO postgres;

--
-- Name: escalation_cases_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.escalation_cases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.escalation_cases_id_seq OWNER TO postgres;

--
-- Name: escalation_cases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.escalation_cases_id_seq OWNED BY public.escalation_cases.id;


--
-- Name: medical_memories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.medical_memories (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    source_type character varying(50) NOT NULL,
    source_reference character varying(255),
    modality character varying(32) NOT NULL,
    embedding_model character varying(128) NOT NULL,
    embedding_vector text NOT NULL,
    summary_text text,
    drive_file_id character varying(255),
    drive_file_url text,
    drive_path text,
    metadata_json text,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.medical_memories OWNER TO postgres;

--
-- Name: medical_memories_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.medical_memories_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.medical_memories_id_seq OWNER TO postgres;

--
-- Name: medical_memories_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.medical_memories_id_seq OWNED BY public.medical_memories.id;


--
-- Name: medication_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.medication_events (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    event_type character varying(50) NOT NULL,
    medication_name character varying(255),
    details text,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.medication_events OWNER TO postgres;

--
-- Name: medication_events_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.medication_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.medication_events_id_seq OWNER TO postgres;

--
-- Name: medication_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.medication_events_id_seq OWNED BY public.medication_events.id;


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notifications (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    channel character varying(50) NOT NULL,
    message_type character varying(50) NOT NULL,
    body text NOT NULL,
    delivery_status character varying(50) NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.notifications OWNER TO postgres;

--
-- Name: notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notifications_id_seq OWNER TO postgres;

--
-- Name: notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notifications_id_seq OWNED BY public.notifications.id;


--
-- Name: patient_condition_snapshots; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.patient_condition_snapshots (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    snapshot_type character varying(80) NOT NULL,
    summary text NOT NULL,
    profile_json text,
    conditions_json text,
    prescriptions_json text,
    vitals_json text,
    source_event_type character varying(80),
    source_event_id character varying(80),
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.patient_condition_snapshots OWNER TO postgres;

--
-- Name: patient_condition_snapshots_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.patient_condition_snapshots_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.patient_condition_snapshots_id_seq OWNER TO postgres;

--
-- Name: patient_condition_snapshots_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.patient_condition_snapshots_id_seq OWNED BY public.patient_condition_snapshots.id;


--
-- Name: patient_doctor_map; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.patient_doctor_map (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    doctor_id integer NOT NULL,
    relationship_type character varying(50) NOT NULL,
    is_default boolean NOT NULL,
    notes text,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.patient_doctor_map OWNER TO postgres;

--
-- Name: patient_doctor_map_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.patient_doctor_map_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.patient_doctor_map_id_seq OWNER TO postgres;

--
-- Name: patient_doctor_map_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.patient_doctor_map_id_seq OWNED BY public.patient_doctor_map.id;


--
-- Name: patient_profile_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.patient_profile_details (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    height_cm double precision,
    weight_kg double precision,
    blood_group character varying(20),
    allergies_json text,
    emergency_contact_name character varying(255),
    emergency_contact_phone character varying(50),
    primary_language character varying(50),
    notes text,
    updated_at timestamp with time zone NOT NULL
);


ALTER TABLE public.patient_profile_details OWNER TO postgres;

--
-- Name: patient_profile_details_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.patient_profile_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.patient_profile_details_id_seq OWNER TO postgres;

--
-- Name: patient_profile_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.patient_profile_details_id_seq OWNED BY public.patient_profile_details.id;


--
-- Name: patient_vitals; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.patient_vitals (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    blood_pressure character varying(50),
    heart_rate_bpm integer,
    blood_glucose_mg_dl double precision,
    temperature_c double precision,
    weight_kg double precision,
    source character varying(80),
    recorded_at timestamp with time zone NOT NULL
);


ALTER TABLE public.patient_vitals OWNER TO postgres;

--
-- Name: patient_vitals_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.patient_vitals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.patient_vitals_id_seq OWNER TO postgres;

--
-- Name: patient_vitals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.patient_vitals_id_seq OWNED BY public.patient_vitals.id;


--
-- Name: patients; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.patients (
    id integer NOT NULL,
    full_name character varying(255) NOT NULL,
    preferred_language character varying(50) NOT NULL,
    date_of_birth date,
    summary text,
    google_email character varying(255),
    google_access_token text,
    google_refresh_token text,
    google_token_expiry timestamp with time zone,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.patients OWNER TO postgres;

--
-- Name: patients_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.patients_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.patients_id_seq OWNER TO postgres;

--
-- Name: patients_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.patients_id_seq OWNED BY public.patients.id;


--
-- Name: pending_actions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pending_actions (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    action_type character varying(80) NOT NULL,
    status character varying(40) NOT NULL,
    draft_payload_json text,
    options_json text,
    selected_option_json text,
    result_json text,
    created_at timestamp with time zone NOT NULL,
    confirmed_at timestamp with time zone
);


ALTER TABLE public.pending_actions OWNER TO postgres;

--
-- Name: pending_actions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pending_actions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pending_actions_id_seq OWNER TO postgres;

--
-- Name: pending_actions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pending_actions_id_seq OWNED BY public.pending_actions.id;


--
-- Name: prescriptions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.prescriptions (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    source_reference character varying(255),
    raw_text text,
    medication_name character varying(255) NOT NULL,
    dosage character varying(100),
    instructions text,
    confidence_score double precision NOT NULL,
    review_status character varying(50) NOT NULL,
    document_drive_file_id character varying(255),
    document_drive_file_url text,
    drive_path text,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.prescriptions OWNER TO postgres;

--
-- Name: prescriptions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.prescriptions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.prescriptions_id_seq OWNER TO postgres;

--
-- Name: prescriptions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.prescriptions_id_seq OWNED BY public.prescriptions.id;


--
-- Name: saved_diet_recipes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.saved_diet_recipes (
    id integer NOT NULL,
    patient_id integer NOT NULL,
    recipe_id character varying(200) NOT NULL,
    created_at timestamp with time zone NOT NULL
);


ALTER TABLE public.saved_diet_recipes OWNER TO postgres;

--
-- Name: saved_diet_recipes_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.saved_diet_recipes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.saved_diet_recipes_id_seq OWNER TO postgres;

--
-- Name: saved_diet_recipes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.saved_diet_recipes_id_seq OWNED BY public.saved_diet_recipes.id;


--
-- Name: chat_messages id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_messages ALTER COLUMN id SET DEFAULT nextval('public.chat_messages_id_seq'::regclass);


--
-- Name: chat_threads id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_threads ALTER COLUMN id SET DEFAULT nextval('public.chat_threads_id_seq'::regclass);


--
-- Name: chronic_conditions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chronic_conditions ALTER COLUMN id SET DEFAULT nextval('public.chronic_conditions_id_seq'::regclass);


--
-- Name: doctors id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.doctors ALTER COLUMN id SET DEFAULT nextval('public.doctors_id_seq'::regclass);


--
-- Name: escalation_cases id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.escalation_cases ALTER COLUMN id SET DEFAULT nextval('public.escalation_cases_id_seq'::regclass);


--
-- Name: medical_memories id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_memories ALTER COLUMN id SET DEFAULT nextval('public.medical_memories_id_seq'::regclass);


--
-- Name: medication_events id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medication_events ALTER COLUMN id SET DEFAULT nextval('public.medication_events_id_seq'::regclass);


--
-- Name: notifications id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications ALTER COLUMN id SET DEFAULT nextval('public.notifications_id_seq'::regclass);


--
-- Name: patient_condition_snapshots id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_condition_snapshots ALTER COLUMN id SET DEFAULT nextval('public.patient_condition_snapshots_id_seq'::regclass);


--
-- Name: patient_doctor_map id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_doctor_map ALTER COLUMN id SET DEFAULT nextval('public.patient_doctor_map_id_seq'::regclass);


--
-- Name: patient_profile_details id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_profile_details ALTER COLUMN id SET DEFAULT nextval('public.patient_profile_details_id_seq'::regclass);


--
-- Name: patient_vitals id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_vitals ALTER COLUMN id SET DEFAULT nextval('public.patient_vitals_id_seq'::regclass);


--
-- Name: patients id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patients ALTER COLUMN id SET DEFAULT nextval('public.patients_id_seq'::regclass);


--
-- Name: pending_actions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pending_actions ALTER COLUMN id SET DEFAULT nextval('public.pending_actions_id_seq'::regclass);


--
-- Name: prescriptions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prescriptions ALTER COLUMN id SET DEFAULT nextval('public.prescriptions_id_seq'::regclass);


--
-- Name: saved_diet_recipes id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.saved_diet_recipes ALTER COLUMN id SET DEFAULT nextval('public.saved_diet_recipes_id_seq'::regclass);


--
-- Data for Name: chat_messages; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.chat_messages (id, thread_id, sender_role, sender_display_name, body, created_at) FROM stdin;
1	4	patient	Shreesha	I was prescribed aspirin by Dr. Shaun. I’m already taking divalproex for epilepsy. Is aspirin safe, or should we change it?\n\n(Hindi): डॉक्टर शॉन ने मुझे एस्पिरिन लिखी है। मैं मिर्गी के लिए डिवालप्रोएक्स ले रहा हूँ। क्या एस्पिरिन सुरक्षित है या बदलनी चाहिए?	2026-04-30 17:36:13.624897+05:30
2	5	patient	Shreesha Bhat	Hi Dr. undefined, I've uploaded a Dermatology Prescription for review. Analysis summary: Full prescription extraction for Sreesha H.B. Three medications added to your profile records.	2026-04-30 17:38:05.876902+05:30
3	6	patient	Shreesha Bhat	Hi Dr. Doctor, I've uploaded a SYMPTOM via Care Maze. Summary: Visual analysis suggests a moderate Atopic Eczema flare. Recommend hydrating with emollients and reviewing corticosteroid application schedule.	2026-04-30 19:00:18.621186+05:30
\.


--
-- Data for Name: chat_threads; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.chat_threads (id, patient_id, doctor_id, subject, status, created_at, updated_at) FROM stdin;
4	1	1	Aspirin prescribed — safe with epilepsy meds?	open	2026-04-30 17:36:13.560073+05:30	2026-04-30 17:36:13.609731+05:30
5	1	1	Inquiry: Dermatology Prescription	open	2026-04-30 17:38:05.818606+05:30	2026-04-30 17:38:05.874846+05:30
6	1	1	Inquiry: SYMPTOM	open	2026-04-30 19:00:18.306256+05:30	2026-04-30 19:00:18.587482+05:30
\.


--
-- Data for Name: chronic_conditions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.chronic_conditions (id, patient_id, name, condition_type, last_updated, notes) FROM stdin;
1	1	Eczema	chronic	\N	Severe skin irritation
2	1	Epilepsy	chronic	\N	Occasional seizures
\.


--
-- Data for Name: doctors; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.doctors (id, full_name, specialty, email, phone, asana_user_gid, asana_workspace_gid, profile_image_key, created_at) FROM stdin;
1	Dr. Shreesha	Gynaecologist	sreeshhb@gmail.com	+91 9876543210	1214276322986923	1213916290149152	surgeon	2026-04-30 17:35:39.543879+05:30
2	Dr. Stephen Strange	Neurology	stephen.strange@nexus_ai.com	+1 555-000-0000	gid_strange	1213916290149152	strange	2026-04-30 17:35:39.543879+05:30
3	Dr. Shaun Murphy	Pediatrics	shaun.murphy@nexus_ai.com	+1 555-123-4567	gid_shaun	1213916290149152	shaun	2026-04-30 17:35:39.543879+05:30
\.


--
-- Data for Name: escalation_cases; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.escalation_cases (id, patient_id, case_type, status, summary, doctor_id, doctor_name, doctor_email, doctor_asana_gid, urgency, external_ticket_id, external_ticket_url, drive_file_id, drive_file_url, calendar_event_id, calendar_event_url, pharmacy_search_summary, drive_path, created_at) FROM stdin;
1	1	doctor_review	created	Review recent eczema flare-up and epilepsy medication interactions.	\N	\N	\N	\N	high	1214359117980066	https://app.asana.com/1/1213916290149152/project/1213919249096879/task/1214359117980066	\N	\N	\N	\N	\N	\N	2026-04-28 23:46:26.169256+05:30
2	1	doctor_review	created	Care Maze review requested after prescription upload. Full prescription extraction for Sreesha H.B. Three medications added to your profile records.	\N	\N	\N	\N	high	CQ-9CDDB31C	\N	\N	\N	\N	\N	\N	\N	2026-04-30 16:59:07.691421+05:30
3	1	doctor_review	created	Demo Auto-Handoff: Full prescription extraction for Sreesha H.B. Three medications added to your profile records.	\N	\N	\N	\N	high	1214418256387209	https://app.asana.com/1/1213916290149152/project/1213919249096879/task/1214418256387209	\N	\N	\N	\N	\N	\N	2026-04-30 17:37:52.683968+05:30
\.


--
-- Data for Name: medical_memories; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.medical_memories (id, patient_id, source_type, source_reference, modality, embedding_model, embedding_vector, summary_text, drive_file_id, drive_file_url, drive_path, metadata_json, created_at) FROM stdin;
1	1	manual_upload	\N	text	google/medsiglip-448:text	[0.43398184176394294, 0.46157015335317, 0.8718242160677501, -0.8425268940260929, -0.4225070572976273, -0.09861905851834896, -0.8231479362172884, 0.3045242999923705, -0.8396276798657206, -0.004440375371938643, 0.10466163118944083, 0.05104142824444957, 0.43855954833295185, 0.29011978332188915, 0.7124284733348591, -0.004287785152971679]		\N	\N	\N	{"note": "Initial patient setup notes"}	2026-04-28 23:46:26.203591+05:30
\.


--
-- Data for Name: medication_events; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.medication_events (id, patient_id, event_type, medication_name, details, created_at) FROM stdin;
\.


--
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notifications (id, patient_id, channel, message_type, body, delivery_status, created_at) FROM stdin;
1	1	mock_email	welcome	Welcome to nexus_ai demo workspace.	sent	2026-04-28 23:46:26.192848+05:30
\.


--
-- Data for Name: patient_condition_snapshots; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.patient_condition_snapshots (id, patient_id, snapshot_type, summary, profile_json, conditions_json, prescriptions_json, vitals_json, source_event_type, source_event_id, created_at) FROM stdin;
1	1	vision_upload	Before_and_after_input (1).png analyzed as symptom. Image analysis is temporarily unavailable.	{"patient_id": 1, "full_name": "Shreesha", "preferred_language": "en", "date_of_birth": "1990-01-01", "summary": "Shreesha prefers en and has 2 recorded conditions.", "height_cm": null, "weight_kg": null, "blood_group": null, "allergies": [], "emergency_contact_name": null, "emergency_contact_phone": null, "primary_language": null, "notes": null, "updated_at": null}	[{"id": 2, "name": "Epilepsy", "condition_type": "chronic", "last_updated": null, "notes": "Occasional seizures"}, {"id": 1, "name": "Eczema", "condition_type": "chronic", "last_updated": null, "notes": "Severe skin irritation"}]	[{"id": 3, "medication_name": "Metformin", "dosage": "500 mg", "instructions": "Twice daily with meals", "review_status": "structured", "created_at": "2026-04-28T23:46:23.938927+05:30"}, {"id": 2, "medication_name": "Metformin", "dosage": "500 mg", "instructions": "Twice daily with meals", "review_status": "structured", "created_at": "2026-04-28T23:46:23.933064+05:30"}, {"id": 1, "medication_name": "Metformin", "dosage": "500 mg", "instructions": "Twice daily with meals", "review_status": "structured", "created_at": "2026-04-28T23:46:23.917652+05:30"}]	[]	vision_upload	1OgY610DRLSWVE_az1E3EgVOzsQh2bfcD	2026-04-29 02:26:19.205405+05:30
\.


--
-- Data for Name: patient_doctor_map; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.patient_doctor_map (id, patient_id, doctor_id, relationship_type, is_default, notes, created_at) FROM stdin;
\.


--
-- Data for Name: patient_profile_details; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.patient_profile_details (id, patient_id, height_cm, weight_kg, blood_group, allergies_json, emergency_contact_name, emergency_contact_phone, primary_language, notes, updated_at) FROM stdin;
\.


--
-- Data for Name: patient_vitals; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.patient_vitals (id, patient_id, blood_pressure, heart_rate_bpm, blood_glucose_mg_dl, temperature_c, weight_kg, source, recorded_at) FROM stdin;
\.


--
-- Data for Name: patients; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.patients (id, full_name, preferred_language, date_of_birth, summary, google_email, google_access_token, google_refresh_token, google_token_expiry, created_at) FROM stdin;
1	Shreesha	en	1990-01-01	Shreesha prefers en and has 2 recorded conditions.	\N	\N	\N	\N	2026-04-28 23:46:23.859187+05:30
\.


--
-- Data for Name: pending_actions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pending_actions (id, patient_id, action_type, status, draft_payload_json, options_json, selected_option_json, result_json, created_at, confirmed_at) FROM stdin;
\.


--
-- Data for Name: prescriptions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.prescriptions (id, patient_id, source_reference, raw_text, medication_name, dosage, instructions, confidence_score, review_status, document_drive_file_id, document_drive_file_url, drive_path, created_at) FROM stdin;
1	1	\N	Prescription for Unknown Med	Metformin	500 mg	Twice daily with meals	0.92	structured	\N	\N	\N	2026-04-28 23:46:23.917652+05:30
2	1	\N	Prescription for Unknown Med	Metformin	500 mg	Twice daily with meals	0.92	structured	\N	\N	\N	2026-04-28 23:46:23.933064+05:30
3	1	\N	Prescription for Unknown Med	Metformin	500 mg	Twice daily with meals	0.92	structured	\N	\N	\N	2026-04-28 23:46:23.938927+05:30
\.


--
-- Data for Name: saved_diet_recipes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.saved_diet_recipes (id, patient_id, recipe_id, created_at) FROM stdin;
\.


--
-- Name: chat_messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.chat_messages_id_seq', 3, true);


--
-- Name: chat_threads_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.chat_threads_id_seq', 6, true);


--
-- Name: chronic_conditions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.chronic_conditions_id_seq', 2, true);


--
-- Name: doctors_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.doctors_id_seq', 3, true);


--
-- Name: escalation_cases_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.escalation_cases_id_seq', 3, true);


--
-- Name: medical_memories_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.medical_memories_id_seq', 1, true);


--
-- Name: medication_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.medication_events_id_seq', 1, false);


--
-- Name: notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.notifications_id_seq', 1, true);


--
-- Name: patient_condition_snapshots_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.patient_condition_snapshots_id_seq', 1, true);


--
-- Name: patient_doctor_map_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.patient_doctor_map_id_seq', 1, false);


--
-- Name: patient_profile_details_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.patient_profile_details_id_seq', 1, false);


--
-- Name: patient_vitals_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.patient_vitals_id_seq', 1, false);


--
-- Name: patients_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.patients_id_seq', 1, true);


--
-- Name: pending_actions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pending_actions_id_seq', 1, false);


--
-- Name: prescriptions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.prescriptions_id_seq', 3, true);


--
-- Name: saved_diet_recipes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.saved_diet_recipes_id_seq', 1, false);


--
-- Name: chat_messages chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_pkey PRIMARY KEY (id);


--
-- Name: chat_threads chat_threads_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_threads
    ADD CONSTRAINT chat_threads_pkey PRIMARY KEY (id);


--
-- Name: chronic_conditions chronic_conditions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chronic_conditions
    ADD CONSTRAINT chronic_conditions_pkey PRIMARY KEY (id);


--
-- Name: doctors doctors_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.doctors
    ADD CONSTRAINT doctors_pkey PRIMARY KEY (id);


--
-- Name: escalation_cases escalation_cases_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.escalation_cases
    ADD CONSTRAINT escalation_cases_pkey PRIMARY KEY (id);


--
-- Name: medical_memories medical_memories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_memories
    ADD CONSTRAINT medical_memories_pkey PRIMARY KEY (id);


--
-- Name: medication_events medication_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medication_events
    ADD CONSTRAINT medication_events_pkey PRIMARY KEY (id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: patient_condition_snapshots patient_condition_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_condition_snapshots
    ADD CONSTRAINT patient_condition_snapshots_pkey PRIMARY KEY (id);


--
-- Name: patient_doctor_map patient_doctor_map_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_doctor_map
    ADD CONSTRAINT patient_doctor_map_pkey PRIMARY KEY (id);


--
-- Name: patient_profile_details patient_profile_details_patient_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_profile_details
    ADD CONSTRAINT patient_profile_details_patient_id_key UNIQUE (patient_id);


--
-- Name: patient_profile_details patient_profile_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_profile_details
    ADD CONSTRAINT patient_profile_details_pkey PRIMARY KEY (id);


--
-- Name: patient_vitals patient_vitals_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_vitals
    ADD CONSTRAINT patient_vitals_pkey PRIMARY KEY (id);


--
-- Name: patients patients_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patients
    ADD CONSTRAINT patients_pkey PRIMARY KEY (id);


--
-- Name: pending_actions pending_actions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pending_actions
    ADD CONSTRAINT pending_actions_pkey PRIMARY KEY (id);


--
-- Name: prescriptions prescriptions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prescriptions
    ADD CONSTRAINT prescriptions_pkey PRIMARY KEY (id);


--
-- Name: saved_diet_recipes saved_diet_recipes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.saved_diet_recipes
    ADD CONSTRAINT saved_diet_recipes_pkey PRIMARY KEY (id);


--
-- Name: chat_messages chat_messages_thread_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_thread_id_fkey FOREIGN KEY (thread_id) REFERENCES public.chat_threads(id);


--
-- Name: chat_threads chat_threads_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_threads
    ADD CONSTRAINT chat_threads_doctor_id_fkey FOREIGN KEY (doctor_id) REFERENCES public.doctors(id);


--
-- Name: chat_threads chat_threads_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_threads
    ADD CONSTRAINT chat_threads_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: chronic_conditions chronic_conditions_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chronic_conditions
    ADD CONSTRAINT chronic_conditions_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: escalation_cases escalation_cases_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.escalation_cases
    ADD CONSTRAINT escalation_cases_doctor_id_fkey FOREIGN KEY (doctor_id) REFERENCES public.doctors(id);


--
-- Name: escalation_cases escalation_cases_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.escalation_cases
    ADD CONSTRAINT escalation_cases_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: medical_memories medical_memories_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medical_memories
    ADD CONSTRAINT medical_memories_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: medication_events medication_events_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.medication_events
    ADD CONSTRAINT medication_events_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: notifications notifications_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: patient_condition_snapshots patient_condition_snapshots_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_condition_snapshots
    ADD CONSTRAINT patient_condition_snapshots_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: patient_doctor_map patient_doctor_map_doctor_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_doctor_map
    ADD CONSTRAINT patient_doctor_map_doctor_id_fkey FOREIGN KEY (doctor_id) REFERENCES public.doctors(id);


--
-- Name: patient_doctor_map patient_doctor_map_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_doctor_map
    ADD CONSTRAINT patient_doctor_map_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: patient_profile_details patient_profile_details_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_profile_details
    ADD CONSTRAINT patient_profile_details_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: patient_vitals patient_vitals_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patient_vitals
    ADD CONSTRAINT patient_vitals_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: pending_actions pending_actions_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pending_actions
    ADD CONSTRAINT pending_actions_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: prescriptions prescriptions_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.prescriptions
    ADD CONSTRAINT prescriptions_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- Name: saved_diet_recipes saved_diet_recipes_patient_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.saved_diet_recipes
    ADD CONSTRAINT saved_diet_recipes_patient_id_fkey FOREIGN KEY (patient_id) REFERENCES public.patients(id);


--
-- PostgreSQL database dump complete
--

\unrestrict lOyUPDJC5GznVCScDKTzsUXY6yy5Q3gyhxxTnq1Q5ciEbVQlZR6rU9dIMtLX4KO

