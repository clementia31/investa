-- Investa — statistiques immobilières publiques (bloc 1 : tables, sécurité, fonction d'import)
create extension if not exists http with schema extensions;

create table if not exists public.immo_zones (niveau text, code text, nom text, parent text, primary key (niveau, code));
create table if not exists public.immo_communes (code text primary key, nom text, niveau text, commune_parent text,
  departement text, region text, epci text, population integer, codes_postaux text, zonage_abc text);
create table if not exists public.immo_prix (niveau text, code text, periode text, type text, nb_ventes integer,
  prix_m2_median integer, prix_m2_moyen integer, primary key (niveau, code, type, periode));
create table if not exists public.immo_loyers (annee smallint, code text, type text, loyer_m2 real, loyer_m2_bas real,
  loyer_m2_haut real, prediction text, nb_obs_commune integer, primary key (code, type, annee));
create table if not exists public.immo_fiscalite (annee smallint, code text, taux_global_tfb real, taux_global_tfnb real,
  taux_plein_teom real, taux_global_th real, primary key (code, annee));
create table if not exists public.immo_oll (observatoire text, annee smallint, agglomeration text, zone text, type_habitat text,
  epoque_construction text, anciennete_locataire text, pieces text, loyer_m2_median real, loyer_m2_moyen real,
  loyer_m2_q1 real, loyer_m2_q3 real, loyer_mensuel_median real, loyer_mensuel_moyen real, surface_moyenne real,
  nb_observations integer, nb_logements integer, methode text);
create table if not exists public.immo_insee_series (idbank text primary key, flux text, titre text, unite text,
  frequence text, derniere_maj text);
create table if not exists public.immo_insee (idbank text, periode text, valeur numeric, primary key (idbank, periode));
create index if not exists immo_prix_periode on public.immo_prix (periode, type, niveau);
create index if not exists immo_communes_dep on public.immo_communes (departement);

-- Données publiques : lecture seule pour tout le monde, aucune écriture possible depuis l'application
do $$ declare t text; begin
  foreach t in array array['immo_zones','immo_communes','immo_prix','immo_loyers','immo_fiscalite','immo_oll',
                           'immo_insee_series','immo_insee'] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('drop policy if exists "lecture publique" on public.%I', t);
    execute format('create policy "lecture publique" on public.%I for select to anon, authenticated using (true)', t);
    execute format('revoke insert, update, delete, truncate on public.%I from anon, authenticated', t);
  end loop;
end $$;

-- Import d'un morceau JSON depuis GitHub (le morceau 1 vide d'abord la table)
create or replace function public.immo_import(p_table text, p_part int)
returns integer language plpgsql set search_path = public, extensions as $$
declare v_json json; v_n integer;
begin
  if p_table not in ('immo_zones','immo_communes','immo_prix','immo_loyers','immo_fiscalite','immo_oll',
                     'immo_insee_series','immo_insee') then
    raise exception 'table inconnue : %', p_table;
  end if;
  perform http_set_curlopt('CURLOPT_TIMEOUT_MSEC', '60000');
  select content::json into v_json from http_get(format(
    'https://raw.githubusercontent.com/clementia31/investa/main/data/immo/db/%s_%s.json', p_table, lpad(p_part::text, 2, '0')));
  if p_part = 1 then execute format('truncate table public.%I', p_table); end if;
  execute format('insert into public.%I select * from json_populate_recordset(null::public.%I, $1)', p_table, p_table) using v_json;
  get diagnostics v_n = row_count;
  return v_n;
end $$;
revoke execute on function public.immo_import(text, int) from public, anon, authenticated;
