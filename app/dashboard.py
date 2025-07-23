# ------------------ app/dashboard.py ------------------
import streamlit as st
import tempfile
import os
import pathlib, json
import pandas as pd

from modules.job_processing import search_and_process_jobs
from modules.utils import load_search_terms
from modules.render_jobs import render_job_results
from modules.history_tracker import LOG_PATH, update_application_status
from config.profile_loader import load_profile

from scrapers.registry import REGISTRY
from streamlit_option_menu import option_menu



@st.cache_data(show_spinner=True)
def do_job_search(
    platforms: list[str],
    locations: list[str],
    terms: list[str],
    hours_old: int,
    results_wanted: int,
    score_threshold: int,
    generate_cv: bool,
    generate_cl: bool,
    debug_mode: bool,
    easy_apply: bool
) -> list[dict]:
    all_matches = []
    idx = 0

    for platform in platforms:
        for location in locations:
            for term in terms:
                matches = search_and_process_jobs(
                    platform, term, location, hours_old, results_wanted,
                    score_threshold=score_threshold,
                    generate_cv=generate_cv,
                    generate_cl=generate_cl,
                    debug=debug_mode,
                    ea_application=easy_apply,
                )
                all_matches.extend(matches)
                idx += 1

    return all_matches


## THIS WILL BE THE MAIN DICTIONARY THAT WILL IMPLEMENT THE APP FUNCTIONALITIES ##
def run_dashboard():
################################    APP'S NAME     ################################
    st.set_page_config(layout="wide", page_title="Job Bot")
    
    PROFILE = load_profile()             # None if not created yet
    st.session_state["PROFILE"] = PROFILE
    
    # 1) Sticky top menu CSS
    st.markdown("""
    <style>
      .block-container {
        padding-top: 3rem !important;
      }
    
      .streamlit-option-menu {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
      }
    
      .streamlit-option-menu .nav {
        margin: 0 !important;
        padding: 0 !important;
      }
      .streamlit-option-menu .nav-link {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
      }
    
      .css-1v3fvcr h1 {
        margin-top: 0.5rem !important;
      }
    </style>
    """, unsafe_allow_html=True)
    
    # 2) Horizontal option_menu
    with st.container():
        st.markdown('<div class="top-nav">', unsafe_allow_html=True)
        selected = option_menu(
            menu_title=None,
            options=["Home","Search","Results","History","Manual Job Entry"],
            icons=["house","search","table","envelope","clock-history","gear"],
            default_index=1,
            orientation="horizontal",
            styles={
                "container": {"padding":"0!important","background-color":"#111"},
                "icon": {"color":"white","font-size":"20px"},
                "nav-link": {
                    "font-size":"16px","margin":"0 1rem",
                    "--hover-color":"#333",
                    "color":"white","padding":"0.25rem 0.75rem"
                },
                "nav-link-selected": {"background-color":"#ff4b4b","color":"white"},
            }
        )
        st.markdown('</div>', unsafe_allow_html=True)
    

    # ---------- 1) HOME ------------------
    if selected == "Home":
        st.title("🏠 Job Bot – Profile")
        PROFILE_PATH = pathlib.Path("config/profile.json")
        if st.session_state["PROFILE"] is None:
            st.info("No profile found. Fill in the form once; the app will remember it.")
    
            with st.form("profile_setup"):
                name       = st.text_input("Full name")
                background = st.text_area("Background (1-2 lines)")
                skills_txt = st.text_input("Key skills (comma-separated)")
                experience = st.text_input("Experiences described in a few sentences (comma-separated)")
                objective  = st.text_input("Career objective")
                submitted  = st.form_submit_button("Save profile")
            
            if submitted:
                PROFILE_PATH.parent.mkdir(exist_ok=True)
                with open(PROFILE_PATH, "w", encoding="utf-8") as fh:
                    json.dump(
                        {
                            "name": name,
                            "background": background,
                            "skills": [s.strip() for s in skills_txt.split(",") if s.strip()],
                            "experience_bullets": [s.strip() for s in experience.split(",") if s.strip()],
                            "objective": objective,
                        },
                        fh,
                        ensure_ascii=False,
                        indent=2,
                    )
                st.success("Profile saved! Reloading …")
                st.rerun()              
    
        else:
            prof = st.session_state["PROFILE"]
            st.markdown(f"**Name:** {prof['name']}")
            st.markdown(f"**Background:** {prof['background']}")
            st.markdown(f"**Skills:** {', '.join(prof['skills'])}")
            st.markdown(f"**Experiences:** {', '.join(prof['experience_bullets'])}")
            st.markdown(f"**Objective:** {prof['objective']}")
    
            if st.button("Edit profile"):
                pathlib.Path("config/profile.json").unlink(missing_ok=True)
                st.rerun()
    
    # ---------- 1) SEARCH TAB ------------
    elif selected == "Search":
        st.header("🔍 Configure Your Job Search")
        if st.session_state["PROFILE"] is None:
            return st.warning("Create your profile in the **Home** tab first.")

## HERE, SELECT THE LLM MODEL TO USE (LOCAL OR API) ##
        if "search_terms" not in st.session_state:
            st.session_state["search_terms"] = []
        
       # --- LLM engine & key -------------------------------------------------
        default_backend = "Ollama (local Llama3-8B)"
        use_api = st.selectbox(
            "​Choose LLM engine:",
            [default_backend, "OpenAI API (gpt-3.5-turbo)"],
            index=0 if os.getenv("LLM_BACKEND", "ollama") == "ollama" else 1,
        )
        
        if use_api.startswith("OpenAI"):
            os.environ["LLM_BACKEND"] = "openai"
        
            # 1) Try env / .env / Streamlit secrets first
            api_key = (
                os.getenv("OPENAI_API_KEY")                # exported in shell
                or st.secrets.get("OPENAI_API_KEY", "")    # ~/.streamlit/secrets.toml
            )
        
            # 2) Fallback → ask the user *only if* we still have nothing
            if not api_key:
                api_key = st.text_input("OpenAI API key", type="password")
        
            if not api_key:
                st.error("Please set OPENAI_API_KEY in your env or paste it above.")
                st.stop()
        
            # Write it back only if non-empty, so we never blank-out the env var
            os.environ["OPENAI_API_KEY"] = api_key
            st.success("OpenAI key loaded ✓")
        
        else:
            os.environ["LLM_BACKEND"] = "ollama"

        
## HERE, WE IMPORT THE KEYWORDS FOR THE FUTURE SCRAPING ON THE PLATFORMS ##       
        st.markdown("### Keywords")
        
        col1, col2 = st.columns(2)
        
        # A)  File uploader (unchanged)
        with col1:
            uploaded_file = st.file_uploader("Upload .txt", type="txt")
        
        # B)  Manual input
        with col2:
            manual_kw = st.text_area("…or type keywords (comma-separated) (CTRL + Enter to apply)")
        
        # Merge the two sources
        search_terms = st.session_state.get("search_terms", [])
        
        if uploaded_file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
                tmp.write(uploaded_file.read())
                search_terms = load_search_terms(tmp.name)
        
        # Append manual keywords (if any)
        if manual_kw.strip():
            manual_list = [k.strip() for k in manual_kw.split(",") if k.strip()]
            # Merge while preserving order & uniqueness
            search_terms = list(dict.fromkeys(search_terms + manual_list))
        
        # Persist so the tab remembers them
        st.session_state["search_terms"] = search_terms
        
        if search_terms:
            st.markdown("##### Review keywords")
        
            # Multiselect shows current list; unchecking deletes entries
            kept = st.multiselect(
                "Active keywords",
                options=search_terms,
                default=search_terms,
                key="kw_review_box",
            )
            # Update state if user changed the list
            if set(kept) != set(search_terms):
                search_terms = kept
                st.session_state["search_terms"] = kept
        
            # Clear-all button
            if st.button("🗑️ Clear all keywords"):
                st.session_state.pop("kw_review_box", None)   # forget multiselect choices
                st.session_state["search_terms"] = []
                st.rerun()
        else:
            st.info("Upload a .txt file **or** enter keywords manually, then review them here.")

## HERE, WE MAKE A MULTIPLE CHOICE FOR THE LOCATIONS THAT WE WANT TO SCRAPE ##
        available_locations = [
            "France", "Germany", "Spain", "Italy", "Netherlands", "Australia",
            "USA", "UK", "Sweden", "Denmark", "Switzerland", "Luxembourg"
        ]
        locations = st.multiselect("Select Locations", available_locations, default=["France"])
        
## HERE, WE MAKE A MULTIPLE CHOICE FOR THE PLATFORMS THAT WE WANT TO SCRAPE ##
        available_platforms = list(REGISTRY.keys())      
        label_map = {
    	    "indeedapi":    "Indeed (API)",
    	    "linkedin":      "Linkedin (Browser)",
    	}
    	
        display_names = [label_map.get(k, k) for k in available_platforms]
        job_sites_readable = st.multiselect(
            "Select Platforms",
            options=display_names,
            default=["Indeed (API)"],
        )
        
        easy_apply = False
        for platform in job_sites_readable:
            if platform == 'Linkedin (Browser)':
                choice = st.radio(
                    "**Normal jobs** or **Easy Apply** jobs?",
                    ["***Normal jobs***", "***Easy Apply***"]
                )
        
                if choice == "***Easy Apply***":
                    easy_apply = True
                
        st.markdown("---")
        job_sites = [k for k, v in label_map.items() if v in job_sites_readable]

## WE IMPLEMENT DIFFERENT SLIDERS TO LET THE USER CHOSE THE AMOUNT OF : RESULTS / ##
## MINIMUM SCORE A JOB HAS TO HAVE / HOW OLD IS THE OFFER ##
        results_wanted = st.slider("Results per search term", 1, 25, 10)
        score_threshold = st.slider("Match Score Threshold", 0, 10, 7)
        days_old = st.slider("Max job age (in days)", 1, 30, 10)

## WE LET THE USER CHOSE RATHER IT WANTS OR NOT TO GENERATE THE TAILORED DOCUMENTS FOR THE JOB / ##
## SHOW THE REASONING OF THE LLM DURING ITS TAILORING ##
        st.markdown("---")
        gen_cv = st.checkbox("Generate Tailored CVs", value=True)
        gen_cl = st.checkbox("Generate Cover Letters", value=True)
        debug_mode = st.checkbox(
            "Show LLM reasoning and prompts",
            key="show_llm_prompts",          # store in session_state
            value=st.session_state.get("show_llm_prompts", False)
        )

## WE RUN THE JOB SEARCH ##
        run_button = st.button("🔍 Start Job Search")
        if run_button:
            if not search_terms:
                st.error("Please upload a valid keywords .txt file.")
            else:
                # Call the cached function
                hours_old = days_old * 24
                matches = do_job_search(
                    job_sites,
                    locations,
                    search_terms,
                    hours_old,
                    results_wanted,
                    score_threshold,
                    gen_cv,
                    gen_cl,
                    debug_mode,
                    easy_apply
                )
                # Store results and jump to the Results tab
                st.session_state["all_matches"] = matches
                st.rerun()
      
    # --- 2) RESULTS TAB ---
    elif selected == "Results":
        st.header("📋 Search Results")
        if st.session_state["PROFILE"] is None:
            return st.warning("Create your profile in the **Home** tab first.")
        
        saved = st.session_state.get("all_matches", None)
        if saved is None:
            st.info("Run a search first …")
        else:
            st.success(f"✅ Found {len(saved)} job(s)!")
            render_job_results(saved, debug_mode=st.session_state.get("show_llm_prompts", False))       

   # ---------- 3) PAST APPLICATIONS TAB ----------
    elif selected == "History":
        st.header("Past applications")
        
        if st.session_state["PROFILE"] is None:
            return st.warning("Create your profile in the **Home** tab first.")
    
        if not LOG_PATH.exists():
            return st.info("You haven’t marked any applications yet.")
    
        raw = json.loads(LOG_PATH.read_text(encoding="utf-8"))
    
        # Legacy format → normalize to list of dicts
        if raw and isinstance(raw[0], str):
            raw = [
                {
                    "url": u,
                    "title": "",
                    "company": "",
                    "location": "",
                    "platform": "",
                    "timestamp": None,
                    "status": "Applied"
                }
                for u in raw
            ]
    
        # Ensure every entry has all fields
        for entry in raw:
            entry.setdefault("title", "")
            entry.setdefault("company", "")
            entry.setdefault("location", "")
            entry.setdefault("platform", "")
            entry.setdefault("timestamp", None)
            entry.setdefault("status", "Applied")
    
        statuses = ["Applied", "Interviewing", "Offered", "Rejected"]
    
        # Header row
        cols = st.columns([2,2,1,1,1,1,1])
        for header, col in zip(
            ["Title","Company","Location","Platform","Timestamp","Status","Link"],
            cols
        ):
            col.markdown(f"**{header}**")
    
        # One row per application
        for i, entry in enumerate(raw):
            c0, c1, c2, c3, c4, c5, c6 = st.columns([2,2,1,1,1,1,1])
            c0.write(entry["title"])
            c1.write(entry["company"])
            c2.write(entry["location"])
            c3.write(entry["platform"])
            c4.write(entry["timestamp"] or "—")
    
            # Status dropdown
            current = entry["status"]
            new_status = c5.selectbox(
                "Status",
                statuses,
                index=statuses.index(current),
                key=f"hist_status_{i}"
            )
            if new_status != current:
                update_application_status(entry["url"], new_status)
                st.rerun()
    
            # Clickable link
            c6.markdown(f"[View job]({entry['url']})", unsafe_allow_html=True)
    
        # CSV download of the raw data
        df = pd.DataFrame(raw)
        st.download_button(
            "⬇️ Download full history as CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="past_applications.csv",
            mime="text/csv"
        )
        
    # ---------- 4) Manual Job Entry ----------
    elif selected == "Manual Job Entry":
        from modules.utils import extract_keywords, sanitize_filename
        from modules.cv_generator import insert_keywords_into_doc, convert_to_pdf_libreoffice
        from modules.cl_generator import generate_cover_letter, save_to_pdf
        
        BASE_CV_PATH_EN = "assets/templates/template_cv.docx"
        
        if "manual_inputs" not in st.session_state:
            st.session_state.manual_inputs = {
                "title": "",
                "company": "",
                "location": "",
                "description": "",
                "folder": "",
                "generated": False
            }

        st.header("Manual Job Entry")
        
        if st.session_state["PROFILE"] is None:
            return st.warning("Create your profile in the **Home** tab first.")
        
        st.text_input("Job Title", key="manual_title")
        st.text_input("Company Name", key="manual_company")
        st.text_input("Location", key="manual_location")
        st.text_area("Job Description", key="manual_description", height=200)
    
        if st.button("Generate CV & Cover Letter"):
            title = st.session_state.manual_title.strip()
            company = st.session_state.manual_company.strip()
            location = st.session_state.manual_location.strip()
            description = st.session_state.manual_description.strip()
    
            if not (title and company and location and description):
                st.error("Please complete all fields.")
            else:
                template_cv = BASE_CV_PATH_EN
                keywords = extract_keywords(description, debug=False)
                
                folder = os.path.join("results", sanitize_filename(f"{title}_{company}"))
                os.makedirs(folder, exist_ok=True)
    
                # Generate CV
                cv_path = os.path.join(folder, "CV_Custom.docx")
                insert_keywords_into_doc(template_cv, keywords, cv_path)
                convert_to_pdf_libreoffice(cv_path, folder)
    
                # Generate Cover Letter
                cl_doc = generate_cover_letter(title, company, location)
                save_to_pdf({}, cl_doc, folder)
    
                # Save all values in session
                st.session_state.manual_inputs.update({
                    "title": title,
                    "company": company,
                    "location": location,
                    "description": description,
                    "folder": folder,
                    "generated": True
                })
    
                st.success("Documents generated and saved!")
    
        # Use the stored session state to show results even after rerun
        if st.session_state.manual_inputs["generated"]:
            folder = st.session_state.manual_inputs["folder"]
            pdf_cv = os.path.join(folder, "CV_Custom.pdf")
            pdf_cl = os.path.join(folder, "Cover_Letter.pdf")
    
            st.markdown(f"Output Folder: `{folder}`")
    
            if os.path.exists(pdf_cv):
                with open(pdf_cv, "rb") as f:
                    st.download_button("Download CV", f, file_name="CV_Custom.pdf", key="cv_dl")
    
            if os.path.exists(pdf_cl):
                with open(pdf_cl, "rb") as f:
                    st.download_button("Download Cover Letter", f, file_name="Cover_Letter.pdf", key="cl_dl")
    
            if st.button("Restart Manual Entry"):
                for key in ("manual_title", "manual_company",
                            "manual_location", "manual_description"):
                    st.session_state.pop(key, None)     
                st.session_state.manual_inputs = {      # clear meta-data
                    "title": "", "company": "", "location": "",
                    "description": "", "folder": "", "generated": False
                }
                st.rerun()
