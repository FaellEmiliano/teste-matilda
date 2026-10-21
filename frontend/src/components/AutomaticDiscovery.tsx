import { useState } from "react";
import {
  ArrowUpRight,
  Database,
  Info,
  LoaderCircle,
  Search,
} from "lucide-react";
import type { Analysis } from "../types";
import { expandDiscovery } from "../services/api";
import { citationLabels } from "./EvidenceInspector";

export function AutomaticDiscovery({
  analysis,
  onUpdated,
}: {
  analysis: Analysis;
  onUpdated: (result: Analysis) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [onlyDocumented, setOnlyDocumented] = useState(false);
  const result = analysis.external_discovery;
  async function expand() {
    setBusy(true);
    setError("");
    try {
      onUpdated(await expandDiscovery(analysis.id));
    } catch (error) {
      setError((error as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const candidates =
    result?.candidates.filter(
      (item) =>
        !onlyDocumented ||
        item.candidate.identities.some(
          (identity) => identity.status === "documented_woman",
        ),
    ) ?? [];
  return (
    <section className="automatic-discovery" aria-labelledby="automatic-title">
      <div className="automatic-heading">
        <div>
          <span className="eyebrow">CATÁLOGO EM CONSTRUÇÃO</span>
          <h2 id="automatic-title">
            <Database size={19} />
            Descoberta automática
          </h2>
          <p>
            Busque publicações além do catálogo editorial. Fontes e trechos
            entram como candidatos para revisão.
          </p>
        </div>
        <button
          className="primary-button"
          disabled={busy}
          onClick={() => void expand()}
        >
          {busy ? (
            <LoaderCircle className="spin" size={17} />
          ) : (
            <Search size={17} />
          )}
          {busy
            ? "Consultando fontes públicas…"
            : result
              ? "Consultar novamente"
              : "Ampliar descoberta automaticamente"}
        </button>
      </div>
      {busy && (
        <p role="status" className="small">
          Consultando OpenAlex, Europe PMC e identidades disponíveis por ORCID.
          Limite de 18 segundos; resultados parciais serão preservados.
        </p>
      )}
      {error && (
        <p role="alert" className="automatic-error">
          {error}
        </p>
      )}
      {result && (
        <details open className="automatic-results">
          <summary>
            {result.candidates.length} publicações candidatas ·{" "}
            {result.status === "complete"
              ? "Consulta concluída"
              : result.status === "partial"
                ? "Resultado parcial"
                : "Fontes indisponíveis"}
          </summary>
          <div className="notice">
            <Info size={17} />
            <p>
              Recuperação automática não equivale a verificação científica. A
              identidade documentada de uma autora não comprova seu papel
              individual no trabalho. Os candidatos permanecem separados das
              contribuições revisadas do grafo.
            </p>
          </div>
          <label className="automatic-filter">
            <input
              type="checkbox"
              checked={onlyDocumented}
              onChange={(event) => setOnlyDocumented(event.target.checked)}
            />
            Mostrar apenas trabalhos com ao menos uma mulher identificada por
            fonte explícita
          </label>
          <div className="candidate-grid">
            {candidates.map(
              ({ candidate, retrieval_reasons, citation_status }) => (
                <article className="candidate-card" key={candidate.id}>
                  <div className="candidate-meta">
                    <span className="badge">Pendente de revisão</span>
                    <span>{candidate.work.year ?? "Ano indisponível"}</span>
                  </div>
                  <h3>{candidate.work.title}</h3>
                  <a
                    className="text-link"
                    href={"https://doi.org/" + candidate.work.doi}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Publicação original <ArrowUpRight size={13} />
                  </a>
                  <p className="small">
                    {retrieval_reasons.join(" ")}{" "}
                    {citationLabels[citation_status]}.
                  </p>
                  {candidate.excerpt ? (
                    <>
                      <span className="eyebrow">
                        TRECHO EXTRAÍDO DO RESUMO · SEM REVISÃO
                      </span>
                      <blockquote>{candidate.excerpt}</blockquote>
                      <p className="small">{candidate.excerpt_location}</p>
                    </>
                  ) : (
                    <p className="small">
                      Resumo indisponível. Somente metadados recuperados.
                    </p>
                  )}
                  <details>
                    <summary>Autoria e resolução de identidades</summary>
                    <p className="small">
                      Todos os participantes recuperados:{" "}
                      {candidate.work.authors
                        .map((author) => author.name)
                        .join(" · ") || "Lista indisponível"}
                    </p>
                    {candidate.identities.map((identity, index) => (
                      <div key={index} className="candidate-identity">
                        <strong>{identity.author_name}</strong>
                        <span>
                          {identity.status === "documented_woman"
                            ? "Mulher identificada em fonte explícita"
                            : identity.status === "conflicting"
                              ? "Identidade ambígua — revisão necessária"
                              : "Identidade não confirmada"}
                        </span>
                        <p>{identity.explanation}</p>
                        {identity.source_urls.map((url) => (
                          <a
                            key={url}
                            href={url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-link"
                          >
                            Fonte de identidade <ArrowUpRight size={12} />
                          </a>
                        ))}
                      </div>
                    ))}
                  </details>
                  <details>
                    <summary>Procedência e limites</summary>
                    {candidate.work.sources.map((source, index) => (
                      <p key={index} className="small">
                        {source.source} ·{" "}
                        {source.from_cache
                          ? "cache identificado"
                          : "consulta externa"}{" "}
                        ·{" "}
                        {new Date(source.retrieved_at).toLocaleString("pt-BR")}
                      </p>
                    ))}
                    <p className="small">
                      Método: {candidate.extraction_method}. Relação temática,
                      sem influência histórica comprovada.
                    </p>
                    <ul>
                      {candidate.limitations.map((warning) => (
                        <li key={warning}>{warning}</li>
                      ))}
                    </ul>
                    <a
                      href={"/api/catalog/candidates/" + candidate.id}
                      target="_blank"
                      rel="noreferrer"
                      className="text-link"
                    >
                      Registro e histórico em JSON <ArrowUpRight size={12} />
                    </a>
                  </details>
                </article>
              ),
            )}
          </div>
          {!candidates.length && (
            <p className="automatic-empty">
              {onlyDocumented
                ? "Nenhum candidato com identidade feminina documentada neste resultado. Isso pode refletir falta de ORCID ou de fontes de identidade."
                : "Nenhuma publicação candidata recuperada. Isso não demonstra inexistência de contribuições femininas."}
            </p>
          )}
          <details className="automatic-coverage">
            <summary>Fontes consultadas e limites da ampliação</summary>
            <ul>
              {result.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
            <p className="small">
              Concluída em{" "}
              {new Date(result.completed_at).toLocaleString("pt-BR")}.{" "}
              {result.sources.length} consultas documentadas; limite de{" "}
              {result.limits.candidates} candidatos.
            </p>
            <a
              href="/api/catalog/candidates"
              target="_blank"
              rel="noreferrer"
              className="text-link"
            >
              Abrir fila do catálogo em JSON <ArrowUpRight size={12} />
            </a>
          </details>
        </details>
      )}
    </section>
  );
}
