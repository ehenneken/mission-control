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
-- Name: clustering; Type: TABLE; Schema: public; Owner: recommender; Tablespace: 
--

CREATE TABLE clustering (
    id integer NOT NULL,
    bibcode character varying NOT NULL,
    cluster integer,
    vector double precision[],
    vector_low double precision[]
);


ALTER TABLE public.clustering OWNER TO recommender;

--
-- Name: clustering_id_seq; Type: SEQUENCE; Schema: public; Owner: recommender
--

CREATE SEQUENCE clustering_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.clustering_id_seq OWNER TO recommender;

--
-- Name: clustering_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: recommender
--

ALTER SEQUENCE clustering_id_seq OWNED BY clustering.id;


--
-- Name: clusters; Type: TABLE; Schema: public; Owner: recommender; Tablespace: 
--

CREATE TABLE clusters (
    id integer NOT NULL,
    cluster integer,
    members character varying[],
    centroid double precision[]
);


ALTER TABLE public.clusters OWNER TO recommender;

--
-- Name: clusters_id_seq; Type: SEQUENCE; Schema: public; Owner: recommender
--

CREATE SEQUENCE clusters_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.clusters_id_seq OWNER TO recommender;

--
-- Name: clusters_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: recommender
--

ALTER SEQUENCE clusters_id_seq OWNED BY clusters.id;


--
-- Name: coreads; Type: TABLE; Schema: public; Owner: recommender; Tablespace: 
--

CREATE TABLE coreads (
    id integer NOT NULL,
    bibcode character varying NOT NULL,
    coreads json
);


ALTER TABLE public.coreads OWNER TO recommender;

--
-- Name: coreads_id_seq; Type: SEQUENCE; Schema: public; Owner: recommender
--

CREATE SEQUENCE coreads_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.coreads_id_seq OWNER TO recommender;

--
-- Name: coreads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: recommender
--

ALTER SEQUENCE coreads_id_seq OWNED BY coreads.id;


--
-- Name: readers; Type: TABLE; Schema: public; Owner: recommender; Tablespace: 
--

CREATE TABLE readers (
    id integer NOT NULL,
    bibcode character varying NOT NULL,
    readers character varying[]
);


ALTER TABLE public.readers OWNER TO recommender;

--
-- Name: readers_id_seq; Type: SEQUENCE; Schema: public; Owner: recommender
--

CREATE SEQUENCE readers_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.readers_id_seq OWNER TO recommender;

--
-- Name: readers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: recommender
--

ALTER SEQUENCE readers_id_seq OWNED BY readers.id;


--
-- Name: reads; Type: TABLE; Schema: public; Owner: recommender; Tablespace: 
--

CREATE TABLE reads (
    id integer NOT NULL,
    cookie character varying NOT NULL,
    reads character varying[]
);


ALTER TABLE public.reads OWNER TO recommender;

--
-- Name: reads_id_seq; Type: SEQUENCE; Schema: public; Owner: recommender
--

CREATE SEQUENCE reads_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.reads_id_seq OWNER TO recommender;

--
-- Name: reads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: recommender
--

ALTER SEQUENCE reads_id_seq OWNED BY reads.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: recommender
--

ALTER TABLE ONLY clustering ALTER COLUMN id SET DEFAULT nextval('clustering_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: recommender
--

ALTER TABLE ONLY clusters ALTER COLUMN id SET DEFAULT nextval('clusters_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: recommender
--

ALTER TABLE ONLY coreads ALTER COLUMN id SET DEFAULT nextval('coreads_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: recommender
--

ALTER TABLE ONLY readers ALTER COLUMN id SET DEFAULT nextval('readers_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: recommender
--

ALTER TABLE ONLY reads ALTER COLUMN id SET DEFAULT nextval('reads_id_seq'::regclass);


--
-- Name: clustering_pkey; Type: CONSTRAINT; Schema: public; Owner: recommender; Tablespace: 
--

ALTER TABLE ONLY clustering
    ADD CONSTRAINT clustering_pkey PRIMARY KEY (id);


--
-- Name: clusters_pkey; Type: CONSTRAINT; Schema: public; Owner: recommender; Tablespace: 
--

ALTER TABLE ONLY clusters
    ADD CONSTRAINT clusters_pkey PRIMARY KEY (id);


--
-- Name: coreads_pkey; Type: CONSTRAINT; Schema: public; Owner: recommender; Tablespace: 
--

ALTER TABLE ONLY coreads
    ADD CONSTRAINT coreads_pkey PRIMARY KEY (id);


--
-- Name: readers_pkey; Type: CONSTRAINT; Schema: public; Owner: recommender; Tablespace: 
--

ALTER TABLE ONLY readers
    ADD CONSTRAINT readers_pkey PRIMARY KEY (id);


--
-- Name: reads_pkey; Type: CONSTRAINT; Schema: public; Owner: recommender; Tablespace: 
--

ALTER TABLE ONLY reads
    ADD CONSTRAINT reads_pkey PRIMARY KEY (id);


--
-- Name: ix_clustering_bibcode; Type: INDEX; Schema: public; Owner: recommender; Tablespace: 
--

CREATE INDEX ix_clustering_bibcode ON clustering USING btree (bibcode);


--
-- Name: ix_clusters_cluster; Type: INDEX; Schema: public; Owner: recommender; Tablespace: 
--

CREATE INDEX ix_clusters_cluster ON clusters USING btree (cluster);


--
-- Name: ix_coreads_bibcode; Type: INDEX; Schema: public; Owner: recommender; Tablespace: 
--

CREATE INDEX ix_coreads_bibcode ON coreads USING btree (bibcode);


--
-- Name: ix_readers_bibcode; Type: INDEX; Schema: public; Owner: recommender; Tablespace: 
--

CREATE INDEX ix_readers_bibcode ON readers USING btree (bibcode);


--
-- Name: ix_reads_cookie; Type: INDEX; Schema: public; Owner: recommender; Tablespace: 
--

CREATE INDEX ix_reads_cookie ON reads USING btree (cookie);


--
-- Name: public; Type: ACL; Schema: -; Owner: recommender
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM recommender;
GRANT ALL ON SCHEMA public TO recommender;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

