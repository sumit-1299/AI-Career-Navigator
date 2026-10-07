--
-- PostgreSQL database dump
--


-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
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
-- Name: canonical_skills; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.canonical_skills (
    id integer NOT NULL,
    canonical_name character varying(150) CONSTRAINT canonical_skills_name_not_null NOT NULL,
    normalized_name character varying(150) NOT NULL,
    skill_type character varying(100),
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: canonical_skills_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.canonical_skills_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: canonical_skills_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.canonical_skills_id_seq OWNED BY public.canonical_skills.id;


--
-- Name: career_preferences; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.career_preferences (
    id integer NOT NULL,
    user_id integer NOT NULL,
    target_role character varying(100) NOT NULL,
    preferred_domain character varying(100) NOT NULL,
    experience_level character varying(50) NOT NULL
);


--
-- Name: career_preferences_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.career_preferences_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: career_preferences_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.career_preferences_id_seq OWNED BY public.career_preferences.id;


--
-- Name: career_skills; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.career_skills (
    id integer NOT NULL,
    career_id integer NOT NULL,
    skill_name character varying(100) NOT NULL,
    required_level integer NOT NULL,
    importance integer NOT NULL,
    canonical_skill_id integer
);


--
-- Name: career_skills_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.career_skills_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: career_skills_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.career_skills_id_seq OWNED BY public.career_skills.id;


--
-- Name: careers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.careers (
    id integer NOT NULL,
    title character varying(100) NOT NULL,
    domain character varying(100) NOT NULL,
    description text
);


--
-- Name: careers_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.careers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: careers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.careers_id_seq OWNED BY public.careers.id;


--
-- Name: data_sources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.data_sources (
    id integer NOT NULL,
    source_name character varying(150) CONSTRAINT data_sources_name_not_null NOT NULL,
    source_type character varying(50) NOT NULL,
    website text,
    license text,
    description text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    source_version character varying(50)
);


--
-- Name: data_sources_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.data_sources_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: data_sources_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.data_sources_id_seq OWNED BY public.data_sources.id;


--
-- Name: learning_resources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.learning_resources (
    id integer NOT NULL,
    canonical_skill_id integer NOT NULL,
    title character varying(250) NOT NULL,
    resource_type character varying(50) NOT NULL,
    provider character varying(100) NOT NULL,
    url text NOT NULL,
    difficulty_level character varying(50) NOT NULL,
    estimated_duration character varying(50),
    description text,
    certification_available boolean NOT NULL,
    status character varying(50) NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);


--
-- Name: learning_resources_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.learning_resources_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: learning_resources_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.learning_resources_id_seq OWNED BY public.learning_resources.id;


--
-- Name: skill_aliases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.skill_aliases (
    id integer NOT NULL,
    canonical_skill_id integer CONSTRAINT skill_aliases_skill_id_not_null NOT NULL,
    alias_name character varying(200) CONSTRAINT skill_aliases_alias_not_null NOT NULL,
    source_id integer,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    normalized_alias character varying(200)
);


--
-- Name: skill_aliases_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.skill_aliases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: skill_aliases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.skill_aliases_id_seq OWNED BY public.skill_aliases.id;


--
-- Name: skills; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.skills (
    id integer NOT NULL,
    user_id integer NOT NULL,
    skill_name character varying(100) NOT NULL,
    proficiency integer NOT NULL,
    canonical_skill_id integer
);


--
-- Name: skills_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.skills_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: skills_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.skills_id_seq OWNED BY public.skills.id;


--
-- Name: student_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.student_profiles (
    id integer NOT NULL,
    user_id integer NOT NULL,
    education character varying(100) NOT NULL,
    specialization character varying(150),
    graduation_year integer,
    cgpa double precision
);


--
-- Name: student_profiles_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.student_profiles_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: student_profiles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.student_profiles_id_seq OWNED BY public.student_profiles.id;


--
-- Name: user_learning_progress; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_learning_progress (
    id integer NOT NULL,
    user_id integer NOT NULL,
    learning_resource_id integer NOT NULL,
    canonical_skill_id integer NOT NULL,
    status character varying(50) NOT NULL,
    progress_percentage double precision NOT NULL,
    notes text,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    last_updated timestamp without time zone NOT NULL
);


--
-- Name: user_learning_progress_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.user_learning_progress_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: user_learning_progress_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.user_learning_progress_id_seq OWNED BY public.user_learning_progress.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    email character varying(120) NOT NULL,
    password_hash character varying(255) NOT NULL
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: canonical_skills id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.canonical_skills ALTER COLUMN id SET DEFAULT nextval('public.canonical_skills_id_seq'::regclass);


--
-- Name: career_preferences id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.career_preferences ALTER COLUMN id SET DEFAULT nextval('public.career_preferences_id_seq'::regclass);


--
-- Name: career_skills id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.career_skills ALTER COLUMN id SET DEFAULT nextval('public.career_skills_id_seq'::regclass);


--
-- Name: careers id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.careers ALTER COLUMN id SET DEFAULT nextval('public.careers_id_seq'::regclass);


--
-- Name: data_sources id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_sources ALTER COLUMN id SET DEFAULT nextval('public.data_sources_id_seq'::regclass);


--
-- Name: learning_resources id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_resources ALTER COLUMN id SET DEFAULT nextval('public.learning_resources_id_seq'::regclass);


--
-- Name: skill_aliases id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_aliases ALTER COLUMN id SET DEFAULT nextval('public.skill_aliases_id_seq'::regclass);


--
-- Name: skills id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skills ALTER COLUMN id SET DEFAULT nextval('public.skills_id_seq'::regclass);


--
-- Name: student_profiles id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles ALTER COLUMN id SET DEFAULT nextval('public.student_profiles_id_seq'::regclass);


--
-- Name: user_learning_progress id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_learning_progress ALTER COLUMN id SET DEFAULT nextval('public.user_learning_progress_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: canonical_skills canonical_skills_canonical_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.canonical_skills
    ADD CONSTRAINT canonical_skills_canonical_name_key UNIQUE (canonical_name);


--
-- Name: canonical_skills canonical_skills_normalized_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.canonical_skills
    ADD CONSTRAINT canonical_skills_normalized_name_key UNIQUE (normalized_name);


--
-- Name: canonical_skills canonical_skills_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.canonical_skills
    ADD CONSTRAINT canonical_skills_pkey PRIMARY KEY (id);


--
-- Name: career_preferences career_preferences_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.career_preferences
    ADD CONSTRAINT career_preferences_pkey PRIMARY KEY (id);


--
-- Name: career_preferences career_preferences_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.career_preferences
    ADD CONSTRAINT career_preferences_user_id_key UNIQUE (user_id);


--
-- Name: career_skills career_skills_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.career_skills
    ADD CONSTRAINT career_skills_pkey PRIMARY KEY (id);


--
-- Name: careers careers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.careers
    ADD CONSTRAINT careers_pkey PRIMARY KEY (id);


--
-- Name: careers careers_title_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.careers
    ADD CONSTRAINT careers_title_key UNIQUE (title);


--
-- Name: data_sources data_sources_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_sources
    ADD CONSTRAINT data_sources_name_key UNIQUE (source_name);


--
-- Name: data_sources data_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.data_sources
    ADD CONSTRAINT data_sources_pkey PRIMARY KEY (id);


--
-- Name: learning_resources learning_resources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_resources
    ADD CONSTRAINT learning_resources_pkey PRIMARY KEY (id);


--
-- Name: skill_aliases skill_aliases_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_aliases
    ADD CONSTRAINT skill_aliases_pkey PRIMARY KEY (id);


--
-- Name: skills skills_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT skills_pkey PRIMARY KEY (id);


--
-- Name: student_profiles student_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT student_profiles_pkey PRIMARY KEY (id);


--
-- Name: student_profiles student_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT student_profiles_user_id_key UNIQUE (user_id);


--
-- Name: skill_aliases uq_canonical_skill_normalized_alias; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_aliases
    ADD CONSTRAINT uq_canonical_skill_normalized_alias UNIQUE (canonical_skill_id, normalized_alias);


--
-- Name: user_learning_progress uq_user_learning_resource; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_learning_progress
    ADD CONSTRAINT uq_user_learning_resource UNIQUE (user_id, learning_resource_id);


--
-- Name: user_learning_progress user_learning_progress_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_learning_progress
    ADD CONSTRAINT user_learning_progress_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: ix_career_skills_canonical_skill_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_career_skills_canonical_skill_id ON public.career_skills USING btree (canonical_skill_id);


--
-- Name: ix_learning_resources_canonical_skill_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_learning_resources_canonical_skill_id ON public.learning_resources USING btree (canonical_skill_id);


--
-- Name: ix_skill_aliases_normalized_alias; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_skill_aliases_normalized_alias ON public.skill_aliases USING btree (normalized_alias);


--
-- Name: ix_skills_canonical_skill_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_skills_canonical_skill_id ON public.skills USING btree (canonical_skill_id);


--
-- Name: ix_user_learning_progress_canonical_skill_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_learning_progress_canonical_skill_id ON public.user_learning_progress USING btree (canonical_skill_id);


--
-- Name: ix_user_learning_progress_learning_resource_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_learning_progress_learning_resource_id ON public.user_learning_progress USING btree (learning_resource_id);


--
-- Name: ix_user_learning_progress_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_learning_progress_user_id ON public.user_learning_progress USING btree (user_id);


--
-- Name: career_preferences career_preferences_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.career_preferences
    ADD CONSTRAINT career_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: career_skills career_skills_career_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.career_skills
    ADD CONSTRAINT career_skills_career_id_fkey FOREIGN KEY (career_id) REFERENCES public.careers(id);


--
-- Name: career_skills fk_career_skills_canonical_skill; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.career_skills
    ADD CONSTRAINT fk_career_skills_canonical_skill FOREIGN KEY (canonical_skill_id) REFERENCES public.canonical_skills(id) ON DELETE SET NULL;


--
-- Name: skills fk_skills_canonical_skill; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT fk_skills_canonical_skill FOREIGN KEY (canonical_skill_id) REFERENCES public.canonical_skills(id) ON DELETE SET NULL;


--
-- Name: learning_resources learning_resources_canonical_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.learning_resources
    ADD CONSTRAINT learning_resources_canonical_skill_id_fkey FOREIGN KEY (canonical_skill_id) REFERENCES public.canonical_skills(id) ON DELETE CASCADE;


--
-- Name: skill_aliases skill_aliases_skill_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_aliases
    ADD CONSTRAINT skill_aliases_skill_fk FOREIGN KEY (canonical_skill_id) REFERENCES public.canonical_skills(id) ON DELETE CASCADE;


--
-- Name: skill_aliases skill_aliases_source_fk; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_aliases
    ADD CONSTRAINT skill_aliases_source_fk FOREIGN KEY (source_id) REFERENCES public.data_sources(id) ON DELETE SET NULL;


--
-- Name: skills skills_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT skills_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: student_profiles student_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.student_profiles
    ADD CONSTRAINT student_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: user_learning_progress user_learning_progress_canonical_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_learning_progress
    ADD CONSTRAINT user_learning_progress_canonical_skill_id_fkey FOREIGN KEY (canonical_skill_id) REFERENCES public.canonical_skills(id) ON DELETE CASCADE;


--
-- Name: user_learning_progress user_learning_progress_learning_resource_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_learning_progress
    ADD CONSTRAINT user_learning_progress_learning_resource_id_fkey FOREIGN KEY (learning_resource_id) REFERENCES public.learning_resources(id) ON DELETE CASCADE;


--
-- Name: user_learning_progress user_learning_progress_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_learning_progress
    ADD CONSTRAINT user_learning_progress_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--


--
-- PostgreSQL database dump
--


-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: canonical_skills; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.canonical_skills (id, canonical_name, normalized_name, skill_type, description, created_at, updated_at) FROM stdin;
1	Python	python	Programming Language	High-level general-purpose programming language	2026-10-04 13:09:49.180478	2026-10-04 13:09:49.180482
2	Java	java	Programming Language	Object-oriented class-based programming language	2026-10-04 13:09:49.189299	2026-10-04 13:09:49.189303
3	SQL	sql	Database Query Language	Domain-specific language used in programming and managing databases	2026-10-04 13:09:49.19256	2026-10-04 13:09:49.192563
4	HTML	html	Web Technology	Standard markup language for documents designed to be displayed in a web browser	2026-10-04 13:09:49.194586	2026-10-04 13:09:49.194589
5	CSS	css	Web Technology	Style sheet language used for describing the presentation of a document	2026-10-04 13:09:49.196598	2026-10-04 13:09:49.1966
6	JavaScript	javascript	Programming Language	Programming language that is one of the core technologies of the World Wide Web	2026-10-04 13:09:49.199043	2026-10-04 13:09:49.199046
7	React	react	Frontend Framework	Free and open-source front-end JavaScript library for building user interfaces	2026-10-04 13:09:49.20096	2026-10-04 13:09:49.200962
8	Git	git	Version Control	Distributed version control system for tracking changes in source code	2026-10-04 13:09:49.202491	2026-10-04 13:09:49.202493
9	Docker	docker	Containerization	Set of platform-as-a-service products using OS-level virtualization to deliver software in containers	2026-10-04 13:09:49.204144	2026-10-04 13:09:49.204146
10	Kubernetes	kubernetes	Container Orchestration	Open-source system for automating deployment, scaling, and management of containerized applications	2026-10-04 13:09:49.206273	2026-10-04 13:09:49.206276
11	Linux	linux	Operating System	Open-source Unix-like operating system based on the Linux kernel	2026-10-04 13:09:49.207956	2026-10-04 13:09:49.207959
12	PostgreSQL	postgresql	Database	Free and open-source relational database management system emphasizing extensibility and SQL compliance	2026-10-04 13:09:49.209375	2026-10-04 13:09:49.209377
13	MySQL	mysql	Database	Open-source relational database management system	2026-10-04 13:09:49.210829	2026-10-04 13:09:49.210831
14	Machine Learning	machine learning	Artificial Intelligence	Study of computer algorithms that improve automatically through experience and data	2026-10-04 13:09:49.212786	2026-10-04 13:09:49.21279
15	Deep Learning	deep learning	Artificial Intelligence	Subfield of machine learning based on artificial neural networks	2026-10-04 13:09:49.214582	2026-10-04 13:09:49.214584
16	AWS	aws	Cloud Computing	Comprehensive, evolving cloud computing platform provided by Amazon	2026-10-04 13:09:49.21595	2026-10-04 13:09:49.215953
17	Networking	networking	Infrastructure	Practice of transporting and exchanging data between nodes over a shared medium	2026-10-04 13:09:49.217378	2026-10-04 13:09:49.21738
18	Cybersecurity	cybersecurity	Security	Protection of computer systems and networks from information disclosure, theft, or damage	2026-10-04 13:09:49.219014	2026-10-04 13:09:49.219017
19	CI/CD	ci/cd	DevOps	Combined practice of continuous integration and continuous delivery/deployment	2026-10-04 13:09:49.221189	2026-10-04 13:09:49.221192
20	Data Structures	data structures	Computer Science	Data organization, management, and storage format that enables efficient access and modification	2026-10-04 13:09:49.222717	2026-10-04 13:09:49.222719
21	Pandas	pandas	Data Analytics Library	Software library written for Python for data manipulation and analysis	2026-10-04 13:09:49.22418	2026-10-04 13:09:49.224182
22	TensorFlow	tensorflow	Machine Learning Framework	Free and open-source software library for machine learning and artificial intelligence	2026-10-04 13:09:49.225777	2026-10-04 13:09:49.22578
23	Excel	excel	Software Tool	Spreadsheet software developed by Microsoft	2026-10-04 13:09:49.228043	2026-10-04 13:09:49.228046
24	Statistics	statistics	Mathematics	Discipline concerning the collection, organization, analysis, interpretation, and presentation of data	2026-10-04 13:09:49.231285	2026-10-04 13:09:49.231288
25	Power BI	power bi	Data Analytics Tool	Interactive data visualization software product developed by Microsoft	2026-10-04 13:09:49.233428	2026-10-04 13:09:49.233432
26	SIEM	siem	Cybersecurity	Security information and event management software system	2026-10-04 13:09:49.235326	2026-10-04 13:09:49.235328
27	CCNA	ccna	Certification / Networking	Cisco Certified Network Associate credential and skill knowledge	2026-10-04 13:09:49.23702	2026-10-04 13:09:49.237022
28	Routing and Switching	routing and switching	Networking	Configuring network paths, routing protocols, and hardware switches	2026-10-04 13:09:49.238907	2026-10-04 13:09:49.238909
29	Database Security	database security	Database Management	Collective measures used to secure and protect database management systems	2026-10-04 13:09:49.241097	2026-10-04 13:09:49.241099
30	Network Security	network security	Networking	Provisions and policies adopted to prevent and monitor unauthorized access	2026-10-04 13:09:49.242887	2026-10-04 13:09:49.24289
\.


--
-- Data for Name: careers; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.careers (id, title, domain, description) FROM stdin;
1	Software Developer	Software Development	Designs develops tests and maintains software applications.
2	Web Developer	Web Development	Builds and maintains websites and web applications.
3	Data Analyst	Data Analytics	Analyzes data to identify trends insights and support business decisions.
4	Data Scientist	Data Science	Uses statistics programming and machine learning to extract insights from data.
5	AI/ML Engineer	Artificial Intelligence	Designs and develops machine learning and artificial intelligence systems.
6	Cloud Engineer	Cloud Computing	Designs deploys and manages cloud infrastructure and services.
7	DevOps Engineer	DevOps	Automates software delivery infrastructure and operational processes.
8	Cybersecurity Analyst	Cybersecurity	Monitors systems and protects organizations from security threats.
9	Network Engineer	Networking	Designs configures and maintains computer networks.
10	Database Administrator	Database Management	Manages databases including performance security backup and recovery.
\.


--
-- Data for Name: career_skills; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.career_skills (id, career_id, skill_name, required_level, importance, canonical_skill_id) FROM stdin;
1	1	Python	4	5	1
2	1	Java	4	5	2
3	1	Data Structures	4	5	20
4	1	Git	3	4	8
5	1	SQL	3	3	3
6	2	HTML	4	5	4
7	2	CSS	4	5	5
8	2	JavaScript	4	5	6
9	2	React	3	4	7
10	2	Git	3	3	8
11	3	Python	3	5	1
12	3	SQL	4	5	3
13	3	Excel	4	4	23
14	3	Statistics	3	5	24
15	3	Power BI	3	4	25
16	4	Python	4	5	1
17	4	SQL	3	4	3
18	4	Statistics	4	5	24
19	4	Machine Learning	4	5	14
20	4	Pandas	4	4	21
21	5	Python	4	5	1
22	5	Machine Learning	4	5	14
23	5	Deep Learning	4	5	15
24	5	TensorFlow	3	4	22
25	5	Statistics	3	4	24
26	6	Linux	4	5	11
27	6	Networking	4	5	17
28	6	AWS	4	5	16
29	6	Python	3	3	1
30	6	Docker	3	4	9
31	7	Linux	4	5	11
32	7	Docker	4	5	9
33	7	Kubernetes	4	5	10
34	7	Git	4	4	8
35	7	CI/CD	4	5	19
36	8	Linux	4	5	11
37	8	Networking	4	5	17
38	8	Cybersecurity	4	5	18
39	8	Python	3	3	1
40	8	SIEM	3	4	26
41	9	Networking	5	5	17
42	9	Linux	3	3	11
43	9	Routing and Switching	4	5	28
44	9	CCNA	4	4	27
45	9	Network Security	3	4	30
46	10	SQL	5	5	3
47	10	PostgreSQL	4	5	12
48	10	MySQL	4	4	13
49	10	Linux	3	3	11
50	10	Database Security	3	4	29
\.


--
-- Data for Name: learning_resources; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.learning_resources (id, canonical_skill_id, title, resource_type, provider, url, difficulty_level, estimated_duration, description, certification_available, status, created_at, updated_at) FROM stdin;
1	1	Python for Everybody Specialization	Course	Coursera / University of Michigan	https://www.coursera.org/specializations/python	Beginner	40 hours	Learn to program and analyze data with Python, from basic syntax to databases and web scrapers.	t	Active	2026-10-04 17:39:05.366878	2026-10-04 17:39:05.366885
2	1	Official Python 3 Documentation & Tutorial	Documentation	Python Software Foundation	https://docs.python.org/3/tutorial/	Beginner	15 hours	Authoritative language tutorial and reference covering data types, control flow, functions, and standard libraries.	f	Active	2026-10-04 17:39:05.372435	2026-10-04 17:39:05.37244
3	16	AWS Cloud Practitioner Essentials	Course	AWS Skill Builder	https://explore.skillbuilder.aws/learn/course/external/view/elearning/134/aws-cloud-practitioner-essentials	Beginner	6 hours	Foundational understanding of the AWS Cloud, security, architecture, pricing, and support.	t	Active	2026-10-04 17:39:05.375365	2026-10-04 17:39:05.375369
4	16	AWS Certified Solutions Architect Associate Hands-on Labs	Project	AWS Workshops	https://workshops.aws/	Intermediate	25 hours	Architectural patterns, VPC networking, auto-scaling, and multi-tier resilient application deployments.	t	Active	2026-10-04 17:39:05.377832	2026-10-04 17:39:05.377834
5	9	Docker Getting Started Tutorial & Play with Docker	Practice Platform	Docker Inc.	https://docs.docker.com/get-started/	Beginner	8 hours	Interactive browser-based sandbox and tutorial for containerizing applications, building Dockerfiles, and compose stacks.	f	Active	2026-10-04 17:39:05.380612	2026-10-04 17:39:05.380615
6	9	Docker & Kubernetes: The Complete Practical Guide	Course	Udemy	https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/	Intermediate	22 hours	Build, test, and deploy Docker applications with Kubernetes production setups.	t	Active	2026-10-04 17:39:05.383368	2026-10-04 17:39:05.383371
7	3	SQL Tutorial & Interactive Practice	Practice Platform	Mode Analytics / SQLBolt	https://mode.com/sql-tutorial/	Beginner	12 hours	Comprehensive SQL tutorial covering SELECT, aggregations, JOINs, subqueries, and window functions.	f	Active	2026-10-04 17:39:05.386016	2026-10-04 17:39:05.38602
8	8	Pro Git Book & Interactive Git Branching	Book	Git SCM	https://git-scm.com/book/en/v2	Beginner	10 hours	The definitive open-source guide to Git internals, branching workflows, merging strategies, and remote collaboration.	f	Active	2026-10-04 17:39:05.38862	2026-10-04 17:39:05.388627
9	11	Introduction to Linux (LFS101x)	Course	The Linux Foundation / edX	https://www.edx.org/course/introduction-to-linux	Beginner	30 hours	Fundamental concepts, command-line operations, shell scripts, and system administration.	t	Active	2026-10-04 17:39:05.391128	2026-10-04 17:39:05.391131
10	20	Data Structures and Algorithms Specialization	Course	Coursera / UC San Diego	https://www.coursera.org/specializations/data-structures-algorithms	Intermediate	45 hours	Algorithmic thinking, trees, hash tables, graphs, dynamic programming, and algorithm optimization.	t	Active	2026-10-04 17:39:05.393884	2026-10-04 17:39:05.393888
11	10	Kubernetes Official Tutorials & Interactive Tasks	Tutorial	Cloud Native Computing Foundation	https://kubernetes.io/docs/tutorials/	Intermediate	15 hours	Deploying containerized apps, exploring Pods, services, scaling, and rolling updates.	f	Active	2026-10-04 17:39:05.396582	2026-10-04 17:39:05.396585
12	16	AWS Certified Solutions Architect – Associate (SAA-C03)	Certification	Amazon Web Services	https://aws.amazon.com/certification/certified-solutions-architect-associate/	Intermediate	60 hours	Validates proficiency in designing secure, high-performing, resilient, and cost-optimized architectures on AWS.	t	Active	2026-10-05 16:44:54.639415	2026-10-05 16:44:54.639419
13	16	AWS Certified Developer – Associate (DVA-C02)	Certification	Amazon Web Services	https://aws.amazon.com/certification/certified-developer-associate/	Intermediate	50 hours	Validates technical expertise in developing, deploying, and debugging cloud-based applications using AWS.	t	Active	2026-10-05 16:44:54.644562	2026-10-05 16:44:54.644565
14	27	Cisco Certified Network Associate (CCNA 200-301)	Certification	Cisco Systems	https://www.cisco.com/c/en/us/training-events/training-certifications/certifications/associate/ccna.html	Intermediate	80 hours	Validates foundational networking knowledge, IP connectivity, network access, security fundamentals, and automation.	t	Active	2026-10-05 16:44:54.647713	2026-10-05 16:44:54.647717
15	10	Certified Kubernetes Administrator (CKA)	Certification	Cloud Native Computing Foundation / Linux Foundation	https://www.cncf.io/certification/cka/	Advanced	70 hours	Validates skills, knowledge and competency to perform responsibilities of Kubernetes administrators.	t	Active	2026-10-05 16:44:54.650444	2026-10-05 16:44:54.650446
16	9	Docker Certified Associate (DCA)	Certification	Mirantis / Docker	https://training.mirantis.com/certification/dca-certification-exam/	Intermediate	40 hours	Validates essential container orchestration, image creation, security, and networking skills on Docker.	t	Active	2026-10-05 16:44:54.653154	2026-10-05 16:44:54.653157
17	18	CompTIA Security+ (SY0-701)	Certification	CompTIA	https://www.comptia.org/certifications/security	Intermediate	60 hours	Global benchmark credential validating foundational security knowledge, threat detection, cryptography, and risk assessment.	t	Active	2026-10-05 16:44:54.655446	2026-10-05 16:44:54.655448
18	1	Certified Associate in Python Programming (PCAP-31-03)	Certification	Python Institute	https://pythoninstitute.org/pcap	Intermediate	45 hours	Validates fundamental programming concepts, object-oriented design, modules, packages, and exception handling in Python.	t	Active	2026-10-05 16:44:54.657472	2026-10-05 16:44:54.657474
19	11	Red Hat Certified System Administrator (RHCSA EX200)	Certification	Red Hat	https://www.redhat.com/en/services/certification/rhcsa	Intermediate	80 hours	Validates core enterprise system administration skills across Red Hat Enterprise Linux environments.	t	Active	2026-10-05 16:44:54.659778	2026-10-05 16:44:54.65978
20	7	Meta Front-End Developer Professional Certificate	Certification	Meta / Coursera	https://www.coursera.org/professional-certificates/meta-front-end-developer	Beginner	100 hours	Comprehensive front-end engineering program covering React, JavaScript ES6+, UX/UI design, and web applications.	t	Active	2026-10-05 16:44:54.661991	2026-10-05 16:44:54.661993
21	14	DeepLearning.AI Machine Learning Specialization	Certification	DeepLearning.AI / Stanford	https://www.deeplearning.ai/courses/machine-learning-specialization/	Intermediate	60 hours	Master foundational machine learning concepts, supervised learning, neural networks, and recommender systems.	t	Active	2026-10-05 16:44:54.664141	2026-10-05 16:44:54.664143
22	3	Oracle Database SQL Certified Associate (1Z0-071)	Certification	Oracle University	https://education.oracle.com/oracle-database-sql/pexam_1Z0-071	Intermediate	50 hours	Demonstrates deep understanding of SQL queries, data manipulation, schema objects, joins, subqueries, and views.	t	Active	2026-10-05 16:44:54.66641	2026-10-05 16:44:54.666413
23	19	GitHub Actions Certification	Certification	GitHub	https://learn.microsoft.com/en-us/credentials/certifications/github-actions/	Intermediate	30 hours	Validates proficiency in automating workflows, building robust CI/CD pipelines, and secure secret management with GitHub Actions.	t	Active	2026-10-05 16:44:54.668644	2026-10-05 16:44:54.668646
24	1	Production REST API with FastAPI, SQLAlchemy & Pytest	Project	AI Career Navigator Portfolio Labs	https://github.com/fastapi/fastapi	Intermediate	20 hours	Build a production-grade asynchronous REST API complete with JWT authentication, database migrations, and 90%+ unit test coverage.	f	Active	2026-10-05 16:44:54.670605	2026-10-05 16:44:54.670607
25	7	Enterprise Responsive Career Analytics Dashboard	Project	Frontend Practice & Community	https://react.dev/learn	Intermediate	25 hours	Develop a modern React 18 single-page application featuring interactive charts, filtering, responsive layout, and client-side routing.	f	Active	2026-10-05 16:44:54.672862	2026-10-05 16:44:54.672865
26	9	Containerized Microservices Architecture with Docker Compose	Project	DevOps Hands-on Labs	https://docs.docker.com/compose/	Intermediate	18 hours	Package and network multi-service web architectures including web frontend, REST backend, caching, and database with isolated networks.	f	Active	2026-10-05 16:44:54.675022	2026-10-05 16:44:54.675024
27	10	High-Availability K8s Cluster Deployment & Ingress Controller	Project	Kubernetes Community Labs	https://kubernetes.io/docs/concepts/workloads/controllers/deployment/	Advanced	30 hours	Deploy and configure zero-downtime rolling deployments, horizontal pod autoscalers, secrets, and NGINX Ingress rules.	f	Active	2026-10-05 16:44:54.677571	2026-10-05 16:44:54.677573
28	3	Enterprise E-Commerce Relational Data Warehouse Modeling	Project	Mode Analytics Labs	https://mode.com/sql-tutorial/	Intermediate	15 hours	Model transactional relational schemas in 3NF, write window aggregation analytics, and optimize slow execution plans with indexing.	f	Active	2026-10-05 16:44:54.67984	2026-10-05 16:44:54.679843
29	14	End-to-End Predictive Machine Learning Pipeline & Registry	Project	Kaggle Applied Machine Learning	https://www.kaggle.com/learn	Intermediate	25 hours	Engineer numerical features, train ensemble regression/classification models, tune hyperparameters, and deploy via REST endpoint.	f	Active	2026-10-05 16:44:54.682061	2026-10-05 16:44:54.682064
30	19	Full-Stack GitOps Automated Deployment Pipeline	Project	Cloud Native DevOps Labs	https://github.com/actions	Intermediate	15 hours	Build an end-to-end GitHub Actions workflow validating linters, running unit tests, building Docker images, and publishing release artifacts.	f	Active	2026-10-05 16:44:54.68417	2026-10-05 16:44:54.684172
31	18	Vulnerability Assessment & Network Defense Hardening Lab	Project	CyberDefenders Labs	https://cyberdefenders.org/	Intermediate	20 hours	Perform threat vulnerability analysis using security scanners, analyze network packet captures, and implement hardened firewall rules.	f	Active	2026-10-05 16:44:54.686409	2026-10-05 16:44:54.686412
32	12	Database Performance Tuning & Concurrency Benchmark System	Project	PostgreSQL Community Projects	https://www.postgresql.org/docs/	Advanced	20 hours	Design benchmark tests measuring row locks, index types (B-Tree, GIN), partitioning strategies, and connection pooler behaviors.	f	Active	2026-10-05 16:44:54.688529	2026-10-05 16:44:54.688531
33	11	Automated Linux Server Provisioning & Bash Tooling Suite	Project	Linux Foundation Labs	https://linuxfoundation.org/	Beginner	12 hours	Author comprehensive shell scripts for user management, automated backup archiving, system daemon management, and cron job scheduling.	f	Active	2026-10-05 16:44:54.690808	2026-10-05 16:44:54.69081
\.


--
-- Name: canonical_skills_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.canonical_skills_id_seq', 30, true);


--
-- Name: career_skills_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.career_skills_id_seq', 50, true);


--
-- Name: careers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.careers_id_seq', 10, true);


--
-- Name: learning_resources_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.learning_resources_id_seq', 33, true);


--
-- PostgreSQL database dump complete
--



--
-- Data for Name: data_sources; Type: TABLE DATA; Schema: public; Owner: career_app
--

COPY public.data_sources (id, source_name, source_type, website, license, description, created_at, source_version) FROM stdin;
1	O*NET	Career Knowledge	https://www.onetcenter.org/database.html	Creative Commons	Occupational and workforce information	2026-09-12 14:23:28.153267	31.0
2	ESCO	Career Knowledge	https://esco.ec.europa.eu/	\N	European skills, competences, qualifications and occupations	2026-09-12 14:23:28.153267	1.2.1
3	NSDC	Career Knowledge	https://www.nsdcindia.org/	\N	Indian occupational standards and qualification information	2026-09-12 14:23:28.153267	1.0
4	PROTOTYPE	In-house Catalog	\N	\N	Curated IT benchmark skills for initial career tracks	2026-10-04 18:38:49.183896	1.0
\.


--
-- Data for Name: skill_aliases; Type: TABLE DATA; Schema: public; Owner: career_app
--

COPY public.skill_aliases (id, canonical_skill_id, alias_name, source_id, created_at, normalized_alias) FROM stdin;
1	1	Python	4	2026-10-04 13:09:49.1863	python
2	2	Java	4	2026-10-04 13:09:49.190869	java
3	3	SQL	4	2026-10-04 13:09:49.193648	sql
4	4	HTML	4	2026-10-04 13:09:49.195517	html
5	5	CSS	4	2026-10-04 13:09:49.197758	css
6	6	JavaScript	4	2026-10-04 13:09:49.200079	javascript
7	7	React	4	2026-10-04 13:09:49.201773	react
8	8	Git	4	2026-10-04 13:09:49.203365	git
9	9	Docker	4	2026-10-04 13:09:49.205241	docker
10	10	Kubernetes	4	2026-10-04 13:09:49.207195	kubernetes
11	11	Linux	4	2026-10-04 13:09:49.208704	linux
12	12	PostgreSQL	4	2026-10-04 13:09:49.210187	postgresql
13	13	MySQL	4	2026-10-04 13:09:49.211697	mysql
14	14	Machine Learning	4	2026-10-04 13:09:49.213801	machine learning
15	15	Deep Learning	4	2026-10-04 13:09:49.215302	deep learning
16	16	AWS	4	2026-10-04 13:09:49.216662	aws
17	17	Networking	4	2026-10-04 13:09:49.218087	networking
18	18	Cybersecurity	4	2026-10-04 13:09:49.220233	cybersecurity
19	19	CI/CD	4	2026-10-04 13:09:49.222035	ci/cd
20	20	Data Structures	4	2026-10-04 13:09:49.223394	data structures
21	21	Pandas	4	2026-10-04 13:09:49.224843	pandas
22	22	TensorFlow	4	2026-10-04 13:09:49.227032	tensorflow
23	23	Excel	4	2026-10-04 13:09:49.230209	excel
24	24	Statistics	4	2026-10-04 13:09:49.232335	statistics
25	25	Power BI	4	2026-10-04 13:09:49.234459	power bi
26	26	SIEM	4	2026-10-04 13:09:49.236193	siem
27	27	CCNA	4	2026-10-04 13:09:49.237927	ccna
28	28	Routing and Switching	4	2026-10-04 13:09:49.240103	routing and switching
29	29	Database Security	4	2026-10-04 13:09:49.241922	database security
30	30	Network Security	4	2026-10-04 13:09:49.243724	network security
31	2	Java (computer programming)	2	2026-10-04 13:09:50.349204	java (computer programming)
32	1	Python (computer programming)	2	2026-10-04 13:09:51.019916	python (computer programming)
\.


--
-- Name: data_sources_id_seq; Type: SEQUENCE SET; Schema: public; Owner: career_app
--

SELECT pg_catalog.setval('public.data_sources_id_seq', 5, true);


--
-- Name: skill_aliases_id_seq; Type: SEQUENCE SET; Schema: public; Owner: career_app
--

SELECT pg_catalog.setval('public.skill_aliases_id_seq', 32, true);
