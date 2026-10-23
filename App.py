import streamlit as st
import pandas as pd
import google.genai as genai

st.set_page_config(page_title="Gratis AI Coach Assistent v4.1", layout="wide")
st.title("🚴‍♂️ 100% Gratis AI Coach Dashboard (Stabiele v4.1)")
st.write("Analyseer TrainingPeaks-data zonder limieten via de gratis Google Gemini API.")

api_key = st.sidebar.text_input("Vul je Google Gemini API Key in:", type="password")

if not api_key:
    st.info("💡 Ga naar ://google.com, maak een gratis sleutel aan en vul hem in de zijbalk in om te starten.")
else:
    client = genai.Client(api_key=api_key)

    uploaded_file = st.file_uploader("Upload je TrainingPeaks 'Workout Summary' CSV-bestand:", type=["csv"])

    st.subheader("✍️ Voeg Coach Context toe")
    context_tekst = st.text_area(
        "Specifieke context (blessures, doelen, herstart):",
        "In deze periode presteerde deze atleet het beste vorig seizoen. Welke zaken zijn hieruit het belangrijkst om mee te nemen naar komend seizoen, en met welke zaken moet ik veel rekening houden? Inmiddels is deze atleet sinds gisteren aan zijn voorbereiding begonnen richting 2027. Let op: de hoogtestage liep tot 14 augustus. Trainingen vanaf 4 augustus tot en met die datum vonden plaats OP hoogte. Zorg dat je de datums in de tabel strikt chronologisch interpreteert (8 en 12 augustus vallen BINNEN de hoogtestage, niet erna)."
    )

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            df.columns = df.columns.str.strip().str.lower()
            st.success(f"Data succesvol geladen! {len(df)} trainingen gevonden.")
            st.dataframe(df.head(10))

            if st.button("🚀 Start Betrouwbare Sportwetenschappelijke Analyse"):
                with st.spinner("Gemini herbeerekent de data..."):
                    training_data = df.to_string(index=False)

                    prompt = f"""
                    Je bent vanaf nu mijn sportwetenschappelijke Assistent Coach. Ik ben een menselijke wielertrainer. 
                    Jouw doel is om patronen te filteren uit de trainingsdata en mij te ontlasten als analist.

                    CONTEXT VAN DE ATLEET:
                    {context_tekst}

                    HIER IS DE TRAININGS_DATA IN CSV-FORMAAT:
                    {training_data}

                    OPDRACHT:
                    Analyseer de data en schrijf een beknopt, professioneel 'Coach Rapport' in duidelijke taal. Use clean text markdown, bolding, and sections.
                    LET OP DE TIJDLIJN: De trainingen van 8 en 12 augustus vonden plaats TIJDENS de hoogtestage. Analyseer de impact hiervan.

                    1. Chronologische Succes-Analyse: Hoe bouwde de vorm zich op TIJDENS de hoogtestage (tot 14 aug) en wat veranderde er fysiologisch in de weken DAARNA richting de winst op 13 september?
                    2. Strategische KPI's voor 2027: Welke specifieke trainingsprikkels, volumes (TSS) of vermogenspatronen uit de succesvolle weken moeten we kopiëren naar het nieuwe seizoen?
                    3. Valkuilen & Risico's: Waar moeten we komend seizoen strikt op monitoren (denk aan de hittegevoeligheid en de neuromusculaire krampen) om uitval te voorkomen?

                    Spreek me aan als een kritische, professionele sportwetenschapper. Sla beleefdheidsflosjes over en ga direct naar de kern.
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

                       # KOGELVRIJE HTML-PRINT TRUC VOOR PERFECTE PDF'S (VERBETERDE LAY-OUT)
            if 'rapport' in st.session_state:
                st.write("---")
                st.subheader("📥 Export Opties")
                
                # Slimme conversie: we zetten markdown koppen, bolding en lijsten om naar nette HTML
                html_content = st.session_state['rapport']
                html_content = html_content.replace('\n', '<br/>')
                html_content = html_content.replace('### ', '<h3>').replace(' ###', '</h3>') # Mocht Gemini ### gebruiken
                html_content = html_content.replace('**', '<b>', 1).replace('**', '</b>', 1)
                
                # Loop om alle overige ** sterretjes netjes om te zetten naar dikgedrukte HTML
                while '**' in html_content:
                    html_content = html_content.replace('**', '<b>', 1).replace('**', '</b>', 1)
                
                html_print_layout = f"""
                <html>
                <head>
                    <title>Sportwetenschappelijk Rapport 2027</title>
                    <style>
                        body {{ font-family: 'Segoe UI', Helvetica, Arial, sans-serif; line-height: 1.7; color: #2d3748; padding: 50px; max-width: 850px; margin: 0 auto; }}
                        h1 {{ color: #1a365d; border-bottom: 3px solid #3182ce; padding-bottom: 12px; font-size: 26px; font-weight: 700; margin-bottom: 20px; }}
                        h2 {{ color: #2b6cb0; margin-top: 35px; font-size: 18px; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px; }}
                        h3 {{ color: #4a5568; margin-top: 20px; font-size: 15px; }}
                        b {{ color: #1a202c; }}
                        .meta {{ font-style: italic; color: #718096; margin-bottom: 30px; font-size: 14px; }}
                        @media print {{
                            body {{ padding: 0; color: #000; max-width: 100%; }}
                            h1 {{ border-bottom: 3px solid #000; }}
                            h2 {{ border-bottom: 1px solid #000; }}
                        }}
                    </style>
                </head>
                <body>
                    <h1>🚴‍♂️ Sportwetenschappelijk Coach Rapport - Wederopbouw 2027</h1>
                    <div class="meta">Gegenereerd door AI Coach Assistent Dashboard | Datum: 23 oktober 2026</div>
                    <div style="margin-top: 10px;">
                        {html_content}
                    </div>
                    <script>
                        window.onload = function() {{ window.print(); }}
                    </script>
                </body>
                </html>
                """
                
                # Maak twee mooie kolommen naast elkaar voor de knoppen
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="🖨️ Exporteer als PDF (via Printvenster)",
                        data=html_print_layout,
                        file_name="Sportwetenschappelijk_Rapport_2027.html",
                        mime="text/html"
                    )
                with col2:
                    st.download_button(
                        label="📝 Download als Tekstbestand (.txt)",
                        data=st.session_state['rapport'],
                        file_name="Sportwetenschappelijk_Rapport_2027.txt",
                        mime="text/plain"
                    )


        except Exception as e:
            st.error(f"Fout bij het inlezen van het CSV-bestand: {e}")
