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
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: orcid; Tablespace: 
--

CREATE TABLE alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO orcid;

--
-- Name: users; Type: TABLE; Schema: public; Owner: orcid; Tablespace: 
--

CREATE TABLE users (
    orcid_id character varying(255) NOT NULL,
    access_token character varying(255),
    created timestamp without time zone,
    updated timestamp without time zone,
    profile bytea
);


ALTER TABLE public.users OWNER TO orcid;

--
-- Name: users_pkey; Type: CONSTRAINT; Schema: public; Owner: orcid; Tablespace: 
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (orcid_id);


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

