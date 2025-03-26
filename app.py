import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

st.set_page_config(page_title="Disney+ Dashboard", layout="wide")
st.title("📺 Disney+ Content Analysis Dashboard")

# Load Data
@st.cache_data
def load_data():
    return pd.read_csv("cleaned_disney_plus_titles.csv")

try:
    df = load_data()
    st.success("Data Loaded Successfully!")
    if st.checkbox("Show Raw Data"):
        st.dataframe(df)
except FileNotFoundError:
    st.error("❌ Data file not found. Make sure 'cleaned_disney_plus_titles.csv' is in the same folder.")

# Sidebar Filters
st.sidebar.header("🗓️ Filter Content")
years = sorted(df['release_year'].dropna().unique())
types = df['type'].dropna().unique()
genres = sorted(set(g for sublist in df['listed_in'].dropna().str.split(', ') for g in sublist))

selected_years = st.sidebar.multiselect("Select Year(s):", years, default=years)
selected_types = st.sidebar.multiselect("Select Type(s):", types, default=types)
selected_genres = st.sidebar.multiselect("Select Genre(s):", genres, default=genres)

# Filter the DataFrame based on sidebar
df_filtered = df[
    (df['release_year'].isin(selected_years)) &
    (df['type'].isin(selected_types)) &
    (df['listed_in'].apply(lambda x: any(genre in x for genre in selected_genres)))
]

# Tabs Layout
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Content Trends", "Genres", "Ratings by Type"])

with tab1:
    st.subheader("🎬 Disney+ Content Overview")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Titles", len(df_filtered))
    with col2:
        st.metric("Movies", len(df_filtered[df_filtered["type"] == "Movie"]))
        st.metric("TV Shows", len(df_filtered[df_filtered["type"] == "TV Show"]))

with tab2:
    st.subheader("📅 Content Added Over Time")
    df_filtered['year'] = pd.to_datetime(df_filtered['date_added']).dt.year
    type_year = df_filtered.groupby(['year', 'type']).size().unstack().fillna(0)
    st.line_chart(type_year)

with tab3:
    st.subheader("🎭 Top 10 Genres on Disney+")
    top_genres = df_filtered['listed_in'].str.split(', ', expand=True).stack().value_counts().head(10)
    st.bar_chart(top_genres)

with tab4:
    st.subheader("📊 Content Ratings by Type")
    pivot_table = df_filtered.pivot_table(
        index='rating',
        columns='type',
        values='title',
        aggfunc='count',
        fill_value=0
    ).sort_index(ascending=False)

    fig, ax = plt.subplots(figsize=(8, 4))
    sns.heatmap(pivot_table, annot=True, fmt='d', cmap='YlGnBu', ax=ax)
    ax.set_title("Content Ratings by Type", fontsize=14)
    st.pyplot(fig)

    with st.expander("💡 Insights"):
        st.markdown("""
        - Most content is rated **G, PG, and TV-G**, reflecting Disney's family-friendly strategy.
        - **TV-14** and **PG-13** titles are rare, showing limited mature content.
        """)

# View Selector
st.markdown("#### 🧠 Insights")
st.write("""
In 2019, Disney+ launched with a huge drop of movie content, reflected in the sharp spike.
TV Shows have grown gradually, showing Disney’s shift into serialized content.
Family, Animation, and Comedy dominate the genres – aligning with Disney’s brand identity.
""")

# Surprise Recommendation with Poster
if st.button("🎬 Surprise Me with a Movie", key="surprise_combined"):
    surprise = df_filtered.sample(1).iloc[0]
    st.markdown(f"### 🎉 Your Random Pick: **{surprise['title']}**")
    st.markdown(f"📺 {surprise['type']} ({surprise['release_year']})")
    st.markdown(f"⭐ Rated: {surprise['rating']}")
    st.markdown(f"🎭 Genres: {surprise['listed_in']}")
    st.image("https://upload.wikimedia.org/wikipedia/en/thumb/a/a9/Fantasia_poster.jpg/220px-Fantasia_poster.jpg", width=200)
    st.markdown("[Watch Trailer](https://www.youtube.com/results?search_query=" + surprise['title'].replace(" ", "+") + "+trailer)")

# Tooltip Insights (Plotly)
fig = px.histogram(df_filtered, x="release_year", color="type",
                   title="Content Release Over Time",
                   hover_data=["title", "rating"])
fig.update_layout(plot_bgcolor="#0e1117", paper_bgcolor="#0e1117")
st.plotly_chart(fig, use_container_width=True)

# Download Button
csv = df_filtered.to_csv(index=False)
st.download_button("📂 Download Filtered Data", csv, "filtered_disneyplus.csv", "text/csv")

# Animated Timeline
timeline = df_filtered.groupby(['release_year', 'type']).size().reset_index(name='count')
fig = px.bar(
    timeline,
    x='type',
    y='count',
    color='type',
    animation_frame='release_year',
    range_y=[0, timeline['count'].max() + 50],
    title="📅 Animated Growth of Disney+ Content Over the Years",
    labels={"count": "Titles", "type": "Content Type"},
)
fig.update_layout(
    font=dict(color="white"),
    plot_bgcolor="#0e1117",
    paper_bgcolor="#0e1117",
    title_font_size=20
)
st.plotly_chart(fig, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("Created with intent by [Camron Njock](https://www.linkedin.com/in/camron-njock-003812262/) | [GitHub](https://github.com/cam-spec)")

# Mood-Based Recommendations
st.sidebar.header("🎭 Mood-Based Recommender")

mood = st.sidebar.selectbox("How are you feeling today?", [
    "Pick a mood", "Happy", "Adventurous", "Chill", "Nostalgic", "Thrilled", "Curious"
])

mood_to_genres = {
    "Happy": ["Comedy", "Animation", "Family"],
    "Adventurous": ["Action-Adventure", "Fantasy", "Sci-Fi"],
    "Chill": ["Documentary", "Animals & Nature", "Musical"],
    "Nostalgic": ["Classic", "Musical", "Animation"],
    "Thrilled": ["Drama", "Superhero", "Action-Adventure"],
    "Curious": ["Documentary", "Biographical", "Science & Nature"]
}

if mood != "Pick a mood":
    st.markdown(f"### ✨ Because you're feeling **{mood}**…")
    genres = mood_to_genres.get(mood, [])
    mood_recs = df[df['listed_in'].apply(lambda x: any(g in x for g in genres))].sample(3)

    for _, row in mood_recs.iterrows():
        st.markdown(f"🎬 **{row['title']}** — *{row['type']}*, Rated {row['rating']}")
        st.markdown(f"📚 *Genres:* {row['listed_in']}")
