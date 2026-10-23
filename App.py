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

            # Kogelvrije TXT downloadknop (werkt ALTIJD, onafhankelijk van Python-versie)
            if 'rapport' in st.session_state:
                st.write("---")
                st.subheader("📥 Export Opties")

                st.download_button(
                    label="📥 Download Rapport als PDF (.PDF)",
                    data=st.session_state['rapport'],
                    file_name="Sportwetenschappelijk_Rapport_2027.pdf",
                    mime="text/plain"
                )

        except Exception as e:
            st.error(f"Fout bij het inlezen van het CSV-bestand: {e}")
