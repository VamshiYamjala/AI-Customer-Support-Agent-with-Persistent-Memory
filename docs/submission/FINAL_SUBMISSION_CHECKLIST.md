# HackwithHyderabad — Final Submission Checklist

**Submission Deadline:** 29 September 2026  
**Developer:** Vamshi Yamjala  
**Project:** AI Customer Support Agent with Persistent Memory (PayNest Support)  
**Live URL:** https://paynest-support-agent.onrender.com/  
**GitHub Repository:** https://github.com/VamshiYamjala/AI-Customer-Support-Agent-with-Persistent-Memory  

---

## 1. Directory of Generated Submission Assets

All submission materials are organized and ready for you to review and publish:

```
docs/submission/
├── TECHNICAL_ARTICLE.md          # Full technical article for Dev.to / Hashnode / Medium / LinkedIn
├── LINKEDIN_POST.md              # Long & Short LinkedIn post copy + hashtags
├── LINKEDIN_TAGGING_GUIDE.md     # Verified company tags & mention best practices
├── REDDIT_POST.md                # 3 Reddit titles, full & short posts, subreddit guide
├── HACKATHON_FEEDBACK.md         # Form feedback responses (Short & Detailed)
├── VIDEO_DEMO_SCRIPT.md          # 4-minute scene-by-scene script with timestamps & cursor actions
├── VIDEO_STORYBOARD.md           # Visual layouts & audio cues for all 9 scenes
├── VIDEO_RECORDING_GUIDE.md      # Voiceover script, OBS setup, editing workflow & QC checklist
└── FINAL_SUBMISSION_CHECKLIST.md # This complete step-by-step submission checklist

assets/social/
└── linkedin_project_graphic.jpg  # Generated 1200x627 px landscape announcement banner
```

---

## 2. Step-by-Step Submission Tasks for You

### Task 1: Record and Upload Demonstration Video (3–5 Minutes)
- [ ] Review `docs/submission/VIDEO_DEMO_SCRIPT.md` and `docs/submission/VIDEO_RECORDING_GUIDE.md`.
- [ ] Open the live application at https://paynest-support-agent.onrender.com/ (zoom browser to ~120%).
- [ ] Record the screen walkthrough using OBS, Loom, or Windows Clipchamp.
- [ ] Export as 1080p MP4.
- [ ] Upload to **YouTube** (set visibility to **Public** or **Unlisted**) or **Loom**.
- [ ] Copy the video URL: `________________________________________`

### Task 2: Publish LinkedIn Announcement Post
- [ ] Open LinkedIn and start a new post.
- [ ] Copy the post text from `docs/submission/LINKEDIN_POST.md` (choose Long or Short).
- [ ] Attach the banner image: `assets/social/linkedin_project_graphic.jpg`.
- [ ] (Optional) Tag verified pages like `@Groq` and `@Render` as guided in `LINKEDIN_TAGGING_GUIDE.md`.
- [ ] Publish the post.
- [ ] Click the "..." icon on your post, select "Copy link to post", and record the link: `________________________________________`

### Task 3: Publish Technical Article (Dev.to / Hashnode / Medium / LinkedIn Article)
- [ ] Open your preferred blogging platform (**Dev.to**, **Medium**, **Hashnode**, or click **Write an article** on LinkedIn).
- [ ] Copy the markdown from `docs/submission/TECHNICAL_ARTICLE.md`.
- [ ] Set cover image to `assets/social/linkedin_project_graphic.jpg`.
- [ ] Add tags: `#ai`, `#fastapi`, `#python`, `#webdev`, `#groq`.
- [ ] Publish the article.
- [ ] Copy the published article link: `________________________________________`

### Task 4: Publish Reddit Post / Community Showcase
- [ ] Review `docs/submission/REDDIT_POST.md`.
- [ ] Select an appropriate subreddit (e.g. `r/FastAPI`, `r/SideProject`, or `r/Python` on project showcase days).
- [ ] Post using one of the 3 title options and the formatted body.
- [ ] Copy the Reddit post link: `________________________________________`

### Task 5: Complete the Official HackwithHyderabad Submission Form
Fill in the form fields using the prepared materials:

1. **Project Name**:  
   `PayNest Support Agent — AI Customer Support Agent with Persistent Memory`
2. **Project Description**:  
   `A context-aware customer support assistant built with FastAPI, Groq LLM (openai/gpt-oss-20b), Hindsight Cloud, and SQLite. Features isolated customer memory banks, real-time Memory ON vs. OFF comparison, company knowledge grounding, and guardrails against unauthorized action claims.`
3. **Live Deployed URL**:  
   `https://paynest-support-agent.onrender.com/`
4. **GitHub Repository**:  
   `https://github.com/VamshiYamjala/AI-Customer-Support-Agent-with-Persistent-Memory`
5. **Video Demo Link**:  
   *(Insert link from Task 1)*
6. **LinkedIn Post Link**:  
   *(Insert link from Task 2)*
7. **Reddit Post Link / Article Link**:  
   *(Insert link from Task 3)*
8. **Hackathon Feedback**:  
   *(Copy text from `docs/submission/HACKATHON_FEEDBACK.md`)*

---

## 3. Final Pre-Submission Sanity Check

- [x] **No Secrets Exposed**: `.env`, API keys, and SQLite database files are strictly excluded from Git.
- [x] **Production Status**: Live service health check returns HTTP 200 `{"status":"ok","hindsight":"ok","llm":"ok"}`.
- [x] **Automated Tests**: 63 local unit/integration tests and 25 live production scenarios verified passing.
- [x] **Documentation Integrity**: All claims and demos align with actual implemented code.
