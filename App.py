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
    selected_model = "gemini-4-hydrogen"
    if not api_key:
        st.info("💡 Maak een API-sleutel aan via Google AI Studio om te starten.")
else:
    api_key = st.sidebar.text_input("Vul je Anthropic Claude API Key in:", type="password")
    selected_model = "claude-3-5-sonnet-20241022"
    if not api_key:
        st.info("💡 Maak een API-sleutel aan via de Anthropic Console om te starten.")

# ==============================================================================
# 3. HOOFDSCHERM: INPUT & GRANULAIRE CONTEXT FILTERS
# ==============================================================================
uploaded_file = st.file_uploader("Upload je TrainingPeaks 'Workout Summary' CSV-bestand:", type=["csv"])

st.subheader("🎛️ Context & Objectiviteit Filters")
st.write("Selecteer welke subjectieve en contextuele bronnen de AI mag gebruiken:")

col1, col2 = st.columns(2)

with col1:
    gebruik_comments = st.checkbox(
        "Neem atleet-comments mee (tekstuele feedback)",
        value=False,
        help="Bevat vaak emotie of excuses, maar ook belangrijke context zoals ziekte of materiaalpech."
    )
    gebruik_rpe = st.checkbox(
        "Neem RPE-scores mee (Rate of Perceived Exertion)",
        value=True,
        help="Nuttig om interne belasting (sRPE) te vergelijken met externe belasting (Watt/TSS)."
    )
    gebruik_gevoel = st.checkbox(
        "Neem 'Feeling' / Gevoel-scores mee",
        value=False,
        help="De algemene gemoedstoestand of frisheid die de atleet aanklikt."
    )

with col2:
    gebruik_coach_context = st.checkbox(
        "Gebruik mijn ingevulde coach-context hieronder",
        value=True
    )
    strenge_data_check = st.checkbox(
        "Confronteer subjectieve input met harde data",
        value=True,
        help="Dwingt de AI om te checken of RPE, gevoel of comments wel kloppen met hartslag en vermogen."
    )
    negeer_outliers = st.checkbox(
        "Filter technische uitbijters (0-waardes & sensor-spikes)",
        value=True
    )

extra_context = st.text_area(
    "Aanvullende atleet-fysiologie & context (bv. drempelwaardes, blessurehistorie, specifieke doelen):",
    placeholder="Bv. FTP 320W, LTHR 172bpm. Let op: atleet klaagt snel over zware benen in week 2 van een blok."
)

# ==============================================================================
# 4. ANALYSE LOGICA & GRANULAIRE DATA-OPSCHONING
# ==============================================================================
if uploaded_file is not None and api_key:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip().str.lower()

        # HARD DATA-FILTER: Verwijder de uitgevinkte kolommen fysiek uit de dataset
        kolommen_te_verwijderen = []

        if not gebruik_comments:
            kolommen_te_verwijderen.extend(
                [col for col in df.columns if any(w in col for w in ['comment', 'description', 'note'])])
        if not gebruik_rpe:
            kolommen_te_verwijderen.extend([col for col in df.columns if 'rpe' in col])
        if not gebruik_gevoel:
            kolommen_te_verwijderen.extend([col for col in df.columns if 'feeling' in col or 'gevoel' in col])

        df_gefilterd = df.drop(columns=kolommen_te_verwijderen, errors='ignore')

        st.success(f"Data succesvol geladen! {len(df_gefilterd)} trainingen klaar voor analyse.")
        if kolommen_te_verwijderen:
            st.caption(f"🔒 Uitgesloten kolommen voor objectiviteit: {', '.join(set(kolommen_te_verwijderen))}")

        st.dataframe(df_gefilterd.head(5))

        if st.button("🚀 Start Analyse"):
            with st.spinner(f"Vitori's assistent ({model_provider}) analyseert de data..."):
                training_data = df_gefilterd.to_string(index=False)

                # Dynamische regels voor de AI op basis van de aangevinkte filters
                context_regels = ""

                if not any([gebruik_comments, gebruik_rpe, gebruik_gevoel]):
                    context_regels += "- **100% BLIND & OBJECTIEF:** Alle subjectieve data (comments, RPE, gevoel) is verwijderd. Baseer je conclusies UITSLUITEND op mechanische (wattage/tempo) en fysiologische (hartslag/TSS) meetwaarden.\n"
                else:
                    actieve_bronnen = []
                    if gebruik_comments: actieve_bronnen.append("tekstuele comments")
                    if gebruik_rpe: actieve_bronnen.append("RPE-scores")
                    if gebruik_gevoel: actieve_bronnen.append("gevoelsscores")
                    context_regels += f"- **TOEGESTANE SUBJECTIEVE DATA:** Je mag uitsluitend gebruikmaken van: {', '.join(actieve_bronnen)}. Andere subjectieve velden zijn bewust geblokkeerd.\n"

                if any([gebruik_comments, gebruik_rpe, gebruik_gevoel]) and strenge_data_check:
                    context_regels += "- **REALITY CHECK:** Vergelijk de toegestane subjectieve input actief met de harde fysiologische data. Wijs de coach er direct op als een hoge RPE, slecht gevoel of negatieve comment NIET strookt met de geleverde wattages of hartslagrespons (bv. normale Efficiency Factor of lage aerobe ontkoppeling).\n"

                if negeer_outliers:
                    context_regels += "- **DATA-HYGIËNE:** Negeer duidelijke meetfouten, onvolledige bestanden of sensor-spikes (zoals 0W gemiddeld bij een rit of onrealistische hartslagpieken).\n"

                actieve_coach_context = extra_context if (
                            gebruik_coach_context and extra_context) else "Geen coach-context meegegeven. Analyseer volledig blanco."

                # De aangescherpte, no-nonsense high-performance prompt
                prompt = f"""
                Je bent een high-performance sportwetenschappelijk analist. Je ondersteunt een professionele duursportcoach. 
                Praat op gelijke hoogte met een topcoach: direct, kritisch en uitsluitend gefocust op bruikbare performance-inzichten. 
                Vermijd academisch gezever of theoretische definities (leg NIET uit wat TSS, CTL of ontkoppeling is). Geef data in DD/MM/YYYY.
                COACH CONTEXT:
                {actieve_coach_context}

                OBJECTIVITEITS- & FILTERREGELS (STRIKT VOLGEN):
                {context_regels}

                TRAININGSDATA (CSV):
                {training_data}

                OPDRACHT:
                Analyseer de dataset vlijmscherp. Schrijf een klinisch, datagedreven Coach Rapport in helder, direct Nederlands.
                Focus op:
                1. **Belastingsopbouw & Respons:** Evalueer de chronische vs. acute belasting (CTL/ATL trends) en herstelratio's.
                2. **Metabole & Mechanische Efficiëntie:** Analyseer Efficiency Factor (EF) en aerobe ontkoppeling (Pw:Hr / Pa:Hr) in duurtrainingen.
                3. **Power-Duration & Energiesystemen:** Welke systemen zijn geprikkeld en welke verschuivingen zijn zichtbaar in piekvermogens?
                4. **Risico's & Valkuilen:** Signaleer indicatoren van maladaptatie, overreaching of een suboptimale intensiteitsverdeling.

                ANALYSEREGELS VOOR HIGH-PERFORMANCE:
                - **Kom direct ter zake:** Geen inleidende zinnen. Start meteen met het harde inzicht.
                - **Harde datakoppeling:** Elke trend of conclusie *moet* direct onderbouwd worden met exacte datums, vermogenswaardes, hartslagen of TSS-scores tussen haakjes.
                - **Actiegericht:** Vertaal de trends naar concrete conclusies waar de coach morgen mee aan de slag kan.

                OUTPUT FORMAT:
                Lever uitsluitend het rapport op in strakke Markdown. Gebruik korte, krachtige alinea's en bulletpoints. 
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
    st.subheader(f"📋 Vitori's AI Coach Rapport ({model_provider})")
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


