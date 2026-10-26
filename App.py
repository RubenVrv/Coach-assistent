import streamlit as st
import pandas as pd
import google.genai as genai

st.set_page_config(page_title="Gratis AI Coach Assistent v4.1", layout="wide")
st.title("🚴‍♂️ AI Coach Dashboard")
st.write("Analyseer TrainingPeaks-data")

api_key = st.sidebar.text_input("Vul je Google Gemini API Key in:", type="password")

if not api_key:
    st.info("💡 Ga naar ://google.com, maak een gratis sleutel aan en vul hem in de zijbalk in om te starten.")
else:
    client = genai.Client(api_key=api_key)

    uploaded_file = st.file_uploader("Upload je TrainingPeaks 'Workout Summary' CSV-bestand:", type=["csv"])

    st.subheader("✍️ Voeg Coach Context toe")
    context_tekst = st.text_area(
        "Specifieke context (blessures, doelen, herstart):",
        ""
    )

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip().str.lower()
            st.success(f"Data succesvol geladen! {len(df)} trainingen gevonden.")
            st.dataframe(df.head(10))

            if st.button("🚀 Start Analyse"):
                with st.spinner("Uw AI assistent berekent de data..."):
                    training_data = df.to_string(index=False)

                    prompt = f"""
                    Je bent mijn sportwetenschappelijke assistent-analist. Ik ben de menselijke
                    duursportcoach en gebruik jou om patronen in trainingsdata te identificeren
                    en onderbouwde inzichten te verkrijgen voor toekomstige trainingsbeslissingen.

                    CONTEXT VAN DE ATLEET:
                    {context_tekst}

                    TRAININGSDATA (CSV):
                    {training_data}

                    OPDRACHT:
                    Analyseer de data en schrijf een beknopt, professioneel Coach Rapport in
                    duidelijk Nederlands. Gebruik de meetgegevens als primaire bron en comments
                    uitsluitend als aanvullende context.

                    1. CHRONOLOGISCHE PRESTATIEANALYSE
                    - Reconstrueer de tijdlijn en identificeer belangrijke trainingsblokken,
                     veranderingen in belasting, herstelperiodes en piekprestaties.
                    - Welke trainingspatronen gingen vooraf aan sterke of zwakke prestaties?
                    - Welke veranderingen in de observeerbare prestatie zijn aantoonbaar?
                     Onderscheid deze van mogelijke fysiologische verklaringen.

                    2. STRATEGISCHE KPI'S VOOR VOLGEND SEIZOEN
                    - Welke trainingsprikkels, volumes, TSS-waarden, intensiteitsverdelingen
                    of vermogenspatronen verdienen herhaling of verder onderzoek?
                    - Formuleer maximaal vijf concrete prioriteiten met datagedreven onderbouwing
                     en relevante indicatoren om ze op te volgen.
                    - Beschouw samenhang niet automatisch als causaliteit en neem niet zomaar
                     aan dat een succesvolle trainingsweek ook optimaal was.

                    3. VALKUILEN EN RISICO'S
                    - Identificeer patronen die mogelijk samenhangen met prestatieverlies,
                     onderbroken trainingsopbouw, DNF's of onvoldoende wedstrijdspecifieke
                     voorbereiding.
                    - Benoem concrete aanwijzingen, alternatieve verklaringen en wat de coach
                    preventief kan monitoren.
                    - Maak duidelijk welke risico's niet betrouwbaar beoordeeld kunnen worden
                      met de beschikbare data.

                    ANALYSEREGELS:
                    - Respecteer de chronologie en houd rekening met vertraging tussen
                      trainingsbelasting en mogelijke prestatieveranderingen.
                    - Onderbouw belangrijke conclusies met concrete waarden, datums en vergelijkingen.
                    - Verzin geen gegevens en benoem ontbrekende of onbetrouwbare data.
                    - Maak onderscheid tussen waarnemingen, hypotheses en onbewezen verklaringen.
                    - Trek geen fysiologische of medische conclusies die de data niet ondersteunen.
                    - Geef prioriteit aan relevante patronen boven een opsomming van losse trainingen.

                    OUTPUT:
                    Gebruik Markdown met duidelijke secties, vetgedrukte kerninzichten en een
                    korte executive summary. Schrijf kritisch, professioneel en direct.
                    Vermijd algemeenheden en herhaling. Lever uitsluitend het Coach Rapport op.
                    """

                    try:
                        response = client.models.generate_content(
                            model='gemini-3.8-flash',
                            contents=prompt,
                        )
                        rapport_tekst = response.text
                        st.session_state['rapport'] = rapport_tekst
                        st.subheader("📋 AI Coach Rapport")
                        st.markdown(rapport_tekst)
                    except Exception as e:
                        st.error(f"Er ging iets mis met de API-aanroep: {e}")

            # KOGELVRIJE EN GEREMDE PDF EXPORT (GEEN RANDOM DIKGEDRUKTE SNIPPETS MEER)
            if 'rapport' in st.session_state:
                st.write("---")
                st.subheader("📥 Export Opties")

                ruwe_tekst = st.session_state['rapport']

                # SLIMME BOLD-REM: We controleren of de dikgedrukte stukken niet te lang zijn
                parts = ruwe_tekst.split('**')
                for i in range(1, len(parts), 2):
                    # Als Gemini meer dan 4 woorden achter elkaar dikdrukt, resetten we het naar normale tekst
                    if len(parts[i].split()) > 4:
                        parts[i] = parts[i]  # Sla de opmaak voor dit lange stuk over
                    else:
                        # Alleen korte kerntermen krijgen de tijdelijke b-tag
                        parts[i] = f"||B||{parts[i]}||/B||"

                # Lijm de tekst weer aan elkaar en verwijder alle rondslingerende markdown-resten
                ruwe_tekst = "".join(parts)
                ruwe_tekst = ruwe_tekst.replace('*', '').replace('_', '')

                lines = ruwe_tekst.split('\n')
                html_processed = []
                in_list = False

                for line in lines:
                    line = line.strip()
                    if not line:
                        if in_list: html_processed.append("</ul>"); in_list = False
                        continue

                    # Titels filteren
                    if line.startswith('#'):
                        if in_list: html_processed.append("</ul>"); in_list = False
                        clean_title = line.replace('#', '').strip()
                        if line.startswith('###'):
                            html_processed.append(f"<h3>{clean_title}</h3>")
                        elif line.startswith('##'):
                            html_processed.append(f"<h2>{clean_title}</h2>")
                        else:
                            html_processed.append(f"<h1>{clean_title}</h1>")
                    elif line.startswith(('1.', '2.', '3.', '4.')) and len(line) < 60:
                        if in_list: html_processed.append("</ul>"); in_list = False
                        html_processed.append(f"<h2>{line}</h2>")
                    # Bulletpoints filteren
                    elif line.startswith(('-', '*', '•')):
                        if not in_list: html_processed.append("<ul>"); in_list = True
                        html_processed.append(f"<li>{line.lstrip('-*• ').strip()}</li>")
                    else:
                        if in_list: html_processed.append("</ul>"); in_list = False
                        html_processed.append(f"<p>{line}</p>")

                if in_list: html_processed.append("</ul>")

                html_content = "".join(html_processed)
                html_content = html_content.replace('||B||', '<b>').replace('||/B||', '</b>')

                # De strakke, rustige opmaak-matrix voor de printer
                html_print_layout = f"""
                <html>
                <head>
                    <title>Sportwetenschappelijk Rapport </title>
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

                        /* Subtiele, rustige bold styling */
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
                        <div class="meta-sub">Gegenereerd via AI Coach Assistent Dashboard </div>
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
                    st.download_button(label="🖨️ Exporteer als PDF (via Printvenster)", data=html_print_layout,
                                       file_name="Sportwetenschappelijk_Rapport_2027.html", mime="text/html")
                with col2:
                    st.download_button(label="📝 Download als Tekstbestand (.txt)", data=st.session_state['rapport'],
                                       file_name="Sportwetenschappelijk_Rapport_2027.txt", mime="text/plain")




        except Exception as e:
            st.error(f"Fout bij het inlezen van het CSV-bestand: {e}")
