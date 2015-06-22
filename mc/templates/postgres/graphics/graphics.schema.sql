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
-- Name: graphics; Type: TABLE; Schema: public; Owner: graphics; Tablespace: 
--

CREATE TABLE graphics (
    id integer NOT NULL,
    bibcode character varying NOT NULL,
    doi character varying,
    source character varying,
    eprint boolean,
    figures json,
    modtime timestamp without time zone
);


ALTER TABLE public.graphics OWNER TO graphics;

--
-- Name: graphics_id_seq; Type: SEQUENCE; Schema: public; Owner: graphics
--

CREATE SEQUENCE graphics_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.graphics_id_seq OWNER TO graphics;

--
-- Name: graphics_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: graphics
--

ALTER SEQUENCE graphics_id_seq OWNED BY graphics.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: graphics
--

ALTER TABLE ONLY graphics ALTER COLUMN id SET DEFAULT nextval('graphics_id_seq'::regclass);


--
-- Name: graphics_pkey; Type: CONSTRAINT; Schema: public; Owner: graphics; Tablespace: 
--

ALTER TABLE ONLY graphics
    ADD CONSTRAINT graphics_pkey PRIMARY KEY (id);


--
-- Name: ix_graphics_bibcode; Type: INDEX; Schema: public; Owner: graphics; Tablespace: 
--

CREATE INDEX ix_graphics_bibcode ON graphics USING btree (bibcode);


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

