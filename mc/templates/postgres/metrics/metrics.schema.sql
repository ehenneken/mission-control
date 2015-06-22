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
-- Name: metrics; Type: TABLE; Schema: public; Owner: metrics; Tablespace: 
--

CREATE TABLE metrics (
    id integer NOT NULL,
    bibcode character varying NOT NULL,
    refereed boolean,
    rn_citations real,
    rn_citation_data json,
    rn_citations_hist json,
    downloads integer[],
    reads integer[],
    an_citations real,
    refereed_citation_num integer,
    citation_num integer,
    citations character varying[],
    refereed_citations character varying[],
    author_num integer,
    an_refereed_citations real,
    modtime timestamp without time zone
);


ALTER TABLE public.metrics OWNER TO metrics;

--
-- Name: metrics_id_seq; Type: SEQUENCE; Schema: public; Owner: metrics
--

CREATE SEQUENCE metrics_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.metrics_id_seq OWNER TO metrics;

--
-- Name: metrics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: metrics
--

ALTER SEQUENCE metrics_id_seq OWNED BY metrics.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: metrics
--

ALTER TABLE ONLY metrics ALTER COLUMN id SET DEFAULT nextval('metrics_id_seq'::regclass);


--
-- Name: metrics_pkey; Type: CONSTRAINT; Schema: public; Owner: metrics; Tablespace: 
--

ALTER TABLE ONLY metrics
    ADD CONSTRAINT metrics_pkey PRIMARY KEY (id);


--
-- Name: ix_metrics_bibcode; Type: INDEX; Schema: public; Owner: metrics; Tablespace: 
--

CREATE UNIQUE INDEX ix_metrics_bibcode ON metrics USING btree (bibcode);


--
-- Name: public; Type: ACL; Schema: -; Owner: adsabs
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

