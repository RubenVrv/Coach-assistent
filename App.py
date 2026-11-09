import streamlit as st
import pandas as pd
import google.genai as genai
import anthropic

st.set_page_config(page_title="Gratis AI Coach Assistent", layout="wide")
st.title("🚴‍♂️ Vitori AI Coach Dashboard ")
st.write("Analyseer TrainingPeaks-data voor professionele coaches")

# 1. INITIALISEER SESSION STATE (Dit voorkomt de KeyError)
if 'rapport' not in st.session_state:
    st.session_state['rapport'] = None

# 2. ZIJBALK: MODEL SELECTION & API KEYS
st.sidebar.header("🤖 Model Instellingen")
model_provider = st.sidebar.selectbox(
    "Kies AI Provider:",
    ["Google Gemini", "Anthropic Claude"]
)

api_key = ""
if model_provider == "Google Gemini":
    api_key = st.sidebar.text_input("Vul je Google Gemini API Key in:", type="password")
    selected_model = "gemini-3.8-flash"
    if not api_key:
        st.info("💡 Maak een API-sleutel aan via Google AI Studio om te starten.")
else:
    api_key = st.sidebar.text_input("Vul je Anthropic Claude API Key in:", type="password")
    selected_model = "claude-3-5-sonnet-20241022"
    if not api_key:
        st.info("💡 Maak een API-sleutel aan via de Anthropic Console om te starten.")

# 3. HOOFDSCHERM: INPUT & EXPERT CHECKBOXES
uploaded_file = st.file_uploader("Upload je TrainingPeaks 'Workout Summary' CSV-bestand:", type=["csv"])

st.subheader("🎯 Sportwetenschappelijke Focuspunten (Expert-niveau)")
st.write("Selecteer de analytische lenzen die de AI moet toepassen op de dataset:")

focus_load = st.checkbox("1. Belastingsanalyse & Respons (CTL, ATL, TSB trends & periodisering-validatie)", value=True)
focus_efficiency = st.checkbox(
    "2. Metabole & Mechanische Efficiëntie (Decoupling / Aerobe ontkoppeling Pw:Hr of Pa:Hr trends)", value=True)
focus_pd_curve = st.checkbox(
    "3. Fenotypering & Power-Duration Trends (Verschuivingen in kritiek vermogen / FTP / MMP-profiel)", value=True)
focus_fatigue = st.checkbox(
    "4. Risico-indicatoren (Maladaptatie, Non-Functional Overreaching (NFOR) & acute load spikes)", value=False)

extra_context = st.text_area(
    "Aanvullende atleet-fysiologie & context (bv. bekende drempelwaardes, VO2max, lactaatprofiel, blessurehistorie):",
    placeholder="Bv. FTP 320W, LTHR 172bpm. Atleet heeft neiging tot vroege aerobe ontkoppeling bij ritten > 3u."
)

# 4. ANALYSE LOGICA
if uploaded_file is not None and api_key:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip().str.lower()
        st.success(f"Data succesvol geladen! {len(df)} trainingen gevonden.")
        st.dataframe(df.head(5))

        if st.button("🚀 Start Expert Analyse"):
            with st.spinner(f"Uw sportwetenschappelijke assistent ({model_provider}) berekent de data..."):
                training_data = df.to_string(index=False)

                # Dynamische expert-opdracht opbouwen op basis van checkboxes
                opdracht_secties = ""
                if focus_load:
                    opdracht_secties += """
                    1. KWALITATIEVE EN QUANTITATIEVE PERIODISERING-EVALUATIE
                    - Evalueer de mechanische en fysiologische belasting chronologisch. 
                    - Analyseer de progressie van de chronische trainingsbelasting (CTL-equivalent) en acute belasting (ATL-equivalent).
                    - Beoordeel of de gerealiseerde overload voldoet aan de principes van supercompensatie.
                    """
                if focus_efficiency:
                    opdracht_secties += """
                    2. METABOLE EN MECHANISCHE EFFICIËNTIE (EFFICIENCY FACTOR & DECOUPLING)
                    - Onderzoek trends in de verhouding tussen input (hartslag) en output (vermogen/tempo) tijdens aerobe submaximale trainingen.
                    - Identificeer patronen van aerobe ontkoppeling (Pw:Hr of Pa:Hr > 5%) in langere submaximale sessies.
                    """
                if focus_pd_curve:
                    opdracht_secties += """
                    3. POWER-DURATION PROFIEL & FENOTYPERING
                    - Analyseer piekvermogens over relevante tijdsdomeinen (bv. 5s, 1min, 5min, 20min) aanwezig in de dataset.
                    - Welke energiesystemen zijn primair geprikkeld en hoe hebben deze zich ontwikkeld?
                    """
                if focus_fatigue:
                    opdracht_secties += """
                    4. MALADAPTATIE EN ACUTE RISICO-ANALYSE
                    - Screen de data op indicatoren van Non-Functional Overreaching (NFOR) of chronische vermoeidheid.
                    - Identificeer acute belastingspieken (acute-to-chronic workload ratio rondslingerend buiten de 0.8 - 1.3 zone).
                    """

                # De aangescherpte expert prompt
                # De aangescherpte, no-nonsense expert prompt
                prompt = f"""
                Je bent een high-performance sportwetenschappelijk analist. Je ondersteunt een professionele duursportcoach. 
                Praat op gelijke hoogte met een topcoach: direct, kritisch en uitsluitend gefocust op bruikbare performance-inzichten. 
                Vermijd academisch gezever, passieve zinnen of theoretische definities (leg NIET uit wat TSS, CTL of ontkoppeling is, de coach weet dit).

                SPECIFIEKE ATLEET-FYSIOLOGIE & METRICS:
                {extra_context if extra_context else "Geen aanvullende parameters opgegeven."}

                TRAININGSDATA (CSV):
                {training_data}

                OPDRACHT:
                Analyseer de dataset vlijmscherp. Schrijf een klinisch, datagedreven Coach Rapport in helder, direct Nederlands. 
                Focus uitsluitend op de geselecteerde sportwetenschappelijke lenzen:

                {opdracht_secties}

                ANALYSEREGELS VOOR HIGH-PERFORMANCE:
                - **Kom direct ter zake:** Geen inleidende zinnen zoals "Na analyse van de data blijkt...". Start meteen met het harde inzicht.
                - **Harde datakoppeling:** Elke trend of conclusie *moet* direct onderbouwd worden met exacte datums, vermogenswaardes, hartslagen of TSS-scores tussen haakjes.
                - **Geen aannames:** Onderscheid gerealiseerde prestatie (MMP) strikt van fysiologische adaptatie. Wees kritisch op de effectiviteit van de load.
                - **Actiegericht:** Vertaal de trends naar concrete conclusies waar de coach morgen mee aan de slag kan in het trainingsschema.

                OUTPUT FORMAT:
                Lever uitsluitend het rapport op in strakke, rauwe Markdown. Gebruik korte, krachtige alinea's en bulletpoints. 
                Start direct met een 'EXECUTIVE SUMMARY' (maximaal 4 bullets met de meest kritieke trends). 
                Geen beleefdheidsfrasen, geen academische conclusies vooraf of achteraf. Alleen de harde feiten.
                """

                # MULTI-MODEL API INTEGRATIE
                try:
                    if model_provider == "Google Gemini":
                        client = genai.Client(api_key=api_key)
                        response = client.models.generate_content(
                            model=selected_model,
                            contents=prompt,
                        )
                        st.session_state['rapport'] = response.text

                    elif model_provider == "Anthropic Claude":
                        client = anthropic.Anthropic(api_key=api_key)
                        response = client.messages.create(
                            model=selected_model,
                            max_tokens=4000,
                            system="Je bent een expert in sportwetenschap en data-analyse voor professionele duursport.",
                            messages=[{"role": "user", "content": prompt}]
                        )
                        st.session_state['rapport'] = response.content.text

                except Exception as api_error:
                    st.error(f"Fout tijdens de AI-analyse: {api_error}")

    except Exception as e:
        st.error(f"Fout bij het verwerken van het bestand: {e}")

# ==============================================================================
# 5. WEERGAVE RAPPORT & JOUW KOGELVRIJE PRINT EXPORT
# ==============================================================================
# VERVANG REGEL 147:
if 'rapport' in st.session_state and st.session_state['rapport'] is not None:
    st.subheader(f"📋 AI Coach Rapport ({model_provider})")
    st.markdown(st.session_state['rapport'])

    st.write("---")
    st.subheader("📥 Export Opties")

    ruwe_tekst = st.session_state['rapport']

    # JOUW SLIMME BOLD-REM LOGICA
    parts = ruwe_tekst.split('**')
    for i in range(1, len(parts), 2):
        if len(parts[i].split()) > 4:
            parts[i] = parts[i]
        else:
            parts[i] = f"||B||{parts[i]}||/B||"

    ruwe_tekst = "".join(parts)
    ruwe_tekst = ruwe_tekst.replace('*', '').replace('_', '')

    lines = ruwe_tekst.split('\n')
    html_processed = []
    in_list = False

    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                html_processed.append("</ul>")
                in_list = False
            continue

        if line.startswith('#'):
            if in_list:
                html_processed.append("</ul>")
                in_list = False
            clean_title = line.replace('#', '').strip()
            if line.startswith('###'):
                html_processed.append(f"<h3>{clean_title}</h3>")
            elif line.startswith('##'):
                html_processed.append(f"<h2>{clean_title}</h2>")
            else:
                html_processed.append(f"<h1>{clean_title}</h1>")
        elif line.startswith(('1.', '2.', '3.', '4.')) and len(line) < 60:
            if in_list:
                html_processed.append("</ul>")
                in_list = False
            html_processed.append(f"<h2>{line}</h2>")
        elif line.startswith(('-', '*', '•')):
            if not in_list:
                html_processed.append("<ul>")
                in_list = True
            html_processed.append(f"<li>{line.lstrip('-*• ').strip()}</li>")
        else:
            if in_list:
                html_processed.append("</ul>")
                in_list = False
            html_processed.append(f"<p>{line}</p>")

    if in_list:
        html_processed.append("</ul>")

    html_content = "".join(html_processed)
    html_content = html_content.replace('||B||', '<b>').replace('||/B||', '</b>')

    # JOUW DESIGN-MATRIX (Let op: de sluitende """ staat nu perfect uitgelijnd)
    html_print_layout = f"""
    <html>
    <head>
        <title>Sportwetenschappelijk Rapport</title>
        <style>
            @import url('https://googleapis.com');

            body {{ 
                font-family: 'Inter', sans-serif; 
                line-height: 1.7; 
                color: #2D3748; 
                padding: 50px; 
                max-width: 850px; 
                margin: 0 auto;
                background-color: #FFFFFF;
                -webkit-print-color-adjust: exact;
            }}

            h1 {{ 
                color: #1A365D; 
                border-bottom: 2px solid #2B6CB0; 
                padding-bottom: 8px; 
                font-size: 20px; 
                font-weight: 700; 
                margin-top: 35px;
                margin-bottom: 15px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}

            h2 {{ 
                color: #2B6CB0; 
                margin-top: 25px; 
                font-size: 16px; 
                font-weight: 600;
                border-bottom: 1px solid #E2E8F0;
                padding-bottom: 4px;
            }}

            h3 {{ 
                color: #4A5568; 
                margin-top: 18px; 
                font-size: 14px; 
                font-weight: 600;
            }}

            p {{ 
                margin-bottom: 12px; 
                text-align: justify;
                font-size: 13.5px;
                font-weight: 400;
                color: #2D3748;
            }}

            b {{ 
                color: #1A202C; 
                font-weight: 600;
            }}

            ul {{ 
                margin-top: 5px; 
                margin-bottom: 12px; 
                padding-left: 20px; 
            }}

            li {{ 
                margin-bottom: 6px; 
                font-size: 13.5px;
                color: #2D3748;
                list-style-type: square;
            }}

            .meta-box {{ 
                background-color: #F7FAFC;
                border-left: 4px solid #1A365D;
                padding: 15px;
                margin-bottom: 30px;
                border-radius: 4px;
            }}

            .meta-title {{ font-size: 16px; font-weight: 700; color: #1A365D; margin: 0 0 5px 0; letter-spacing: 0.5px; }}
            .meta-sub {{ font-style: italic; color: #718096; margin: 0; font-size: 11px; }}

            @media print {{
                body {{ padding: 0; color: #000000; max-width: 100%; }}
                .meta-box {{ background-color: #FFFFFF; border: 1px solid #CBD5E0; }}
                h1, h2 {{ page-break-after: avoid; }}
            }}
        </style>
    </head>
    <body>
        <div class="meta-box">
            <div class="meta-title">🚴‍♂️ HIGH-PERFORMANCE COACH RAPPORT</div>
            <div class="meta-sub">Gegenereerd via AI Coach Assistent Dashboard</div>
        </div>
        <div>
            {html_content}
        </div>
        <script>
            window.onload = function() {{ window.print(); }}
        </script>
    </body>
    </html>
    """

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="🖨️ Exporteer als PDF (via Printvenster)",
            data=html_print_layout,
            file_name="Sportwetenschappelijk_Rapport.html",
            mime="text/html"
        )
    with col2:
        st.download_button(
            label="📝 Download als Tekstbestand (.txt)",
            data=st.session_state['rapport'],
            file_name="Sportwetenschappelijk_Rapport.txt",
            mime="text/plain"
        )


