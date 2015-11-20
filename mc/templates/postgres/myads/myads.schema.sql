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
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: myads; Tablespace: 
--

CREATE TABLE alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO myads;

--
-- Name: queries; Type: TABLE; Schema: public; Owner: myads; Tablespace: 
--

CREATE TABLE queries (
    id integer NOT NULL,
    uid integer,
    qid character varying(32),
    created timestamp without time zone,
    updated timestamp without time zone,
    numfound integer,
    category character varying(255),
    query bytea
);


ALTER TABLE public.queries OWNER TO myads;

--
-- Name: queries_id_seq; Type: SEQUENCE; Schema: public; Owner: myads
--

CREATE SEQUENCE queries_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.queries_id_seq OWNER TO myads;

--
-- Name: queries_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: myads
--

ALTER SEQUENCE queries_id_seq OWNED BY queries.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: myads; Tablespace: 
--

CREATE TABLE users (
    id integer NOT NULL,
    name character varying(255),
    user_data bytea
);


ALTER TABLE public.users OWNER TO myads;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: myads
--

CREATE SEQUENCE users_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO myads;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: myads
--

ALTER SEQUENCE users_id_seq OWNED BY users.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: myads
--

ALTER TABLE ONLY queries ALTER COLUMN id SET DEFAULT nextval('queries_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: myads
--

ALTER TABLE ONLY users ALTER COLUMN id SET DEFAULT nextval('users_id_seq'::regclass);


--
-- Name: queries_pkey; Type: CONSTRAINT; Schema: public; Owner: myads; Tablespace: 
--

ALTER TABLE ONLY queries
    ADD CONSTRAINT queries_pkey PRIMARY KEY (id);


--
-- Name: queries_qid_key; Type: CONSTRAINT; Schema: public; Owner: myads; Tablespace: 
--

ALTER TABLE ONLY queries
    ADD CONSTRAINT queries_qid_key UNIQUE (qid);


--
-- Name: users_pkey; Type: CONSTRAINT; Schema: public; Owner: myads; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: public; Type: ACL; Schema: -; Owner: adsabs
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM adsabs;
GRANT ALL ON SCHEMA public TO adsabs;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

