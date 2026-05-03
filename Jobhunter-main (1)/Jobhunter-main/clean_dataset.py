import pandas as pd

# Load ORIGINAL raw dataset — not the already cleaned one
df = pd.read_csv("data/raw_jobs.csv")
print(f"Original dataset: {len(df)} rows, {len(df.columns)} columns")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 1: Keep only the columns we need
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
columns_to_keep = [
    "job_id",
    "company_name",
    "title",
    "description",
    "location",
    "remote_allowed",
    "formatted_experience_level",
    "formatted_work_type",
    "skills_desc",
    "normalized_salary",
    "application_url"
]
df = df[columns_to_keep].copy()
print(f"\nAfter column selection: {len(df)} rows, {len(df.columns)} columns")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 2: Drop rows where title or company is missing
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
df = df.dropna(subset=["title", "company_name"])
print(f"After dropping missing title/company: {len(df)} rows")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 3: Keep only tech related jobs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
tech_keywords = [
    "engineer", "developer", "software", "backend",
    "frontend", "fullstack", "full stack", "data",
    "python", "java", "react", "node", "devops",
    "cloud", "ml", "machine learning", "ai", "analyst"
]
mask = df["title"].str.lower().str.contains(
    "|".join(tech_keywords),
    na=False
)
df = df[mask]
print(f"After tech filter: {len(df)} rows")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 4: Keep only valid experience levels
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
valid_levels = [
    "Entry level",
    "Mid-Senior level",
    "Associate",
    "Internship",
    "Director"
]
df = df[df["formatted_experience_level"].isin(valid_levels)]
print(f"After experience level filter: {len(df)} rows")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 5: Keep only useful work types
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
df = df[df["formatted_work_type"].isin(
    ["Full-time", "Internship", "Contract"]
)]
print(f"After work type filter: {len(df)} rows")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 6: Check how many have skills_desc
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
has_skills = df["skills_desc"].notna() & (df["skills_desc"].str.strip() != "")
has_url = df["application_url"].notna() & (df["application_url"].str.strip() != "")
has_both = has_skills & has_url

print(f"\nData quality check:")
print(f"  Rows with skills_desc:               {has_skills.sum()}")
print(f"  Rows with application_url:            {has_url.sum()}")
print(f"  Rows with BOTH skills + url:          {has_both.sum()}")
print(f"  Rows with at least application_url:   {has_url.sum()}")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 7: Smart row selection
# Priority 1 → both skills_desc AND application_url
# Priority 2 → at least application_url
# Priority 3 → any remaining rows
# Target: 500 rows total
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TARGET = 500

df_both = df[has_both].copy()
df_url_only = df[has_url & ~has_skills].copy()
df_rest = df[~has_url].copy()

print(f"\nRow buckets:")
print(f"  Bucket 1 (skills + url): {len(df_both)}")
print(f"  Bucket 2 (url only):     {len(df_url_only)}")
print(f"  Bucket 3 (rest):         {len(df_rest)}")

# Fill up to 500 rows using priority order
frames = []
remaining = TARGET

if len(df_both) > 0:
    take = min(len(df_both), remaining)
    frames.append(df_both.head(take))
    remaining -= take
    print(f"\nTook {take} rows from Bucket 1 (both skills + url)")

if remaining > 0 and len(df_url_only) > 0:
    take = min(len(df_url_only), remaining)
    frames.append(df_url_only.head(take))
    remaining -= take
    print(f"Took {take} rows from Bucket 2 (url only)")

if remaining > 0 and len(df_rest) > 0:
    take = min(len(df_rest), remaining)
    frames.append(df_rest.head(take))
    remaining -= take
    print(f"Took {take} rows from Bucket 3 (rest)")

df_final = pd.concat(frames, ignore_index=True)
df_final = df_final.reset_index(drop=True)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 8: Fix remote_allowed inconsistency
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def clean_remote(val):
    if str(val) in ['1', '1.0', 'True', 'true', 'yes']:
        return True
    return False

df_final["remote_allowed"] = df_final["remote_allowed"].apply(clean_remote)
print(f"\n✅ Fixed remote_allowed:")
print(f"   Remote=True:  {df_final['remote_allowed'].sum()} jobs")
print(f"   Remote=False: {(~df_final['remote_allowed']).sum()} jobs")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 9: Fill remaining missing values
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
df_final["location"] = df_final["location"].fillna("Remote")
df_final["description"] = df_final["description"].fillna("")
df_final["skills_desc"] = df_final["skills_desc"].fillna("")
df_final["normalized_salary"] = df_final["normalized_salary"].fillna(0)
df_final["application_url"] = df_final["application_url"].fillna("")
df_final["formatted_work_type"] = df_final["formatted_work_type"].fillna("Full-time")

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# STEP 10: Trim description to 500 chars
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
df_final["description"] = df_final["description"].str[:500]

# Keep only rows where skills_desc is not empty
df_final = df_final[df_final["skills_desc"].str.strip() != ""]
df_final = df_final.reset_index(drop=True)
print(f"After dropping empty skills_desc: {len(df_final)} rows")

# FINAL: Save and report
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
df_final.to_csv("data/jobs.csv", index=False)

print(f"\n{'='*50}")
print(f"FINAL jobs.csv SUMMARY")
print(f"{'='*50}")
print(f"Total rows:    {len(df_final)}")
print(f"Total columns: {len(df_final.columns)}")
print(f"\nColumns: {list(df_final.columns)}")
print(f"\nExperience levels:")
print(df_final["formatted_experience_level"].value_counts())
print(f"\nWork types:")
print(df_final["formatted_work_type"].value_counts())
print(f"\nSkills_desc filled: {(df_final['skills_desc'] != '').sum()} / {len(df_final)}")
print(f"Application_url filled: {(df_final['application_url'] != '').sum()} / {len(df_final)}")
print(f"\nSample rows:")
print(df_final[['job_id','company_name','title',
                'formatted_experience_level',
                'remote_allowed']].head(5).to_string())
print(f"\n✅ data/jobs.csv overwritten successfully!")