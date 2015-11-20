--
-- PostgreSQL database dump
--

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: adsws; Tablespace: 
--

CREATE TABLE alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO adsws;

--
-- Name: oauth2client; Type: TABLE; Schema: public; Owner: adsws; Tablespace: 
--

CREATE TABLE oauth2client (
    name character varying(40),
    description text,
    website text,
    user_id integer,
    client_id character varying(255) NOT NULL,
    client_secret character varying(255) NOT NULL,
    is_confidential boolean,
    is_internal boolean,
    last_activity timestamp without time zone,
    _redirect_uris text,
    _default_scopes text
);


ALTER TABLE public.oauth2client OWNER TO adsws;

--
-- Name: oauth2token; Type: TABLE; Schema: public; Owner: adsws; Tablespace: 
--

CREATE TABLE oauth2token (
    id integer NOT NULL,
    client_id character varying(40) NOT NULL,
    user_id integer,
    token_type character varying(255),
    access_token character varying(255),
    refresh_token character varying(255),
    expires timestamp without time zone,
    _scopes text,
    is_personal boolean,
    is_internal boolean
);


ALTER TABLE public.oauth2token OWNER TO adsws;

--
-- Name: oauth2token_id_seq; Type: SEQUENCE; Schema: public; Owner: adsws
--

CREATE SEQUENCE oauth2token_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.oauth2token_id_seq OWNER TO adsws;

--
-- Name: oauth2token_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adsws
--

ALTER SEQUENCE oauth2token_id_seq OWNED BY oauth2token.id;


--
-- Name: roles; Type: TABLE; Schema: public; Owner: adsws; Tablespace: 
--

CREATE TABLE roles (
    id integer NOT NULL,
    name character varying(80),
    description character varying(255)
);


ALTER TABLE public.roles OWNER TO adsws;

--
-- Name: roles_id_seq; Type: SEQUENCE; Schema: public; Owner: adsws
--

CREATE SEQUENCE roles_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.roles_id_seq OWNER TO adsws;

--
-- Name: roles_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adsws
--

ALTER SEQUENCE roles_id_seq OWNED BY roles.id;


--
-- Name: roles_users; Type: TABLE; Schema: public; Owner: adsws; Tablespace: 
--

CREATE TABLE roles_users (
    user_id integer,
    role_id integer
);


ALTER TABLE public.roles_users OWNER TO adsws;

--
-- Name: users; Type: TABLE; Schema: public; Owner: adsws; Tablespace: 
--

CREATE TABLE users (
    id integer NOT NULL,
    email character varying(255),
    password character varying(255),
    name character varying(255),
    active boolean,
    confirmed_at timestamp without time zone,
    last_login_at timestamp without time zone,
    login_count integer,
    registered_at timestamp without time zone,
    ratelimit_level integer
);


ALTER TABLE public.users OWNER TO adsws;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: adsws
--

CREATE SEQUENCE users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO adsws;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: adsws
--

ALTER SEQUENCE users_id_seq OWNED BY users.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: adsws
--

ALTER TABLE ONLY oauth2token ALTER COLUMN id SET DEFAULT nextval('oauth2token_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: adsws
--

ALTER TABLE ONLY roles ALTER COLUMN id SET DEFAULT nextval('roles_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: adsws
--

ALTER TABLE ONLY users ALTER COLUMN id SET DEFAULT nextval('users_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: adsws
--

COPY alembic_version (version_num) FROM stdin;
2e0c0694da22
\.


--
-- Data for Name: oauth2client; Type: TABLE DATA; Schema: public; Owner: adsws
--

COPY oauth2client (name, description, website, user_id, client_id, client_secret, is_confidential, is_internal, last_activity, _redirect_uris, _default_scopes) FROM stdin;
vis-services			10	S7gjLuoxOCOwyUq61mGcBTSatWHn4szdiAkQR5HX	kUhD20d5gwrxifV5vS6VOphpeYUsWUqAJQroCOzK	t	t	\N	\N	\N
recommender@ads			28	WM9EQpxThNBAMyZaTRDxi5OSkOwNto1lv57INGaX	CgtzeKUDBgwZkPBq2yOeQfgSlwVxEkfUSGCfBX2i	t	t	\N	\N	\N
biblib@ads			31	Q6TRJuAD23ZzyaQ94C3qvSCg3Gk7qKTKrxtB1NU6	CgtzeKUDBgwZkPBq2yOeQfgSlwVxEkfUSGCfBX2i	t	t	\N	\N	\N
tester@ads			59	Sy6NLN5wgOs0f0oUBBbw4H6WvndmMcW7yL3LJ2i7	zvNuQqYkjbJUVBEcty8xonx7GiKwYpSNvEaDdw1P	t	t	\N	\N	\N
\.


--
-- Data for Name: oauth2token; Type: TABLE DATA; Schema: public; Owner: adsws
--

COPY oauth2token (id, client_id, user_id, token_type, access_token, refresh_token, expires, _scopes, is_personal, is_internal) FROM stdin;
173	WM9EQpxThNBAMyZaTRDxi5OSkOwNto1lv57INGaX	28	bearer	jzMwX8vaoR20hAu3y24fomOf3BUXUpktElScaLnp	anR42y2ccQ9zawiwBBbUZ5SeVvGKMALfu8395zeC	2050-01-01 00:00:00	api	t	t
26	S7gjLuoxOCOwyUq61mGcBTSatWHn4szdiAkQR5HX	10	bearer	hWxXLcxRHgjER10GXJrScYeCmpOsvcBEP8i7FIFS	V3ICtceIqRvNuR9TnHTFR3gfzHdEWbZblB1yuNkj	2050-01-01 00:00:00	api	t	t
192	Q6TRJuAD23ZzyaQ94C3qvSCg3Gk7qKTKrxtB1NU6	31	bearer	D58JjURMLIPEzqfYNyKeqG1kR8O6AjV4pW4njdBV	LkJeTR9fyYitVNPYcnPZHEF2d0kw2scuipRxDyf6	2050-01-01 00:00:00	ads:internal api	t	t
182	Sy6NLN5wgOs0f0oUBBbw4H6WvndmMcW7yL3LJ2i7	59	bearer	Jh5ehrzFtEl2OCoF1DEMCU1ubJlASqlyfKgwGoQ4	YIqGTvLZ9s1XYkLL1PTgzBGpld2iJVkLV2c84FVC	2050-01-01 00:00:00	user store-query execute-query store-preferences	t	t
\.


--
-- Name: oauth2token_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adsws
--

SELECT pg_catalog.setval('oauth2token_id_seq', 4, true);


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: adsws
--

COPY roles (id, name, description) FROM stdin;
\.


--
-- Name: roles_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adsws
--

SELECT pg_catalog.setval('roles_id_seq', 1, false);


--
-- Data for Name: roles_users; Type: TABLE DATA; Schema: public; Owner: adsws
--

COPY roles_users (user_id, role_id) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: adsws
--

COPY users (id, email, password, name, active, confirmed_at, last_login_at, login_count, registered_at, ratelimit_level) FROM stdin;
1	anonymous@ads	\N	\N	t	2015-04-24 12:20:43.205067	\N	\N	2015-04-24 12:20:43.205082	\N
10	vis-services@ads	\N	\N	\N	\N	\N	\N	\N	1000
28	recommender@ads	\N	\N	\N	\N	\N	\N	\N	\N
31	biblib@ads	\N	\N	\N	\N	\N	\N	\N	1000
59	tester@ads	\N	\N	t	\N	\N	\N	\N	\N
\.


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: adsws
--

SELECT pg_catalog.setval('users_id_seq', 5, true);


--
-- Name: oauth2client_pkey; Type: CONSTRAINT; Schema: public; Owner: adsws; Tablespace: 
--

ALTER TABLE ONLY oauth2client
    ADD CONSTRAINT oauth2client_pkey PRIMARY KEY (client_id);


--
-- Name: oauth2token_access_token_key; Type: CONSTRAINT; Schema: public; Owner: adsws; Tablespace: 
--

ALTER TABLE ONLY oauth2token
    ADD CONSTRAINT oauth2token_access_token_key UNIQUE (access_token);


--
-- Name: oauth2token_pkey; Type: CONSTRAINT; Schema: public; Owner: adsws; Tablespace: 
--

ALTER TABLE ONLY oauth2token
    ADD CONSTRAINT oauth2token_pkey PRIMARY KEY (id);


--
-- Name: oauth2token_refresh_token_key; Type: CONSTRAINT; Schema: public; Owner: adsws; Tablespace: 
--

ALTER TABLE ONLY oauth2token
    ADD CONSTRAINT oauth2token_refresh_token_key UNIQUE (refresh_token);


--
-- Name: roles_name_key; Type: CONSTRAINT; Schema: public; Owner: adsws; Tablespace: 
--

ALTER TABLE ONLY roles
    ADD CONSTRAINT roles_name_key UNIQUE (name);


--
-- Name: roles_pkey; Type: CONSTRAINT; Schema: public; Owner: adsws; Tablespace: 
--

ALTER TABLE ONLY roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: users_email_key; Type: CONSTRAINT; Schema: public; Owner: adsws; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users_pkey; Type: CONSTRAINT; Schema: public; Owner: adsws; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: oauth2client_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adsws
--

ALTER TABLE ONLY oauth2client
    ADD CONSTRAINT oauth2client_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: oauth2token_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adsws
--

ALTER TABLE ONLY oauth2token
    ADD CONSTRAINT oauth2token_client_id_fkey FOREIGN KEY (client_id) REFERENCES oauth2client(client_id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: oauth2token_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adsws
--

ALTER TABLE ONLY oauth2token
    ADD CONSTRAINT oauth2token_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON UPDATE CASCADE ON DELETE CASCADE;


--
-- Name: roles_users_role_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adsws
--

ALTER TABLE ONLY roles_users
    ADD CONSTRAINT roles_users_role_id_fkey FOREIGN KEY (role_id) REFERENCES roles(id);


--
-- Name: roles_users_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: adsws
--

ALTER TABLE ONLY roles_users
    ADD CONSTRAINT roles_users_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id);


--
-- Name: public; Type: ACL; Schema: -; Owner: adsws
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

