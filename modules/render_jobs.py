# ------------------ modules/render_jobs.py ------------------
import streamlit as st
import pandas as pd
import tempfile
import os
import datetime
from modules.email_sender import send_application_email
from config.profile_loader import load_profile
from modules.history_tracker import has_already_applied, log_application

PROFILE = load_profile()
def render_job_results(all_matches, debug_mode):
    results_df = pd.DataFrame(all_matches)

    for idx, job in enumerate(all_matches):
        applied = has_already_applied(job["url"])
        
        st.markdown(f"**{job['title']}** at **{job['company']}**  ")
        st.markdown(f"\U0001F4CD Location: {job['location']}")
        st.markdown(f"🌐 Platform: {job['platform']}")
        st.markdown(f"🌐 Url: {job['url']}")
        st.markdown(f"🌐 Email (if available): {job['email']}")
        st.markdown(f"\U0001F4C1 Folder: `{job['folder']}`")
        st.markdown(f"\u2B50 Match Score: {job.get('score', 'N/A')}/10")

        if st.button("(Re)generate Cover Letter", key=f"regen_en_{idx}"):
            from modules.cl_generator import generate_cover_letter, save_to_pdf
        
            new_letter = generate_cover_letter(
                job["title"],
                job["company"],
                job["location"],
            )
            if new_letter:
                save_to_pdf(job, new_letter, job["folder"])
                st.success("Regenerated CL in English")
                st.rerun()           
        
        if applied:
            st.success("Already marked as applied")
        else:
            if st.button("Mark as Applied", key=f"mark_applied_{idx}"):
                log_application(
                    url=job["url"],
                    title=job["title"],
                    company=job["company"],
                    location=job["location"],
                    platform=job["platform"],
                )
                st.success("Marked as applied")
                st.rerun()
        
        email_val = job.get("email", "")
        if email_val and not pd.isna(email_val) and str(email_val).strip().lower() != "nan":
            emails = [e.strip() for e in str(email_val).replace(";", ",").split(",") if e.strip()]
            if len(emails) > 1:
                st.markdown("Multiple Emails Found")
                selected_email = st.selectbox("Choose email address to send to:", emails, key=f"email_select_{idx}")
            else:
                selected_email = emails[0]
            
            st.markdown("### 📤 Manual Send Options")
            sent_key = f"sent_{job['title']}_{job['company']}_{idx}"
            sent = st.session_state.get(sent_key)
            if sent:
                st.success(f"Sent to {sent['email']} on {sent['timestamp']}")
            else:
                clicked = st.button("Send selected applications", key=f"send_btn_{idx}")
                if clicked:
                    
                    with st.spinner("Sending..."):
                        
                        candidate_name = PROFILE.get("name", "Your Name")
                        from_address = st.session_state.get("from_address", "")
                        app_password = st.session_state.get("app_password", "")
                        smtp_server = st.session_state.get("smtp_server", "")
                        smtp_port = int(st.session_state.get("smtp_port", 587))
                        
                        if not (from_address and app_password and smtp_server and smtp_port):
                            st.error("Please enter your SMTP credentials in the sidebar before sending.")
                        else:
            
                            attachments = [
                                os.path.join(job['folder'], 'CV_Custom.pdf'),
                                os.path.join(job['folder'], 'Cover_Letter.pdf'),
                            ]
                            
                            missing = [p for p in attachments if not os.path.isfile(p)]
                            if missing:
                                st.error(f"Missing {', '.join(os.path.basename(m) for m in missing)} for {job['title']}")
                            
                            else:
                                try:
                                    
                                    success, status = send_application_email(
                                        to_address=selected_email,
                                        subject=f"Application: {job['title']} at {job['company']}",
                                        body_text=(
                                            "Dear Hiring Team,\n\n"
                                            "Please find attached my CV and cover letter for your review.\n\n"
                                            f"Best regards,\n{candidate_name}"
                                        ),
                                        attachments=attachments,
                                        from_address=from_address,
                                        app_password=app_password,
                                        smtp_server=smtp_server,
                                        smtp_port=smtp_port,
                                    )
                                    
                                    if success:
                                        st.session_state[sent_key] = {
                                            "email": selected_email,
                                            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                            "status": status   # you can also save the status if you want
                                        }
                                        st.rerun()
                                        # st.success(f"{job['title']} → Sent ({status})")
                                    else:
                                        st.error(f"{job['title']} → Failed ({status})")
                                except Exception as e:
                                    st.error(f"❌ Error sending {job['title']}: {e}")  
            
        else:
            st.markdown("📤 No Manual Send Option Available (no email found)")                                                                                                                                                                  
        st.markdown("---")                                                

    
    csv_path = os.path.join(tempfile.gettempdir(), "job_results.csv")
    results_df.to_csv(csv_path, index=False)
    with open(csv_path, "rb") as f:
        st.download_button("\U0001F4E5 Download Results CSV", data=f, file_name="job_results.csv", mime="text/csv")

