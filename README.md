# LUNA (Local University Notes Assistant)
LUNA è un sistema multi-agente per lo studio universitario con due funzionalità principali: Note Enhancement per la pulizia formale e l'arricchimento degli appunti, e Topic Research per la generazione autonoma di report su argomenti specifici. L'intera architettura funziona al 100% in locale, senza appoggiarsi al cloud, senza API a pagamento e garantendo la totale privacy dei dati.

## Requisiti
- Python 3.11+
- Ollama installato (scaricabile da https://ollama.com)
- ~16 GB di RAM raccomandati per l'esecuzione del modello `qwen3.5:9b`

## Setup
```bash
# 1. Installa le dipendenze Python
pip install -r requirements.txt

# 2. Scarica i modelli Ollama
ollama pull qwen3.5:2b
ollama pull qwen3.5:4b
ollama pull qwen3.5:9b
ollama pull embeddinggemma:300m

# 3. Verifica che Ollama gira
ollama list
```

## Avvio

**Modalità rapida (consigliata):** doppio click su `avvia.bat`.
Lo script verifica Python, le dipendenze, Ollama e i modelli necessari, scarica ciò che manca e apre la UI nel browser. Al primo avvio può richiedere alcuni minuti per installare i pacchetti e scaricare i modelli (~15 GB totali).

**Modalità manuale (alternativa):**
```bash
streamlit run app.py
```
L'interfaccia utente si aprirà nel browser all'indirizzo http://localhost:8501.

## Le tre tab

### Migliora i miei appunti
Incolli del testo o carichi un file in formato `.md`, `.txt` o `.pdf`. Puoi opzionalmente attivare il toggle "Integra con ricerca web". Di default questa funzionalità è OFF, ed è rigorosamente opt-in per ogni singola richiesta. Quando abilitato, il sistema cercherà automaticamente sul web per colmare le lacune individuate, altrimenti si limiterà a ripulire e formattare i tuoi appunti.

### Ricerca su un argomento
Inserisci un topic (es. "machine learning") e il sistema pianifica autonomamente delle sotto-query, cerca sul web, sintetizza i risultati e genera un report dettagliato provvisto di un'apposita sezione `## Fonti`.

### Libreria
Questa sezione permette di sfogliare, visualizzare un'anteprima, scaricare o eliminare in modo definitivo tutti i file Markdown generati nelle altre due sezioni.

## Esempi pre-generati

La cartella `examples/` contiene output reali della pipeline, per vedere subito un risultato senza dover lanciare la UI o aspettare l'inferenza locale:

- `notes_example_statistica_inferenziale.md` — output di Feature A su appunti di Statistica Inferenziale (test di ipotesi, t-test, ANOVA, frequentista vs bayesiano).

Per generare nuovi esempi è sufficiente lanciare `avvia.bat` (o `streamlit run app.py`) e usare la UI — i file finiscono in `outputs/notes/` o `outputs/research/`.

## Architettura (panoramica)
```
Notes:    linguist → structurer → gap_detector → [web_researcher?] → writer_notes → critic → save
Research: planner → searcher → synthesizer → writer_report → critic → save
```
Ogni nodo è un agente specializzato; orchestrazione via LangGraph; inferenza locale via Ollama.

## Tier dei modelli
| Livello | Modello | Descrizione |
|---|---|---|
| `QWEN_LIGHT` | `qwen3.5:2b` | Task puramente meccanici (linting, correzione sintattica). |
| `QWEN_MEDIUM` | `qwen3.5:4b` | Strutturazione e ragionamento intermedio (critic, gap detection). |
| `QWEN_HEAVY` | `qwen3.5:9b` | Generazione e sintesi (synthesis, planning e redazione di report/appunti). |
| `EMBED_MODEL` | `embeddinggemma:300m` | Creazione di embedding per il vector store (RAG). |

## Performance
I tempi sono indicativi e variano con la macchina, la lunghezza dell'input e il carico. Misurati su **AMD Ryzen 5 3600X / 16 GB RAM / NVIDIA GeForce RTX 5060 Ti** su appunti di ~500 parole.

### Feature A — Migliora i miei appunti

| Stage | Tempo | Note |
|---|---|---|
| linguist | 5–15 s | Modello 2b. Scala con la lunghezza del testo grezzo. |
| structurer | 10–25 s | Modello 4b. Applica formattazione Markdown. |
| gap_detector | 5–10 s | Modello 4b. Identifica lacune logiche in JSON. |
| web_researcher | ~ 50 s | Solo se "Integra con ricerca web" attivo. ~ 13 s per lacuna ricercata. |
| writer_notes (path veloce) | < 1 s | Bypass LLM quando non c'è web augmentation né critic feedback. |
| writer_notes (path LLM) | ~ 30 s | Modello 9b. Attivo con web augmentation o nel loop critic. |
| critic | 65–80 s | Modello 4b con `reasoning=True` per verifica multi-step rigorosa. |
| save_output | < 1 s | I/O su disco. |
| **Totale tipico** | **~ 2 min** (no web) · **~ 3 min** (web on) | |

### Feature B — Ricerca su un argomento

| Stage | Tempo | Note |
|---|---|---|
| planner | ~ 20 s | Modello 9b. Genera 3–6 sotto-query mirate sul topic. |
| searcher | ~ 35 s | I/O bound. ~ 6 s per sotto-query (DDGS + trafilatura, con filtro lunghezza). |
| synthesizer | ~ 6 s | Modello 9b. Veloce: opera su title+snippet, non sul fulltext. |
| writer_report | ~ 25 s | Modello 9b. Assembla il report seguendo il template. |
| critic | ~ 100 s | Modello 4b con `reasoning=True`. Più lento di Feature A: il report è più lungo da verificare. |
| save_output | < 1 s | I/O. |
| **Totale tipico** | **~ 3 min** | |

> Nota: il `critic` è il collo di bottiglia voluto. Usa `reasoning=True` (thinking di qwen3.5) per verificare il rispetto del template punto per punto. Disattivare il thinking renderebbe il pipeline ~10× più veloce ma con verifica meno affidabile.

## Troubleshooting
- **`ModuleNotFoundError: No module named 'agents'` quando lanci pytest:** 
  Causa: stai eseguendo pytest senza il `pythonpath` corretto. 
  Soluzione: Il repository include un file `pytest.ini` che lo configura automaticamente, ma è necessario lanciare il comando direttamente dalla project root.
- **Output di Feature A povero o vuoto:** 
  Causa: indeterminismo del modello locale, in particolare `qwen3.5:9b` può occasionalmente fallire a generare output validi. 
  Soluzione: Il sistema ha dei meccanismi di fallback deterministici che producono comunque una draft basata sul testo strutturato, ma se ti ritrovi un file eccessivamente povero, riesegui semplicemente la pipeline per ottenere un output più ricco.
- **`streamlit run` parte ma il browser non si apre:** 
  Causa: mancato aggancio automatico del default browser. 
  Soluzione: aprilo manualmente puntando il navigatore su http://localhost:8501.

## Test
```bash
# Smoke (veloce, < 2s, no Ollama)
pytest tests/test_agents_smoke.py -v

# Suite completa, escludendo i test lenti
pytest tests/ -v

# Test E2E con Ollama reale (~15 min)
pytest tests/test_graphs_e2e.py --run-slow -v
```

## Licenza / Crediti
Progetto accademico per il corso di Laboratorio di Data Science (UNIVPM, A.A. 2025/2026).
Professore Mensi
Studente: Matheus Soares Campos